from .models import CustomPermission, User


def check_permissions(user: User, app: str, permission: str = None) -> bool:

    """ Check if user has app permissions """

    if user.is_admin:
        return True

    permissions = CustomPermission.objects.filter(
        user=user,
        app=app
    )

    if permission:
        permissions = permissions.filter(permission=permission)

    return permissions.exists()