from pathlib import Path

from decouple import Csv, config
from django.templatetags.static import static

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY', default='insecure-local-only-change-me')

DEBUG = False

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv())

INSTALLED_APPS = [
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django.contrib.humanize',
    'django_htmx',
    'tinymce',
    'core',
    'catalog',
    'leads',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'core.middleware_admin.AdminForceUkrainianMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'csp.middleware.CSPMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'core.context_processors.site_globals',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'uk'
LANGUAGES = [
    ('uk', 'Українська'),
    ('ru', 'Русский'),
]
LOCALE_PATHS = [BASE_DIR / 'locale']
TIME_ZONE = 'Europe/Kyiv'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Секретний префікс адмінки (без слешів з боків). Старий /admin → 404.
ADMIN_URL = config('ADMIN_URL', default='rossa-panel').strip().strip('/')

EMAIL_BACKEND = config(
    'EMAIL_BACKEND',
    default='django.core.mail.backends.console.EmailBackend',
)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='ROSSA <hello@rossa.ua>')
MANAGER_EMAIL = config('MANAGER_EMAIL', default='hello@rossa.ua')

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True

CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ("'self'",),
        # unsafe-eval потрібен для Alpine.js у django-unfold (x-show / x-data).
        # unsafe-inline: inline CSS-змінні в base.html + TinyMCE/Unfold.
        'script-src': ("'self'", "'unsafe-inline'", "'unsafe-eval'"),
        'style-src': ("'self'", "'unsafe-inline'"),
        'font-src': ("'self'", 'data:'),
        'img-src': ("'self'", 'data:', 'blob:'),
        'media-src': ("'self'",),
        'connect-src': ("'self'",),
        'object-src': ("'none'",),
        # Google Maps embed на /contacts/
        'frame-src': ("'self'", 'https://www.google.com', 'https://maps.google.com'),
        'frame-ancestors': ("'none'",),
        'base-uri': ("'self'",),
        'form-action': ("'self'",),
    }
}

TINYMCE_DEFAULT_CONFIG = {
    'height': 360,
    'menubar': False,
    'plugins': 'link lists',
    'toolbar': 'undo redo | bold italic underline | bullist numlist | link | removeformat',
    'branding': False,
    'promotion': False,
    'forced_root_block': 'p',
    'newline_behavior': 'block',
    # Дзеркало core.cms_sanitize.ALLOWED_TAGS — staff XSS defense-in-depth.
    'valid_elements': (
        'p,br,strong/b,em/i,u,ul,ol,li,'
        'a[href|title|target|rel],span[class]'
    ),
    'valid_link_targets': '_blank',
    'content_style': (
        'body { font-family: system-ui, -apple-system, sans-serif; font-size: 16px; '
        'line-height: 1.55; padding: 8px 12px; }'
        'p { margin: 0 0 0.9em; }'
        'p:last-child { margin-bottom: 0; }'
    ),
}


def _unfold_navigation(request=None):
    from core.admin_nav import build_unfold_navigation
    return build_unfold_navigation()


UNFOLD = {
    'SITE_TITLE': 'ROSSA — панель керування',
    'SITE_HEADER': 'ROSSA',
    'SITE_SYMBOL': 'crown',
    'SITE_FAVICONS': [
        {
            'rel': 'icon',
            'sizes': 'any',
            'href': lambda request: static('images/favicon/favicon.ico'),
        },
        {
            'rel': 'icon',
            'type': 'image/png',
            'sizes': '32x32',
            'href': lambda request: static('images/favicon/favicon-32.png'),
        },
        {
            'rel': 'icon',
            'type': 'image/png',
            'sizes': '16x16',
            'href': lambda request: static('images/favicon/favicon-16.png'),
        },
        {
            'rel': 'apple-touch-icon',
            'sizes': '180x180',
            'href': lambda request: static('images/favicon/apple-touch-icon.png'),
        },
    ],
    'COLORS': {
        # Beige page surface — matches --color-surface (#f1efec)
        'base': {
            '50': '#f1efec',
            '100': '#e8e6e3',
            '200': '#dcdad7',
            '300': '#c6c4c1',
            '400': '#9b9997',
            '500': '#7b7977',
            '600': '#656362',
            '700': '#504e4c',
            '800': '#3a3837',
            '900': '#2b2928',
            '950': '#232120',
        },
        # Brown accent — matches --color-accent (#986030)
        'primary': {
            '50': '#faf7f5',
            '100': '#f3ece6',
            '200': '#e5d7cb',
            '300': '#d1b7a2',
            '400': '#b7906e',
            '500': '#b07a45',
            '600': '#986030',
            '700': '#7d4f27',
            '800': '#633e1f',
            '900': '#4c3018',
            '950': '#2e1d0e',
        },
    },
    'SHOW_HISTORY': True,
    'SIDEBAR': {
        'show_search': True,
        'show_all_applications': False,
        'navigation': _unfold_navigation,
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '{levelname} {asctime} {module} {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'root': {'handlers': ['console'], 'level': 'WARNING'},
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'django.request': {'handlers': ['console'], 'level': 'ERROR', 'propagate': False},
    },
}

CATALOG_PAGE_SIZE = 9
