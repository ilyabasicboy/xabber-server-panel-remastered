from django.core.management.base import BaseCommand
from xabber_server_panel.users.models import CustomPermission, get_apps_choices


class Command(BaseCommand):
    help = ('Update permissions')
    can_import_settings = True

    def handle(self, *args, **options):
        app_list = [app[0] for app in get_apps_choices()]

        for app in app_list:
            for permission in CustomPermission.PERMISSIONS:
                permission, created = CustomPermission.objects.get_or_create(
                    permission=permission[0],
                    app=app
                )

        # delete old permissions
        CustomPermission.objects.exclude(app__in=app_list).delete()