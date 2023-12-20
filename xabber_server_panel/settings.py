from .generic_settings import *

DEBUG = True
EXT_TOOLS = '/home/viktor.vasilev/apps/ejabberd/utils'
EJD_DIR = "/home/viktor.vasilev/apps/ejabberd"
PSQL_SCRIPT = os.path.join(EXT_TOOLS, 'psql/psql')
EJABBERD_DUMP = os.path.join(EXT_TOOLS, 'psql/pg.sql')
EJABBERD_CONFIG_PATH = os.path.join(EJD_DIR, 'etc/ejabberd/')
EJABBERDCTL = os.path.join(EJD_DIR, 'bin/ejabberdctl')
EJABBERD_SHOULD_RELOAD = False
EJABBERD_STATE = os.path.join('/home/viktor.vasilev/apps/ejabberd/', 'server_state')
INSTALLATION_LOCK = os.path.join('/home/viktor.vasilev/apps/ejabberd/', '.installation_lock')
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join('/home/viktor.vasilev/apps/ejabberd/', 'panel.sqlite3'),
#     }
# }
SILENCED_SYSTEM_CHECKS = ['auth.W004']