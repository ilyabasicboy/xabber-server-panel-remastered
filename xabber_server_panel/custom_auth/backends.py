from django.contrib.auth import backends
from django.contrib.auth import get_user_model

from xabber_server_panel.api.api import EjabberdAPI
from xabber_server_panel.api.models import EjabberdAccount
from xabber_server_panel.api.utils import int_to_token

from xabber_server_panel.users.models import User


class CustomAuthBackend(object):
    SESSION_KEY = '_auth_user_id'
    def authenticate(self, request, username, password, api=None, **kwargs):
        username, host = username.split('@')
        try:
            user = User.objects.get(
                username=username,
                host=host
            )
        except User.DoesNotExist:
            return None

        if user.is_admin and user.check_password(password):
            if not api:
                api = EjabberdAPI()
            return EjabberdAccount(api, user=user)
        return None

    def get_user(self, user_id):
        try:
            user = User.objects.get(id=user_id)
            api = EjabberdAPI()
            return EjabberdAccount(api, user=user)
        except:
            try:
                token = int_to_token(user_id)
            except Exception as e:
                return None
            api = EjabberdAPI()
            api.fetch_token(token)
            return EjabberdAccount(api)