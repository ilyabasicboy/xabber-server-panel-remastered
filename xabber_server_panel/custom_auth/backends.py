from xabber_server_panel.base_modules.users.models import User
from django.contrib.sessions.models import Session


class CustomAuthBackend(object):

    """
        Customized to allow authorization for administrators and users with any permissions.
         Also backend writes api token in user.token field if ejabberd server is started.
    """

    def authenticate(self, request, username, password, api=None, **kwargs):
        username, host = username.split('@')
        try:
            user = User.objects.get(
                username=username,
                host=host
            )
        except User.DoesNotExist:
            return None

        # check permissions
        if (user.is_admin or user.has_any_permissions) and user.check_password(password) and user.is_active:

            # set token in session
            if api and api.token and request:
                request.session.flush()

                request.session['api_token'] = api.token
                request.session.modified = True

            return user
        return None

    def get_user(self, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
        return user