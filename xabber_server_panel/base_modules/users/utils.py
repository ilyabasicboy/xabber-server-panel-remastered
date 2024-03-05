from django.utils import timezone
from datetime import datetime

from .models import CustomPermission, User, get_apps_choices


def update_permissions():
    app_list = [app[0] for app in get_apps_choices()]

    for app in app_list:
        for permission in CustomPermission.PERMISSIONS:
            permission, created = CustomPermission.objects.get_or_create(
                permission=permission[0],
                app=app
            )

    # delete old permissions
    CustomPermission.objects.exclude(app__in=app_list).delete()


def check_permissions(user: User, app: str, permission: str = None) -> bool:

    """ Check if user has app permissions """

    if user.is_authenticated:
        if user.is_admin:
            return True

        permissions = CustomPermission.objects.filter(
            user=user,
            app=app
        )

        if permission:
            permissions = permissions.filter(permission=permission)

        return permissions.exists()


def check_users(api, host):

    """
        Check registered users and create
        if it doesn't exist in django db
    """

    try:
        registered_users = api.get_users({"host": host}).get('users')
    except:
        registered_users = []

    if registered_users:

        # Get a list of existing usernames from the User model
        existing_usernames = User.objects.filter(host=host).values_list('username', flat=True)

        # get registered usernames list
        registered_usernames = [user['username'] for user in registered_users]

        # Filter the user_list to exclude existing usernames
        unknown_users = [user for user in registered_users if user['username'] not in existing_usernames]

        # create in db unknown users
        if unknown_users:
            users_to_create = [
                User(
                    username=user['username'],
                    host=host,
                    auth_backend=user['backend']
                )
                for user in unknown_users
            ]
            User.objects.bulk_create(users_to_create)

        # get unregistered users in db and delete
        users_to_delete = User.objects.filter(host=host).exclude(username__in=registered_usernames)
        if users_to_delete:
            users_to_delete.delete()


def block_user(api, user, reason):
    user.reason = reason
    api.block_user(
        {
            "username": user.username,
            "host": user.host,
            'reason': reason
        }
    )
    user.status = 'BLOCKED'
    user.save()


def unblock_user(api, user):
    data = {
        "username": user.username,
        "host": user.host
    }

    if user.status == 'BLOCKED':
        api.unblock_user(data)
        user.reason = None
        if user.is_expired:
            user.expires = None

        user.status = 'ACTIVE'

    if user.status == 'BANNED':
        api.unban_user(data)

        if user.is_expired:
            user.reason = "Your account has expired"
            data['reason'] = "Your account has expired"
            api.block_user(data)
            user.status = 'EXPIRED'
        else:
            user.reason = None
            user.status = 'ACTIVE'

    user.save()


def ban_user(api, user):
    data = {
        "username": user.username,
        "host": user.host
    }

    if not user.is_active:
        api.unblock_user(data)

    api.ban_user(data)
    user.status = 'BANNED'
    user.save()


def set_expires(api, user, expires):
    if expires:
        try:
            user.expires = expires.replace(tzinfo=timezone.utc)
        except Exception as e:
            user.expires = None
    else:
        user.expires = None

    # send data to server
    data = {
        "host": user.host,
        "username": user.username
    }

    if user.status == 'EXPIRED':
        if not user.is_expired:
            user.reason = None
            api.unblock_user(data)
            user.status = 'ACTIVE'
    elif user.is_active:
        if user.is_expired:
            user.reason = "Your account has expired"
            data['reason'] = "Your account has expired"
            api.block_user(data)
            user.status = 'EXPIRED'

    user.save()


def get_user_data_for_api(user, password=None):
    data = {
        'username': user.username,
        'host': user.host,
        'nickname': user.nickname,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'is_admin': user.is_admin,
        'expires': user.expires,
        'vcard': {
            'nickname': user.nickname,
            'n': {
                'given': user.first_name,
                'family': user.last_name
            },
            'photo': {'type': '', 'binval': ''}
        }
    }
    if password:
        data['password'] = password
    return data