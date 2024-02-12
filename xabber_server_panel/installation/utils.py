import os
import subprocess
import psycopg2
from psycopg2 import sql
import json

from django.template.loader import get_template
from django.contrib.auth.hashers import make_password
from django.conf import settings

from xabber_server_panel.base_modules.config.utils import get_modules_config, update_vhosts_config
from xabber_server_panel.base_modules.circles.models import Circle
from xabber_server_panel.base_modules.config.models import VirtualHost
from xabber_server_panel.base_modules.users.models import User
from xabber_server_panel.utils import get_system_group_suffix, start_ejabberd, stop_ejabberd, is_ejabberd_started

from .signals import success_installation


def database_exists(data):
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(
            dbname=data['db_name'],
            user=data['db_user'],
            password=data['db_user_pass'],
            host=data['db_host']
        )
    except psycopg2.Error:
        print("Can't connect to database. Maybe you enter wrong data.")
        return False

    try:
        conn.autocommit = True
        cursor = conn.cursor()

        # Check if the database exists
        cursor.execute(sql.SQL("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s"), [data['db_name']])
        exists = cursor.fetchone()
        if exists:
            return True
        else:
            return False
    except psycopg2.OperationalError as e:
        print("Error connecting to PostgreSQL:", e)
        return False
    finally:
        if conn:
            conn.close()


def is_database_empty(data):
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(
            dbname=data['db_name'],
            user=data['db_user'],
            password=data['db_user_pass'],
            host=data['db_host']
        )
    except psycopg2.Error:
        print("Can't connect to database. Maybe you enter wrong data.")
        return False

    try:
        conn.autocommit = True
        cursor = conn.cursor()

        # Check if the database is empty
        cursor.execute("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'public')")
        exists = cursor.fetchone()[0]
        return not exists
    except psycopg2.OperationalError as e:
        print("Error connecting to PostgreSQL:", e)
        return False
    finally:
        if conn:
            conn.close()


def migrate_db(data):
    try:
        # Connect to the PostgreSQL database
        conn = psycopg2.connect(
            dbname=data['db_name'],
            user=data['db_user'],
            password=data['db_user_pass'],
            host=data['db_host']
        )

    except psycopg2.Error:
        print("Can't connect to database. Maybe you enter wrong data.")
        return False

    try:
        # Open a cursor to perform database operations
        cursor = conn.cursor()

        # Read the SQL dump file
        with open(settings.EJABBERD_DUMP, 'r') as f:
            sql_commands = f.read()

        # Execute each command from the dump file
        cursor.execute(sql_commands)

        # Commit the transaction
        conn.commit()

        # Close the cursor and connection
        cursor.close()
        conn.close()

        return True
    except psycopg2.Error as e:
        print("Error:", e)
        return False


def create_vhost(data):
    try:
        VirtualHost.objects.create(
            name=data['host']
        )
        return True
    except:
        return False


def create_config(data):
    data['PROJECT_DIR'] = settings.PROJECT_DIR
    data['VHOST_FILE'] = os.path.join(settings.EJABBERD_CONFIG_PATH, settings.EJABBERD_VHOSTS_CONFIG_FILE)
    data['MODULES_FILE'] = os.path.join(settings.EJABBERD_CONFIG_PATH, settings.EJABBERD_MODULES_CONFIG_FILE)
    data['ADD_CONFIG'] = os.path.join(settings.EJABBERD_CONFIG_PATH, settings.EJABBERD_ADD_CONFIG_FILE)

    # Create add config
    add_config = os.path.join(settings.EJABBERD_CONFIG_PATH, settings.EJABBERD_ADD_CONFIG_FILE)
    if not os.path.isfile(add_config):
        with open(add_config, 'w') as f:
            # Write an empty string to the file
            f.write("")

    config_template = get_template('config/base_config.yml')
    config_file = open(os.path.join(settings.EJABBERD_CONFIG_PATH, 'ejabberd.yml'), "w+")
    config_file.write(config_template.render(context=data))
    config_file.close()
    update_vhosts_config([data['host']])
    get_modules_config()


def create_admin(data):

    # delete spaces
    password = data.get('password', '').strip()

    # create user in db
    user = User(
        username=data['username'],
        host=data['host'],
        is_admin=True
    )
    user.password = make_password(password)
    user.save()

    # create user on server
    cmd_create_admin = [
        settings.EJABBERDCTL,
        'register',
        data['username'],
        data['host'],
        password
    ]
    cmd = subprocess.Popen(cmd_create_admin,
                           stdin=subprocess.PIPE,
                           # stdout=open('/dev/null', 'w'),
                           stderr=subprocess.STDOUT)
    cmd.communicate()
    return cmd.returncode == 0


def set_created_user_as_admin(data):
    cmd_create_admin = [settings.EJABBERDCTL, 'panel_set_admin',
                          data['username'],
                          data['host']]
    cmd = subprocess.Popen(cmd_create_admin,
                           stdin=subprocess.PIPE,
                           # stdout=open('/dev/null', 'w'),
                           stderr=subprocess.STDOUT)
    cmd.communicate()
    return cmd.returncode == 0


def create_group(data):
    cmd_create_group = [settings.EJABBERDCTL, 'srg_create',
                        data['host'],
                        data['host'],
                        settings.EJABBERD_DEFAULT_GROUP_NAME,
                        settings.EJABBERD_DEFAULT_GROUP_DESCRIPTION,
                        ""]
    cmd = subprocess.Popen(cmd_create_group,
                           stdin=subprocess.PIPE,
                           stdout=open('/dev/null', 'w'),
                           stderr=subprocess.STDOUT)
    cmd.communicate()
    return cmd.returncode == 0


def assign_group_to_all(data):
    cmd_assign_to_all = [settings.EJABBERDCTL, 'srg_user_add',
                         '@all@',
                         data['host'],
                         data['host'],
                         data['host']]
    cmd = subprocess.Popen(cmd_assign_to_all,
                           stdin=subprocess.PIPE,
                           stdout=open('/dev/null', 'w'),
                           stderr=subprocess.STDOUT)
    cmd.communicate()
    return cmd.returncode == 0


def start_installation_process(data):

    if not database_exists(data):
        msg = "Database does not exists."
        print(msg)
        return False, msg

    if not is_database_empty(data):
        msg = "Database is not empty."
        print(msg)
        return False, msg

    if not migrate_db(data):
        msg = "Can't migrate database."
        print(msg)
        return False, msg
    print("Successfully migrated database.")

    if not create_vhost(data):
        msg = "Cant create virtual host."
        print(msg)
        return False, msg
    print('Successfully host created')

    create_config(data)
    print("Successfully create config for ejabberd.")

    if not start_ejabberd(first_start=True):
        msg = "Can't start ejabberd."
        print(msg)
        return False, msg
    print("Successfully started ejabberd.")

    if not create_admin(data):
        msg = "Can't create admin in Xabber server database."
        print(msg)
        return False, msg

    if not set_created_user_as_admin(data):
        msg = "Can't set created user as admin in Xabber server database."
        print(msg)
        return False, msg

    if not create_group(data):
        msg = "Can`t create default roster group"
        print(msg)
        return False, msg

    if not assign_group_to_all(data):
        msg = "Can`t create default roster group"
        print(msg)
        return False, msg

    print("Successfully created admin in ejabberd.")

    return True, None


def install_cmd(request, data):
    success, error_message = start_installation_process(data)
    if not success:
        if is_ejabberd_started():
            stop_ejabberd()
        return success, error_message


    # block installation mode
    open(settings.INSTALLATION_LOCK, 'a').close()
    os.chmod(settings.INSTALLATION_LOCK, 0o444)

    success_installation.send(sender=None,
                              request=request,
                              **data)
    return success, error_message


def create_circles(data):

    circle = Circle.objects.create(
        circle=data['host'],
        host=data['host'],
        name=settings.EJABBERD_DEFAULT_GROUP_NAME,
        description=settings.EJABBERD_DEFAULT_GROUP_DESCRIPTION,
        prefix=get_system_group_suffix(),
        all_users=True
    )
    circle.save()


def check_predefined_config():
    return os.path.isfile(os.path.join(settings.BASE_DIR, settings.PREDEFINED_CONFIG_FILE_PATH))


def load_predefined_config():
    with open(os.path.join(settings.BASE_DIR, settings.PREDEFINED_CONFIG_FILE_PATH)) as file:
        try:
            data = json.load(file)
        except:
            data = {}
        return data