from xabber_server_panel.base_modules.config.models import BaseXmppModule, ModuleSettings


def get_xmpp_server_config():
    settings = ModuleSettings.objects.all()
    configs = []
    for s in settings:
        # add config
        try:
            config = BaseXmppModule(
                vhost=s.host,
                name=s.module,
                module_options=s.get_options()
            )
            configs += [config]
        except Exception as e:
            print(e)
    return configs
