from .generic_settings import *


DEBUG = True
EXT_TOOLS = '/home/ilya.basyrov/apps/xabberserver_tools/utils'
EJD_DIR = "/home/ilya.basyrov/apps/xabberserver"
PSQL_SCRIPT = os.path.join(EXT_TOOLS, 'psql/psql')
EJABBERD_DUMP = os.path.join(EXT_TOOLS, 'psql/pg.sql')
EJABBERD_CONFIG_PATH = os.path.join(EJD_DIR, 'etc/ejabberd/')
EJABBERDCTL = os.path.join(EJD_DIR, 'bin/ejabberdctl')
EJABBERD_SHOULD_RELOAD = False
EJABBERD_STATE = os.path.join('/home/ilya.basyrov/apps/xabberserver/', 'server_state')
INSTALLATION_LOCK = os.path.join('/home/ilya.basyrov/apps/xabberserver/', '.installation_lock')

# DATABASES = {#     'default': {#         'ENGINE': 'django.db.backends.sqlite3',#         'NAME': os.path.join('/home/ilya.basyrov/apps/xabberserver/', 'panel.sqlite3'),#     }# }

SILENCED_SYSTEM_CHECKS = ['auth.W004']
WEBHOOKS_SECRET = 'xmppwebhook'
DEFAULT_ACCOUNT_LIFETIME = 5
CRON_JOB_TOKEN = 'cronsecret'
UUID_NS = '4a349548-5456-11ed-8204-6f7c536e951c'
ALLOWED_HOSTS = ['*']