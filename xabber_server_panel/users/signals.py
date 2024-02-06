from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.core import management


# @receiver(post_migrate)
def update_custom_permissions(sender, **kwargs):
    management.call_command('update_permissions')
