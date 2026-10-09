from .develop import *  # noqa: F403

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Не глушити тести rate-limit'ом (прод: 10/хв).
LEAD_RATE_LIMIT_MAX = 10_000
