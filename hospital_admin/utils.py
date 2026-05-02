from django.db.models import Q
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import BadHeaderError, send_mail
from django.template.loader import render_to_string
from pharmacy.models import Medicine
import secrets
import string


def searchMedicines(request):
    
    search_query = ''
    
    if request.GET.get('search_query'):
        search_query = request.GET.get('search_query')
            
    medicine = Medicine.objects.filter(Q(name__icontains=search_query))
    
    return medicine, search_query


def generate_secure_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_unique_user_id(prefix):
    user_model = get_user_model()
    normalized_prefix = ''.join(ch for ch in prefix.upper() if ch.isalnum())[:4] or 'USER'
    while True:
        candidate = f'{normalized_prefix}{secrets.randbelow(900000) + 100000}'
        if not user_model.objects.filter(username=candidate).exists():
            return candidate


def send_account_credentials_email(*, role_label, recipient_name, recipient_email, user_id, password, extra_context=None):
    values = {
        'role_label': role_label,
        'recipient_name': recipient_name,
        'recipient_email': recipient_email,
        'user_id': user_id,
        'password': password,
    }
    if extra_context:
        values.update(extra_context)

    subject = f'{role_label} Account Created'
    html_message = render_to_string('hospital_admin/account-credentials-mail.html', {'values': values})
    plain_message = (
        f"Hello {recipient_name},\n\n"
        f"Your {role_label.lower()} account has been created in HealthStack.\n\n"
        "Login credentials:\n"
        f"User ID: {user_id}\n"
        f"Password: {password}\n\n"
        "For security, please sign in and change your password after first login.\n\n"
        "Regards,\nHealthStack Admin\n"
    )

    try:
        send_mail(
            subject,
            plain_message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            [recipient_email],
            html_message=html_message,
            fail_silently=False,
        )
        return True, None
    except BadHeaderError:
        return False, 'bad-header'
    except Exception:
        return False, 'send-failed'