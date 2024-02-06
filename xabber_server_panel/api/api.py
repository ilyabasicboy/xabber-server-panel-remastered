import requests

from django.conf import settings


class EjabberdAPI(object):

    def __init__(self):
        self.token = None
        self.session = requests.Session()
        self.base_url = settings.EJABBERD_API_URL
        self.raw_response = None
        self.response = {}
        self.errors = []

    def fetch_token(self, token):
        self.token = token
        self.session.headers.update({'Authorization': 'Bearer {}'.format(token)})

    def _wrapped_call(self, method, url, data, http_method):

        """ call session method and resolve exceptions """

        try:
            # check method and provide data
            if http_method in ("post", "delete", "put"):
                self.raw_response = method(url, json=data, timeout=settings.HTTP_REQUEST_TIMEOUT)
            elif http_method == "get":
                self.raw_response = method(url, params=data, timeout=settings.HTTP_REQUEST_TIMEOUT)

        # resolve exceptions
        except requests.exceptions.ConnectionError:
            self.errors += ['Connection error.']
        except requests.exceptions.RequestException as e:
            self.errors += [f'Request error: {e}']
        except Exception as e:
            self.errors += [e]

    def _call_method(self, http_method, relative_url, data):

        """
             request data from api,
             resolve exceptions and check response data
         """

        method = getattr(self.session, http_method)
        url = self.base_url + relative_url

        # request data from api
        self._wrapped_call(method, url, data, http_method)

        # check errors and convert response to json
        if self.raw_response:
            self._parse_response()

        if settings.DEBUG:
            print('request:', http_method, url, data)
            print('raw response:', self.raw_response)
            print('response', self.response)
            print('errors:', self.errors)

        self.response['errors'] = self.errors


    def _parse_response(self):

        """ Jsonify response or add errors if response is not ok """

        if self.raw_response.ok:
            try:
                json_raw_response = self.raw_response.json()
                if isinstance(json_raw_response, dict):
                    self.response = json_raw_response
            except Exception:
                self.errors += ['invalid_json_response']
        else:
            self.errors += [self.raw_response.reason]

    def login(self, credentials):
        """
            Args: username, password
        """

        username = credentials.get('username')
        password = credentials.get('password')
        data = {
            "jid": username,
            "ip": credentials.get("source_ip", ""),
            "browser": credentials.get("source_browser", ""),
            "scopes": settings.EJABBERD_API_SCOPES,
            "ttl": settings.EJABBERD_API_TOKEN_TTL
        }

        # set auth header
        self.session.auth = requests.auth.HTTPBasicAuth(username, password)

        self._call_method('post', '/issue_token', data=data)

        # fetch token if success
        if not self.errors:
            self.response.get('token')
            self.fetch_token(self.response.get('token'))

        return self.response

    def logout(self, host):
        data = {
            "token": self.token,
            "host": host
        }
        self._call_method('post', '/revoke_token', data=data)
        return self.response

    def request_token(self, username, ip, browser):
        data = {
            "jid": username,
            "ip": ip,
            "browser": browser,
            "scopes": settings.EJABBERD_API_SCOPES,
            "ttl": settings.EJABBERD_API_TOKEN_TTL
        }
        self._call_method('post', '/issue_token', data=data)
        return self.response

    def get_vhosts(self, data={}):

        """ Get Virtual host list """

        self._call_method('get', '/vhosts', data=data)
        return self.response

    def set_admin(self, data):

        """
            Args: username, host
        """

        self._call_method('post', '/admins', data=data)
        return self.response

    def del_admin(self, data):

        """
            Args: username, host
        """

        self._call_method('delete', '/admins', data=data)
        return self.response

    def set_permissions(self, data):
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
        self._call_method('post', '/permissions', data=data)
        return self.response

    def get_users(self, data):
        """
            Args: host
        """

        self._call_method('get', '/users', data=data)
        return self.response

    def get_users_count(self, data):
        """
            Args: host
        """

        self._call_method('get', '/users/count', data=data)
        return self.response

    def get_groups(self, data):
        """
            Args: host
        """
        self._call_method('get', '/groups', data=data)
        return self.response

    def get_groups_count(self, data):
        """
            Args: host
        """

        self._call_method('get', '/groups/count', data=data)
        return self.response

    def create_user(self, data):
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

        return self.response

    def register_user(self, data):

        user_data = {
            "username": data.get("username", ''),
            "host": data.get("host", ''),
            "password": data.get("password", '')
        }

        self._call_method('post', '/users', data=user_data)
        return self.response

    def unregister_user(self, data):
        """
            Args: username, host
        """

        self._call_method('delete', '/users', data=data)
        return self.response

    def set_vcard(self, data):

        vcard_data = {
            "username": data.get("username"),
            "host": data.get("host"),
            "vcard": data.get('vcard', {})
        }
        self._call_method('post', '/vcard', data=vcard_data)
        return self.response

    def get_vcard(self, data):
        """
            Args: username, host
        """

        self._call_method('get', '/vcard', data=data)
        return self.response

    def change_password_api(self, data):

        """
            Args: password, username, host
        """

        self._call_method('put', '/users/set_password', data=data)
        return self.response

    def get_circles(self, data):
        """
            Args: host
        """

        self._call_method('get', '/circles', data=data)
        return self.response

    def get_circles_info(self, data):
        """
            Args: circle, host
        """

        self._call_method('get', '/circles/info', data=data)
        return self.response

    def create_circle(self, data):

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

        self._call_method('post', '/circles', data=data, )
        return self.response

    def delete_circle(self, data):
        """
            Args: circle, host
        """
        self._call_method('delete', '/circles', data=data)
        return self.response

    def create_group(self, data):
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

        self._call_method('post', '/groups', data=data)
        return self.response

    def add_circle_members(self, data):

        """
            Example:
                {
                    'circle': circle.circle,
                    'host': circle.host,
                    'grouphost': circle.host, [optional]
                    'members': ['@all@']
                }
        """
        self._call_method('post', '/circles/members', data=data)
        return self.response

    def get_circle_members(self, data):
        """
            Args: circle, host
        """
        self._call_method('get', '/circles/members', data=data)
        return self.response

    def del_circle_members(self, data):

        """
            Example:
                {
                    'circle': circle.circle,
                    'host': circle.host,
                    'grouphost': circle.host, [optional]
                    'members': ['@all@']
                }
        """
        self._call_method('delete', '/circles/members', data=data)
        return self.response

    def stats_host(self, data):
        """
            Args: host
        """

        self._call_method('get', '/users/online', data=data)
        return self.response

    def get_keys(self, data):
        """
            Args: host
        """

        self._call_method('get', '/registration/keys', data=data)
        return self.response

    def create_key(self, data):
        """
            Args: host, expire[, description]
        """

        self._call_method('post', '/registration/keys', data=data)
        return self.response

    def change_key(self, data, key):
        """
            Args: host, expire[, description]
        """

        self._call_method('put', '/registration/keys/{}'.format(key), data=data)
        return self.response

    def delete_key(self, data, key):
        """
            Args: host
        """
        self._call_method('delete', '/registration/keys/{}'.format(key), data=data)
        return self.response

    def block_user(self, data):
        """
            Args: host, username, reason
        """

        self._call_method('post', '/users/block', data=data)
        return self.response

    def unblock_user(self, data):
        """
            Args: host, username
        """

        self._call_method('delete', '/users/block', data=data)
        return self.response

    def ban_user(self, data):
        """
            Args: host, username
        """

        self._call_method('post', '/users/ban', data=data)
        return self.response

    def unban_user(self, data):
        """
            Args: host, username
        """

        self._call_method('delete', '/users/ban', data=data)
        return self.response
