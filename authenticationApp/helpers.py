def generate_otp_email_template(app_name: str, otp: str, expiry_minutes: int = 30):
    subject = f"{app_name} - OTP Verification"

    plain_message = f"""
Hi,

Your One-Time Password (OTP) to complete your registration on {app_name} is:

OTP Code: {otp}

This OTP is valid for {expiry_minutes} minutes.
Please do not share it with anyone.

If you did not request this, ignore this email.

Regards,
{app_name} Team
"""

    html_message = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background: #f7f7f7; padding: 20px;">
  <div style="max-width: 500px; margin: auto; background: #ffffff; padding: 25px; border-radius: 8px; 
              box-shadow: 0 2px 6px rgba(0,0,0,0.1);">

    <h2 style="text-align:center; color:#333;">Email Verification</h2>
    <p>Hello,</p>

    <p>Your One-Time Password (OTP) to complete your registration with <b>{app_name}</b> is:</p>

    <div style="text-align:center; margin: 30px 0;">
      <span style="font-size: 32px; font-weight: bold; letter-spacing: 6px; 
                   background: #f0f0f0; padding: 12px 24px; border-radius: 6px;
                   display: inline-block;">
        {otp}
      </span>
    </div>

    <p>This code is valid for <b>{expiry_minutes} minutes</b>. Please do not share it with anyone.</p>

    <p>If you didn't request this OTP, you can safely ignore this email.</p>

    <p style="margin-top: 30px;">Regards,<br><b>{app_name} Team</b></p>

  </div>
</body>
</html>
"""

    return subject, plain_message, html_message


def generate_password_reset_email(app_name: str, otp: str, expiry_minutes: int = 10):
    subject = f"{app_name} - Password Reset OTP"

    # Plain text fallback
    plain_message = f"""
Hi,

We received a request to reset your password for your {app_name} account.

Your Password Reset OTP is:

OTP Code: {otp}

This OTP is valid for {expiry_minutes} minutes.
If you did not request a password reset, please ignore this email.

Stay secure,
{app_name} Team
"""

    # HTML template
    html_message = f"""
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; background: #f7f7f7; padding: 20px;">
  <div style="max-width: 500px; margin: auto; background: #ffffff; padding: 25px; border-radius: 8px; 
              box-shadow: 0 2px 6px rgba(0,0,0,0.1);">

    <h2 style="text-align:center; color:#333;">Password Reset Request</h2>
    <p>Hello,</p>

    <p>We received a request to reset your password for your <b>{app_name}</b> account.</p>
    <p>Please use the OTP below to proceed:</p>

    <div style="text-align:center; margin: 30px 0;">
      <span style="font-size: 32px; font-weight: bold; letter-spacing: 6px; 
                   background: #f0f0f0; padding: 12px 24px; border-radius: 6px;
                   display: inline-block;">
        {otp}
      </span>
    </div>

    <p>This OTP is valid for <b>{expiry_minutes} minutes</b>.</p>
    
    <p>If you did not request a password reset, you can safely ignore this email.</p>

    <p style="margin-top: 30px;">Stay secure,<br><b>{app_name} Team</b></p>

  </div>
</body>
</html>
"""

    return subject, plain_message, html_message
