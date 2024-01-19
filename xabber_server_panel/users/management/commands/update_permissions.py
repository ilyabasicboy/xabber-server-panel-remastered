from django.core.management.base import BaseCommand
from xabber_server_panel.users.models import CustomPermission


class Command(BaseCommand):
    help = ('Update permissions')
    can_import_settings = True

    def handle(self, *args, **options):
        for app in CustomPermission.APPS:
            for permission in CustomPermission.PERMISSIONS:
                permission, created = CustomPermission.objects.get_or_create(
                    permission=permission[0],
                    app=app[0]
                )