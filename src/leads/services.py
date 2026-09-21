from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import get_language


def notify_manager(subject: str, body: str):
    to = [settings.MANAGER_EMAIL]
    if not to[0]:
        return
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, to, fail_silently=True)


def current_lang():
    return (get_language() or 'uk')[:2]
