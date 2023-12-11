from django.conf import settings
from django.template.loader import render_to_string

from xabber_server_panel.dashboard.models import VirtualHost

import subprocess
import time
import os
import re


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


def start_ejabberd():
    if is_ejabberd_started() or not server_installed():
        return

    response = execute_ejabberd_cmd('start')

    while not is_ejabberd_started():
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


def update_ejabberd_config():
    update_vhosts_config()
    # from modules_installation.utils.config_generator import make_xmpp_config
    # make_xmpp_config()
    reload_ejabberd_config()


def update_vhosts_config():
    template = 'ejabberd/vhosts_template.yml'
    vhosts = VirtualHost.objects.all()
    if not vhosts.exists():
        return
    file = open(
        os.path.join(
            settings.EJABBERD_CONFIG_PATH,
            settings.EJABBERD_VHOSTS_CONFIG_FILE
        ), 'w+')
    file.write(render_to_string(template, {'vhosts': vhosts}))
    file.close()


def host_is_valid(host_name):
    # Define a regular expression for the host format: 'example.com'
    pattern = re.compile(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return bool(pattern.match(host_name))