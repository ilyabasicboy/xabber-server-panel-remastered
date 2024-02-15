from functools import wraps
from django.http import HttpResponseRedirect
from django.shortcuts import reverse
from django.contrib import messages

from .utils import check_permissions


def permission_read(func):

    @wraps(func)
    def wrapper(view, request, *args, **kwargs):

        if check_permissions(request.user, view.app):
            return func(view, request, *args, **kwargs)
        else:
            messages.error(request, 'You have no permissions for this request.')
            return HttpResponseRedirect(reverse('home'))

    return wrapper


def permission_write(func):

    @wraps(func)
    def wrapper(view, request, *args, **kwargs):

        if check_permissions(request.user, view.app, permission='write'):
            return func(view, request, *args, **kwargs)
        else:
            messages.error(request, 'You have no permissions for this request.')
            return HttpResponseRedirect(reverse('home'))

    return wrapper


def permission_admin(func):

    @wraps(func)
    def wrapper(view, request, *args, **kwargs):

        if request.user.is_admin:
            return func(view, request, *args, **kwargs)
        else:
            messages.error(request, 'You have no permissions for this request.')
            return HttpResponseRedirect(reverse('home'))

    return wrapper