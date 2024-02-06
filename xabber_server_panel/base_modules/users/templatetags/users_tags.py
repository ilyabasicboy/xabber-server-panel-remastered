from django import template
from ..models import User
from ..utils import check_permissions


register = template.Library()


@register.simple_tag()
def get_user_by_jid(jid):
    try:
        username, host = jid.split('@')
    except:
        return None

    user = User.objects.filter(username=username, host=host).first()

    return user


@register.simple_tag()
def check_user_permissions(user, app, permission=None):
    return check_permissions(user, app, permission)