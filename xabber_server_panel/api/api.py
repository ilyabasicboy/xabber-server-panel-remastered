import requests

from django.conf import settings
from .exceptions import ResponseException


class EjabberdAPI(object):
    def __init__(self):
        self.authorized = False
        self.token = None
        self.session = requests.Session()
        self.base_url = settings.EJABBERD_API_URL
        self._cleanup_for_request()

    def _cleanup_for_request(self):
        self.raw_response = None
        self.response = None
        self.status_code = None
        self.success = None

    def fetch_token(self, token):
        self.token = token
        self.session.headers.update({'Authorization': 'Bearer {}'.format(token)})

    def _wrapped_call(self, method, url, status_code, data, http_method):
        try:
            if http_method in ("post", "delete", "put"):
                self.raw_response = method(url,
                                           json=data,
                                           timeout=settings.HTTP_REQUEST_TIMEOUT)
            elif http_method == "get":
                self.raw_response = method(url,
                                           params=data,
                                           timeout=settings.HTTP_REQUEST_TIMEOUT)
        except requests.exceptions.ConnectionError:
            self.status_code = 503
            raise ResponseException({'type': 'connection_error'})
        except requests.exceptions.RequestException as e:
            self.status_code = 500
            raise ResponseException({'type': 'request_error', 'detail': e})
        except Exception as e:
            self.status_code = 500
            raise ResponseException({'type': 'client_error', 'detail': e})
        try:
            self.response = self.raw_response.json() if self.raw_response.text else {}
        except Exception:
            raise ResponseException({'type': 'invalid_json'})
        self.status_code = self.raw_response.status_code
        if self.status_code != status_code:
            raise ResponseException({'type': 'bad_status_code',
                                     'detail': self.status_code})

    def _call_method(self, http_method, relative_url, success_code, data,
                     login_method=False, auth_required=True, return_bool=False):
        self._cleanup_for_request()
        method = getattr(self.session, http_method)
        url = self.base_url + relative_url
        print(http_method, url, data)
        try:
            self._wrapped_call(method, url, success_code, data, http_method)
        except ResponseException as e:
            print(e)
            print(self.response)
            self.success = False
            if self.response is None:
                error = e.get_error_message()
            else:
                try:
                    error = self.response.get('message')
                except Exception as e:
                    error = ''
            self.response = {'error': error}
        else:
            self.success = True
            if auth_required:
                self.authorized = True
            elif login_method:
                self.response.get('token')
                self.fetch_token(self.response.get('token'))
                self.authorized = True
        return self.success if return_bool else self.response

    def login(self, credentials, **kwargs):
        username = credentials.get('username')
        password = credentials.get('password')
        data = {
            "jid": username,
            "ip": credentials.get("source_ip", ""),
            "browser": credentials.get("source_browser", ""),
            "scopes": settings.EJABBERD_API_SCOPES,
            "ttl": settings.EJABBERD_API_TOKEN_TTL
        }
        self.session.auth = requests.auth.HTTPBasicAuth(username, password)
        self._call_method('post', '/issue_token', 201, data=data,
                          login_method=True, auth_required=False, **kwargs)
        self.session.auth = None
        return self.success

    def logout(self, host, **kwargs):
        data = {
            "token": self.token,
            "host": host
        }
        self._call_method('post', '/revoke_token', 200, data=data,
                          **kwargs)
        if self.success:
            self.authorized = False
        return self.success

    def request_token(self, username, ip, browser, **kwargs):
        data = {
            "jid": username,
            "ip": ip,
            "browser": browser,
            "scopes": settings.EJABBERD_API_SCOPES,
            "ttl": settings.EJABBERD_API_TOKEN_TTL
        }
        return self._call_method('post', '/issue_token', 201, data=data, login_method=True, auth_required=False, **kwargs)

    def get_vhosts(self, data={}, **kwargs):

        """ Get Virtual host list """

        return self._call_method('get', '/vhosts', 200, data=data, **kwargs)

    def set_admin(self, data, **kwargs):

        """
            Args: username, host
        """

        return self._call_method('post', '/admins', 201, data=data, **kwargs)

    def del_admin(self, data, **kwargs):

        """
            Args: username, host
        """

        return self._call_method('delete', '/admins', 201, data=data, **kwargs)

    def set_permissions(self, data, **kwargs):
        """
            Example:
                {
                    "username": "username",
                    "host": "example.com",
                    "permissions": {
                        "circles": "write",
                        "users": "read"
                    },
                }
        """

        return self._call_method('post', '/permissions', 201, data=data, **kwargs)

    def get_users(self, data, **kwargs):
        """
            Args: host
        """

        return self._call_method('get', '/users', 200, data=data, **kwargs)

    def get_users_count(self, data, **kwargs):
        """
            Args: host
        """

        return self._call_method('get', '/users/count', 200, data=data, **kwargs)

    def get_groups(self, data, **kwargs):
        """
            Args: host
        """

        return self._call_method('get', '/groups', 200, data=data, **kwargs)

    def get_groups_count(self, data, **kwargs):
        """
            Args: host
        """

        return self._call_method('get', '/groups/count', 200, data=data, **kwargs)

    def create_user(self, data, **kwargs):
        """
            Example:
                data = {
                    'username': "username",
                    'host': "host",
                    'nickname': "nickname",
                    'first_name': "first_name",
                    'last_name': "last_name",
                    'is_admin': True,
                    'expires': date,
                    'vcard': {
                        'nickname': "nickname",
                        'n': {
                            'given': "first_name",
                            'family': "last_name"
                        },
                        'photo': {'type': '', 'binval': ''}
                    }
                }
        """

        self.register_user(data)
        self.set_vcard(data)

        return self.success

    def register_user(self, data, **kwargs):

        user_data = {
            "username": data.get("username", ''),
            "host": data.get("host", ''),
            "password": data.get("password", '')
        }

        self._call_method('post', '/users', 201, data=user_data, **kwargs)
        return self.response

    def unregister_user(self, data, **kwargs):
        """
            Args: username, host
        """

        self._call_method('delete', '/users', 200, data=data, **kwargs)
        return self.response

    def set_vcard(self, data, **kwargs):

        vcard_data = {
            "username": data.get("username"),
            "host": data.get("host"),
            "vcard": data.get('vcard', {})
        }
        return self._call_method('post', '/vcard', 200, data=vcard_data, **kwargs)

    def get_vcard(self, data, **kwargs):
        """
            Args: username, host
        """
        return self._call_method('get', '/vcard', 200, data=data, **kwargs)

    def change_password_api(self, data, **kwargs):
        return self._call_method('put', '/users/set_password', 200, data=data, **kwargs)

    def get_circles(self, data, **kwargs):
        """
            Args: host
        """
        return self._call_method('get', '/circles', 200, data=data, **kwargs)

    def get_circles_info(self, data, **kwargs):
        """
            Args: circle, host
        """
        return self._call_method('get', '/circles/info', 200, data=data, **kwargs)

    def create_circle(self, data, **kwargs):

        """
            Create/update circle
            Example:
                {
                    'circle': 'circle.circle',
                    'host': 'circle.host',
                    'name': 'circle.name',
                    'description': 'circle.description',
                    'displayed_groups': [],
                    'all_users': False
                }

        """
        return self._call_method('post', '/circles', 200, data=data, **kwargs)

    def delete_circle(self, data, **kwargs):
        return self._call_method('delete', '/circles', 200, data=data, **kwargs)

    def create_group(self, data, **kwargs):
        """
            Example:
                {
                    "localpart": "name",
                    "host": "example.com",
                    "owner": "name@example.com",
                    "name": "group name",
                    "privacy": "public/incognito",
                    "index": "none/local/global",
                    "membership": "open/member-only"
                }
        """
        return self._call_method('post', '/groups', 200, data=data, **kwargs)

    def add_circle_members(self, data, **kwargs):

        """
            Example:
                {
                    'circle': circle.circle,
                    'host': circle.host,
                    'grouphost': circle.host, [optional]
                    'members': ['@all@']
                }
        """
        return self._call_method('post', '/circles/members', 200, data=data, **kwargs)

    def get_circle_members(self, data, **kwargs):
        """
            Args: circle, host
        """
        return self._call_method('get', '/circles/members', 200, data=data, **kwargs)

    def del_circle_members(self, data, **kwargs):

        """
            Example:
                {
                    'circle': circle.circle,
                    'host': circle.host,
                    'grouphost': circle.host, [optional]
                    'members': ['@all@']
                }
        """
        return self._call_method('delete', '/circles/members', 200, data=data, **kwargs)

    def stats_host(self, data, **kwargs):
        """
            Args: host
        """
        return self._call_method('get', '/users/online', 200, data=data, **kwargs)

    def get_keys(self, data, **kwargs):
        """
            Args: host
        """
        return self._call_method('get', '/registration/keys', 200, data=data, **kwargs)

    def create_key(self, data, **kwargs):
        """
            Args: host, expire[, description]
        """
        return self._call_method('post', '/registration/keys', 201, data=data, **kwargs)

    def change_key(self, data, key, **kwargs):
        """
            Args: host, expire[, description]
        """
        return self._call_method('put', '/registration/keys/{}'.format(key), 200, data=data, **kwargs)

    def delete_key(self, data, key, **kwargs):
        """
            Args: host
        """
        return self._call_method('delete', '/registration/keys/{}'.format(key), 200, data=data, **kwargs)

    def block_user(self, data, **kwargs):
        """
            Args: host, username, reason
        """
        return self._call_method('post', '/users/block', 200, data=data, **kwargs)

    def unblock_user(self, data, **kwargs):
        """
            Args: host, username
        """
        return self._call_method('delete', '/users/block', 200, data=data, **kwargs)

    def ban_user(self, data, **kwargs):
        """
            Args: host, username
        """
        return self._call_method('post', '/users/ban', 200, data=data, **kwargs)

    def unban_user(self, data, **kwargs):
        """
            Args: host, username
        """
        return self._call_method('delete', '/users/ban', 200, data=data, **kwargs)
