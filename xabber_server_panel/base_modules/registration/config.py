from .models import RegistrationSettings
from xabber_server_panel.base_modules.config.models import BaseXmppModule


def get_xmpp_server_config():
    settings = RegistrationSettings.objects.all()
    configs = []
    for s in settings:
        try:
            if s.status != "disabled":
                configs.append(
                    BaseXmppModule(
                        vhost=s.host.name,
                        name="mod_register",
                        module_options={
                            "password_strength": 32,
                            "access": "register"
                        }
                    )
                )
            if s.status == "link":
                configs.append(
                    BaseXmppModule(
                        vhost=s.host.name,
                        name="mod_registration_keys",
                        module_options={}
                    )
                )
        except Exception as e:
            return e
    return configs
