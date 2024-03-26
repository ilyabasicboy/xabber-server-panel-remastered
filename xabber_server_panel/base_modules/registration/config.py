from .models import RegistrationSettings
from xabber_server_panel.base_modules.config.models import BaseXmppModule


def get_xmpp_server_config():
    settings = RegistrationSettings.objects.all()
    configs = []
    for s in settings:
        # add registration config
        if s.status != "disabled":
            try:
                register_config = BaseXmppModule(
                    vhost=s.host.name,
                    name="mod_register",
                    module_options={
                        "password_strength": 32,
                        "access": "register"
                    }
                )
                configs += [register_config]
            except Exception as e:
                print(e)
        # add keys config
        if s.status == "link":
            try:
                config = BaseXmppModule(
                    vhost=s.host.name,
                    name="mod_registration_keys",
                    module_options={}
                )
                configs += [config]
            except Exception as e:
                print(e)
    return configs
