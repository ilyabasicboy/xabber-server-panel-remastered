from django.template.loader import render_to_string
from django.conf import settings
from django.apps import apps

from xabber_server_panel.base_modules.config.models import VirtualHost
from xabber_server_panel.utils import reload_ejabberd_config
from xabber_server_panel.base_modules.config.models import BaseXmppModule, BaseXmppOption

import copy
import os
from importlib import util, import_module


def get_value(key, value, level):

    """ Helper function to format key-value pairs with proper indentation """

    shift = '  ' * level
    result = ''

    # Handle lists
    if isinstance(value, list):
        result += "{}:\n".format(key)
        for el in value:
            result += shift + "  - {}\n".format(el)

    # Handle dictionaries
    elif isinstance(value, dict):
        if value:
            result += "{}:\n".format(key)
            for subkey, subvalue in value.items():
                result += get_value(subkey, subvalue, level + 1)
        else:
            result += "{}: {}\n".format(key, "{}")

    # Handle other types
    else:
        result += "{}: {}\n".format(key, value)
    return shift + result


def get_modules_config():

    """ Returns list of xmpp module or xrmpp option configs """

    configs = []

    # loop over all apps and check xmpp_server_config
    for app in apps.app_configs.values():

        # Check if the module exists before attempting to import it
        module_spec = util.find_spec(".config", package=app.name)
        if module_spec:
            module_config = import_module('.config', package=app.name)
            if hasattr(module_config, 'get_xmpp_server_config'):
                config_list = module_config.get_xmpp_server_config()
                configs += [config.get_config() for config in config_list if isinstance(config, (BaseXmppModule, BaseXmppOption))]
    return configs


def make_xmpp_config():
    # Get module configurations from settings
    module_configs = get_modules_config()

    # Define the path for the Ejabberd configuration file
    config_path = os.path.join(settings.EJABBERD_CONFIG_PATH, settings.EJABBERD_MODULES_CONFIG_FILE)

    # Get all virtual hosts
    hosts = VirtualHost.objects.all()

    # Initialize dictionaries to store global and per-host configurations
    global_options = {}
    host_config = {host.name: {} for host in hosts}
    append_host_config = copy.deepcopy(host_config)

    # Loop through module configurations
    for module_config in module_configs:
        try:
            # Check if the configuration is a module
            if module_config.get('type') == "module":
                # Check if the module is for global or a specific virtual host
                if module_config.get('vhost') == "global":
                    # Update all host configurations with the module options
                    for config in append_host_config.values():
                        config.update({module_config.get('name'): module_config.get('module_options')})
                else:
                    # Update the specific virtual host configuration with the module options
                    for key, value in append_host_config.items():
                        if key == module_config.get('vhost'):
                            value.update({module_config.get('name'): module_config.get('module_options')})

            # Check if the configuration is an option
            elif module_config.get('type') == "option":
                # Check if the option is for global or a specific virtual host
                if module_config.get('vhost') == "global":
                    # Update global options with the option value
                    global_options.update({module_config.get('name'): module_config.get('value')})
                else:
                    # Update the specific virtual host configuration with the option value
                    host_config.get(module_config.get('vhost')).update(
                        {module_config.get('name'): module_config.get('value')})

        except Exception as e:
            # Print any exceptions that occur, but continue with the next iteration
            print(e)
            pass

    # Write the configurations to the Ejabberd configuration file
    with open(config_path, "w") as f:
        # Write global options to the file
        for key, value in global_options.items():
            f.write(get_value(key, value, level=0))

        # Write host configurations to the file
        config_values = [config for config in host_config.values() if config]
        if config_values:
            f.write("host_config:\n")
            for key, value in host_config.items():
                if value:
                    f.write('  "{}":\n'.format(key))
                    for key1, val1 in value.items():
                        f.write(get_value(key1, val1, level=3))

        # Write append_host_config to the file
        f.write("append_host_config:\n")
        for key, value in append_host_config.items():
            if value:
                f.write('  "{}":\n'.format(key) + "    modules:\n")
                for key1, val1 in value.items():
                    f.write(get_value(key1, val1, level=3))
            else:
                f.write('  "{}":\n'.format(key) + "    modules: []\n")


def update_vhosts_config(hosts=None):
    template = 'config/hosts_template.yml'

    if not hosts:
        hosts = VirtualHost.objects.all()

    if not hosts:
        return

    file = open(
        os.path.join(
            settings.EJABBERD_CONFIG_PATH,
            settings.EJABBERD_VHOSTS_CONFIG_FILE
        ), 'w+')
    xml = render_to_string(template, {'hosts': hosts})
    file.write(xml)
    file.close()


def update_ejabberd_config():
    update_vhosts_config()
    make_xmpp_config()
    reload_ejabberd_config()


def check_hosts(api):

    """
        Check registered users and create
        if it doesn't exist in django db
    """

    try:
        registered_hosts = api.get_vhosts().get('vhosts')
    except:
        registered_hosts = []

    if registered_hosts:

        # Get a list of existing usernames from the User model
        existing_hosts = VirtualHost.objects.values_list('name', flat=True)

        # Filter the user_list to exclude existing usernames
        unknown_hosts = [host for host in registered_hosts if host not in existing_hosts]

        # create in db unknown users
        if unknown_hosts:
            hosts_to_create = [
                VirtualHost(
                    name=host,
                )
                for host in unknown_hosts
            ]
            VirtualHost.objects.bulk_create(hosts_to_create)

        # get unregistered users in db and delete
        hosts_to_delete = VirtualHost.objects.exclude(name__in=registered_hosts)
        if hosts_to_delete:
            hosts_to_delete.delete()