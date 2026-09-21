from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY')

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
    'core',
    'catalog',
    'leads',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
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
        'script-src': ("'self'",),
        'style-src': ("'self'", 'https://fonts.googleapis.com'),
        'font-src': ("'self'", 'https://fonts.gstatic.com'),
        'img-src': ("'self'", 'data:', 'blob:'),
        'media-src': ("'self'",),
        'connect-src': ("'self'",),
        'frame-ancestors': ("'none'",),
        'base-uri': ("'self'",),
        'form-action': ("'self'",),
    }
}

UNFOLD = {
    'SITE_TITLE': 'ROSSA',
    'SITE_HEADER': 'ROSSA',
    'SITE_SYMBOL': 'chair',
    'SHOW_HISTORY': True,
    'SIDEBAR': {
        'show_search': True,
        'navigation': [
            {
                'title': 'Каталог',
                'separator': True,
                'items': [
                    {'title': 'Категорії', 'icon': 'category', 'link': '/admin/catalog/category/'},
                    {'title': 'Тканини', 'icon': 'palette', 'link': '/admin/catalog/fabric/'},
                    {'title': 'Відтінки', 'icon': 'colorize', 'link': '/admin/catalog/shade/'},
                    {'title': 'Товари', 'icon': 'inventory_2', 'link': '/admin/catalog/product/'},
                ],
            },
            {
                'title': 'Заявки',
                'separator': True,
                'items': [
                    {'title': 'Замовлення', 'icon': 'shopping_bag', 'link': '/admin/leads/orderrequest/'},
                    {'title': 'Співпраця', 'icon': 'handshake', 'link': '/admin/leads/partnershiplead/'},
                    {'title': 'Контакти', 'icon': 'mail', 'link': '/admin/leads/contactlead/'},
                ],
            },
            {
                'title': 'Вміст сайту',
                'separator': True,
                'items': [
                    {'title': 'Налаштування', 'icon': 'settings', 'link': '/admin/core/sitesettings/'},
                    {'title': 'Головна', 'icon': 'home', 'link': '/admin/core/homepage/'},
                    {'title': 'Переваги', 'icon': 'star', 'link': '/admin/core/valueprop/'},
                    {'title': 'Про нас', 'icon': 'info', 'link': '/admin/core/aboutpage/'},
                    {'title': 'Співпраця (сторінка)', 'icon': 'groups', 'link': '/admin/core/collabpage/'},
                    {'title': 'Юридичні сторінки', 'icon': 'gavel', 'link': '/admin/core/legalpage/'},
                ],
            },
        ],
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
