from django.core import management


# @receiver(post_migrate)
def update_custom_permissions(sender, **kwargs):
    management.call_command('update_permissions')
