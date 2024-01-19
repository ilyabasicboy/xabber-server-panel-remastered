from django.contrib.auth.mixins import UserPassesTestMixin
from xabber_server_panel.users.models import CustomPermission


class CustomPermissionMixin(UserPassesTestMixin):
    permission_required = (None, None)

    def test_func(self):
        user = self.request.user

        if self.permission_required:
            app_permission = CustomPermission.objects.filter(
                user=user,
                app=self.permission_required[0],
                permission=self.permission_required[1]
            ).exists()
            return app_permission