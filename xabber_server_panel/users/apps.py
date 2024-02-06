from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'xabber_server_panel.users'

    def ready(self):
        import xabber_server_panel.users.signals
