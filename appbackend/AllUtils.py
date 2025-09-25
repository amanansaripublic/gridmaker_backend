



from django.conf import settings
from django.core.mail import send_mail

def sendMail(email, message, subject="Subject"):
    try:
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email, ]
        send_mail( subject, message, email_from, recipient_list )
    except Exception as e:
        return False
    
    return True