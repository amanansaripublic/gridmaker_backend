# payments/services/apple_iap_service.py
import requests
import jwt
import time
from datetime import datetime, timedelta
from constance import config  # Import constance config
from typing import Dict, Optional


class AppleIAPService:
    """Service for Apple In-App Purchase validation with dynamic configuration"""
    
    PRODUCTION_URL = "https://buy.itunes.apple.com/verifyReceipt"
    SANDBOX_URL = "https://sandbox.itunes.apple.com/verifyReceipt"
    
    PRODUCTION_API_URL = "https://api.storekit.itunes.apple.com"
    SANDBOX_API_URL = "https://api.storekit-sandbox.itunes.apple.com"
    
    @property
    def bundle_id(self):
        """Get bundle ID from constance config"""
        return config.APPLE_BUNDLE_ID
    
    @property
    def shared_secret(self):
        """Get shared secret from constance config"""
        return config.APPLE_SHARED_SECRET or None
    
    @property
    def issuer_id(self):
        """Get issuer ID from constance config"""
        return config.APPLE_ISSUER_ID or None
    
    @property
    def key_id(self):
        """Get key ID from constance config"""
        return config.APPLE_KEY_ID or None
    
    @property
    def private_key(self):
        """Get private key from constance config"""
        return config.APPLE_PRIVATE_KEY or None
    
    def verify_receipt(self, receipt_data: str, exclude_old_transactions: bool = True) -> Dict:
        """
        Verify receipt with Apple (Legacy receipt validation)
        First tries production, falls back to sandbox if needed
        """
        payload = {
            'receipt-data': receipt_data,
            'exclude-old-transactions': exclude_old_transactions
        }
        
        if self.shared_secret:
            payload['password'] = self.shared_secret
        
        # Try production first
        response = requests.post(self.PRODUCTION_URL, json=payload, timeout=10)
        result = response.json()
        
        # If status is 21007, receipt is from sandbox - retry with sandbox URL
        if result.get('status') == 21007:
            response = requests.post(self.SANDBOX_URL, json=payload, timeout=10)
            result = response.json()
            result['environment'] = 'Sandbox'
        else:
            result['environment'] = 'Production'
        
        return result
    
    def parse_receipt_response(self, receipt_response: Dict) -> Dict:
        """Parse Apple receipt validation response"""
        status = receipt_response.get('status')
        
        if status != 0:
            error_messages = {
                21000: "The App Store could not read the JSON object you provided.",
                21002: "The data in the receipt-data property was malformed or missing.",
                21003: "The receipt could not be authenticated.",
                21004: "The shared secret you provided does not match the shared secret on file.",
                21005: "The receipt server is not currently available.",
                21006: "This receipt is valid but subscription has expired.",
                21007: "This receipt is from the test environment.",
                21008: "This receipt is from the production environment.",
                21010: "This receipt could not be authorized.",
            }
            raise ValueError(error_messages.get(status, f"Unknown error: {status}"))
        
        receipt = receipt_response.get('receipt', {})
        latest_receipt_info = receipt_response.get('latest_receipt_info', [])
        
        # Get the most recent transaction
        if latest_receipt_info:
            latest_transaction = max(latest_receipt_info, 
                                   key=lambda x: int(x.get('purchase_date_ms', 0)))
        else:
            in_app = receipt.get('in_app', [])
            if in_app:
                latest_transaction = max(in_app, 
                                       key=lambda x: int(x.get('purchase_date_ms', 0)))
            else:
                raise ValueError("No transaction found in receipt")
        
        return {
            'transaction_id': latest_transaction.get('transaction_id'),
            'original_transaction_id': latest_transaction.get('original_transaction_id'),
            'product_id': latest_transaction.get('product_id'),
            'purchase_date_ms': latest_transaction.get('purchase_date_ms'),
            'expires_date_ms': latest_transaction.get('expires_date_ms'),
            'quantity': int(latest_transaction.get('quantity', 1)),
            'bundle_id': receipt.get('bundle_id'),
            'environment': receipt_response.get('environment'),
            'raw_response': receipt_response
        }
    
    def generate_jwt_token(self) -> str:
        """Generate JWT token for App Store Server API (StoreKit 2)"""
        if not all([self.issuer_id, self.key_id, self.private_key]):
            raise ValueError("Apple API credentials not configured in admin panel")
        
        issued_at = int(time.time())
        expiration_time = issued_at + 3600  # 1 hour
        
        headers = {
            'alg': 'ES256',
            'kid': self.key_id,
            'typ': 'JWT'
        }
        
        payload = {
            'iss': self.issuer_id,
            'iat': issued_at,
            'exp': expiration_time,
            'aud': 'appstoreconnect-v1',
            'bid': self.bundle_id
        }
        
        token = jwt.encode(payload, self.private_key, algorithm='ES256', headers=headers)
        return token
    
    def get_transaction_info(self, transaction_id: str, environment: str = 'production') -> Dict:
        """
        Get transaction info using App Store Server API (StoreKit 2)
        """
        base_url = self.PRODUCTION_API_URL if environment == 'production' else self.SANDBOX_API_URL
        url = f"{base_url}/inApps/v1/transactions/{transaction_id}"
        
        token = self.generate_jwt_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(f"Failed to get transaction info: {response.status_code} - {response.text}")
    
    def verify_bundle_id(self, bundle_id: str) -> bool:
        """Verify bundle ID matches your app"""
        return bundle_id == self.bundle_id
    
    def is_configured(self) -> bool:
        """Check if Apple IAP is properly configured"""
        return bool(self.bundle_id and (self.shared_secret or 
                   (self.issuer_id and self.key_id and self.private_key)))


# Create service instance
apple_iap_service = AppleIAPService()
