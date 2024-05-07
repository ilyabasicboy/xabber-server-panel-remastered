from django.db.models.signals import pre_delete
from django.dispatch import receiver

from xabber_server_panel.base_modules.config.models import VirtualHost, ModuleSettings


@receiver(pre_delete, sender=VirtualHost)
def delete_module_settings(sender, *args, **kwargs):
    instance = kwargs.get('instance')
    ModuleSettings.objects.filter(host=instance.name).delete()