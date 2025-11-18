from django.http import JsonResponse
from .models import SubscriptionDetails


class SubscriptionMiddleware:
    """
    Middleware to check subscription status and restrict access
    """
    
    # URLs that don't require active subscription
    ALLOWED_URLS = [
        '/api/subscriptions/plans/',
        '/api/subscriptions/status/',
        '/api/payments/',
        '/admin/',
        '/accounts/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip for anonymous users
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Skip for superusers/staff
        if request.user.is_superuser or request.user.is_staff:
            return self.get_response(request)
        
        # Check if URL is in allowed list
        for allowed_url in self.ALLOWED_URLS:
            if request.path.startswith(allowed_url):
                return self.get_response(request)
        
        # Check subscription status
        try:
            subscription = SubscriptionDetails.objects.get(user=request.user)
            subscription.check_and_update_status()
            
            if not subscription.is_active:
                # Return JSON response for API calls
                if request.path.startswith('/api/'):
                    return JsonResponse({
                        'error': 'Active subscription required',
                        'subscription_expired': True
                    }, status=403)
                    
        except SubscriptionDetails.DoesNotExist:
            # User has no subscription
            if request.path.startswith('/api/'):
                return JsonResponse({
                    'error': 'Subscription required',
                    'has_subscription': False
                }, status=403)
        
        return self.get_response(request)
