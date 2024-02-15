from xabber_server_panel.base_modules.users.utils import update_permissions


# @receiver(post_migrate)
def update_custom_permissions(sender, **kwargs):
    update_permissions()
