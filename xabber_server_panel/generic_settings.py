import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_ROOT = os.path.join(BASE_DIR, 'xabber_server_panel')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(PROJECT_ROOT, "static")]
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440
FILE_UPLOAD_PERMISSIONS = 0o644  # права для записи файлов, размером > FILE_UPLOAD_MAX_MEMORY_SIZE
SECRET_KEY = 'django-insecure--$i1m4fmjutnxyoyuu(c&#!djlv^&47$n@55=snkwexoo%&9k%'

DEBUG = False

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'xabber_server_panel',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'xabber_server_panel.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_ROOT, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'xabber_server_panel.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(os.path.abspath(os.path.join(BASE_DIR, os.pardir)), 'xmppserver.sqlite3'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
MODULES_DIR = os.path.join(BASE_DIR, 'modules')

# ======== Ejabberd settings ============= #

INSTALLATION_LOCK = os.path.join(PROJECT_ROOT, '.installation_lock')
PSQL_SCRIPT = os.path.join(PROJECT_ROOT, 'utils/psql/psql')
EJABBERD_DUMP = os.path.join(PROJECT_ROOT, 'utils/psql/pg.sql')
EJABBERD_CONFIG_PATH = os.path.join(PROJECT_ROOT, 'xmppserver/etc/ejabberd/')
EJABBERD_MODULES_CONFIG_FILE = 'modules_config.yml'
EJABBERDCTL = os.path.join(PROJECT_ROOT, 'xmppserver/bin/ejabberdctl')
EJABBERD_SHOULD_RELOAD = False
EJABBERD_STATE = os.path.join(PROJECT_ROOT, 'server_state')
EJABBERD_STATE_ON = 1
EJABBERD_STATE_OFF = 0
EJABBERD_DEFAULT_GROUP_NAME = "All"
EJABBERD_DEFAULT_GROUP_DESCRIPTION = "Contains all users on this virtual host"

EJABBERD_VHOSTS_CONFIG_FILE = 'virtual_hosts.yml'

EJABBERD_API_URL = 'http://127.0.0.1:5280/panel'
EJABBERD_API_TOKEN_TTL = 60 * 60 * 24 * 365
EJABBERD_API_SCOPES = 'sasl_auth'

PAGINATION_PAGE_SIZE = 30
HTTP_REQUEST_TIMEOUT = 5

# =========== AUTH ============ #
INSTALLED_APPS += ['xabber_server_panel.custom_auth']

LOGIN_REDIRECT_URL = '/auth/login/'
LOGIN_URL='/auth/login/'

AUTHENTICATION_BACKENDS = [
    'xabber_server_panel.custom_auth.backends.CustomAuthBackend',
]

# =========== USERS =============== #
INSTALLED_APPS += ['xabber_server_panel.users']

AUTH_USER_MODEL = 'users.User'

# ============ API ============#
INSTALLED_APPS += ['xabber_server_panel.api']

# ============ DASHBOARD ============#
INSTALLED_APPS += ['xabber_server_panel.dashboard']

# ============ CIRCLES ===============#
INSTALLED_APPS += ['xabber_server_panel.circles']

# ============ GROUPS ===============#
INSTALLED_APPS += ['xabber_server_panel.groups']

# ============ REGISTRATION ===============#
INSTALLED_APPS += ['xabber_server_panel.registration']

# ============ CONFIG ===============#
INSTALLED_APPS += ['xabber_server_panel.config']


# external modules
if os.path.exists(MODULES_DIR):
    for folder in os.listdir(MODULES_DIR):
        folder_path = os.path.join(MODULES_DIR, folder)
        if os.path.isdir(folder_path):
            app_name = "modules." + folder
            INSTALLED_APPS += [app_name]