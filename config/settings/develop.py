from decouple import config

from .base import *  # noqa: F403

DEBUG = True

SECRET_KEY = config('SECRET_KEY', default='dev-only-insecure-key-do-not-use-in-prod')

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', 'testserver']

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# django-csp 4.x: CSP_REPORT_ONLY застарів — лише CONTENT_SECURITY_POLICY_REPORT_ONLY.
CONTENT_SECURITY_POLICY_REPORT_ONLY = CONTENT_SECURITY_POLICY  # noqa: F405
CONTENT_SECURITY_POLICY = None
