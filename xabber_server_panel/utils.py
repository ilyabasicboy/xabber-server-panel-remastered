from django.conf import settings
from django.apps import apps
from collections import OrderedDict
from django.contrib import messages
from django.forms import ValidationError

import subprocess
import time
import os
import re
import random
import string
from importlib import import_module


# ========== XABBER SERVER =============

def write_ejabberd_state(state):
    server_state_file = open(settings.EJABBERD_STATE, "w+")
    server_state_file.write(str(state))
    server_state_file.close()


def execute_ejabberd_cmd(cmd):
    cmd_ejabberd = [settings.EJABBERDCTL, cmd]
    command = subprocess.call(
        cmd_ejabberd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return command is 0


def is_ejabberd_started():
    return execute_ejabberd_cmd('status')


def server_installed():
    return os.path.isfile(settings.INSTALLATION_LOCK)


def start_ejabberd(first_start=False):
    if is_ejabberd_started():
        return

    if not first_start and not server_installed():
        return

    response = execute_ejabberd_cmd('start')

    while not is_ejabberd_started():
        print('wait 1 sec')
        time.sleep(1)

    write_ejabberd_state(settings.EJABBERD_STATE_ON)
    return response


def restart_ejabberd():
    if not server_installed():
        return

    response = execute_ejabberd_cmd('restart')

    while not is_ejabberd_started():
        time.sleep(1)

    write_ejabberd_state(settings.EJABBERD_STATE_ON)
    return response


def stop_ejabberd(change_state=True):

    response = execute_ejabberd_cmd('stop')

    while is_ejabberd_started():
        time.sleep(1)

    if change_state:
        write_ejabberd_state(settings.EJABBERD_STATE_OFF)

    return response


def reload_ejabberd_config():
    return execute_ejabberd_cmd('reload_config')


def update_app_list(app_list):

    apps.app_configs = OrderedDict()
    apps.apps_ready = apps.models_ready = apps.loading = apps.ready = False
    apps.clear_cache()
    apps.populate(app_list)


def reload_server():
    # try to reload server
    try:
        if os.environ.get("XABBER_PANEL_PF"):
            import signal
            pid = open(os.environ.get("XABBER_PANEL_PF")).read()
            os.kill(int(pid), signal.SIGHUP)
        else:
            os.utime(os.path.join(settings.BASE_DIR, 'xabber_server_panel/wsgi.py'), times=None)
    except:
        pass


# ============ VALIDATORS =============

def validate_jid(jid):
    # Regular expression for validating JID without resource
    pattern = r'^[^@<>{}"\'\\]+@[^@<>{}"\'\\]+\.[^@<>{}"\'\\]+$'
    if re.match(pattern, jid):
        return True
    else:
        return False


def jid_form_validation(value):
    # Define a regular expression for the jid format: 'user@example.com'
    if not validate_jid(value):
        raise ValidationError("Invalid jid format.")


def host_is_valid(host_name):
    # Define a regular expression for the host format: 'example.com'
    pattern = re.compile(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return bool(pattern.match(host_name))


def host_form_validation(value):
    # Define a regular expression for the host format: 'example.com'
    if not host_is_valid(value):
        raise ValidationError("Invalid host format.")


def validate_local_part(value):
    """
    Custom validator to check if the local part of an email address is valid.
    """
    if not re.match(r'^[a-zA-Z0-9._%+-]+$', value):
        raise ValidationError(
            'Invalid characters in the local part.'
        )


# =============== OTHER ==============

def get_error_messages(request):
    error_messages = []

    # Get all messages for the current request
    message_list = messages.get_messages(request)

    # Filter messages with the 'error' tag
    for message in message_list:
        if message.tags == 'error':
            error_messages.append(message.message)

    return error_messages

def get_success_messages(request):
    success_messages = []

    # Get all messages for the current request
    message_list = messages.get_messages(request)

    # Filter messages with the 'error' tag
    for message in message_list:
        if message.tags == 'success':
            success_messages.append(message.message)

    return success_messages


def get_system_group_suffix():
    return ''.join(random.choices(string.ascii_lowercase, k=8))