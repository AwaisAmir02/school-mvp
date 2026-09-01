from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY')

SINGLE_SCHOOL_MODE = config('SINGLE_SCHOOL_MODE', default=False, cast=bool)

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_htmx',
    'django_celery_beat',

    'common',
    'schools',
    'accounts',
    'permissions',
    'academics',
    'students',
    'staff',
    'audit',
]

JAZZMIN_SETTINGS = {
    'site_title': 'School MVP',
    'site_header': 'School MVP',
    'site_brand': 'School MVP',
    'site_logo': 'icons/icon-192.png',
    'login_logo': 'icons/icon-192.png',
    'site_icon': 'icons/icon-192.png',
    'welcome_sign': 'Welcome to the School MVP administration console',
    'copyright': 'School MVP',
    'search_model': ['schools.School', 'accounts.User'],
    'show_sidebar': True,
    'navigation_expanded': True,
    'order_with_respect_to': [
        'schools', 'accounts', 'academics', 'staff', 'students', 'audit', 'auth', 'django_celery_beat',
    ],
    'custom_links': {
        'Materialize UI': [
            {
                'name': 'School Management (Materialize UI)',
                'url': 'schools:school_list',
                'icon': 'fas fa-th-large',
            },
        ],
    },
    'icons': {
        'auth': 'fas fa-users-cog',
        'auth.group': 'fas fa-users',
        'schools': 'fas fa-building',
        'schools.school': 'fas fa-school',
        'accounts': 'fas fa-users-cog',
        'accounts.user': 'fas fa-user',
        'academics': 'fas fa-book-open',
        'academics.academicyear': 'fas fa-calendar-alt',
        'academics.classlevel': 'fas fa-layer-group',
        'academics.section': 'fas fa-columns',
        'academics.stream': 'fas fa-stream',
        'staff': 'fas fa-chalkboard-teacher',
        'staff.staff': 'fas fa-id-badge',
        'students': 'fas fa-graduation-cap',
        'students.student': 'fas fa-user-graduate',
        'audit': 'fas fa-clipboard-list',
        'audit.auditlog': 'fas fa-history',
    },
    'default_icon_parents': 'fas fa-chevron-circle-right',
    'default_icon_children': 'fas fa-circle',
}

JAZZMIN_UI_TWEAKS = {
    'theme': 'flatly',
    'default_theme_mode': 'light',
    'navbar': 'navbar-white navbar-light',
    'sidebar': 'sidebar-dark-primary',
    'accent': 'accent-primary',
    'button_classes': {
        'primary': 'btn-primary',
        'secondary': 'btn-secondary',
        'info': 'btn-info',
        'warning': 'btn-warning',
        'danger': 'btn-danger',
        'success': 'btn-success',
    },
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'permissions.context_processors.user_permissions',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = config('TIME_ZONE', default='UTC')
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_SERIALIZER = 'json'

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'schools:dashboard'
LOGOUT_REDIRECT_URL = 'accounts:login'
