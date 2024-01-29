from .models import CustomPermission, User


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


def check_users(user, host):

    """
        Check registered users and create
        if it doesn't exist in django db
    """

    try:
        registered_users = user.api.xabber_registered_users({"host": host}).get('users')
    except:
        registered_users = []

    if registered_users:

        # Get a list of existing usernames from the User model
        existing_usernames = User.objects.values_list('username', flat=True)

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