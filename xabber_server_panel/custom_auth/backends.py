from xabber_server_panel.base_modules.users.models import User


class CustomAuthBackend(object):

    def authenticate(self, request, username, password, api=None, **kwargs):
        username, host = username.split('@')
        try:
            user = User.objects.get(
                username=username,
                host=host
            )
        except User.DoesNotExist:
            return None

        if (user.is_admin or user.has_any_permissions) and user.check_password(password):
            if api and api.token:
                user.token = api.token
                user.save()
            return user
        return None

    def get_user(self, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
        return user