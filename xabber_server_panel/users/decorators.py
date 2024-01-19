from functools import wraps
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator

from .utils import check_permissions


def permission_read(view=None):
    '''
        User read permissions check
    '''

    def decorator(view):
        @wraps(view)
        def wrapper(view, request, *args, **kwargs):
            if check_permissions(request.user, view.app):
                return view(request, *args, **kwargs)
            else:
                raise PermissionDenied
        return wrapper
    return decorator(view) if view else decorator


def permission_write(view=None):
    '''
        User write permissions check
    '''

    def decorator(view):
        @wraps(view)
        def wrapper(view, request, *args, **kwargs):
            if check_permissions(request.user, view.app, permission='write'):
                return view(request, *args, **kwargs)
            else:
                raise PermissionDenied
        return wrapper
    return decorator(view) if view else decorator