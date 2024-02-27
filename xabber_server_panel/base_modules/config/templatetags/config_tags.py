from django import template

from xabber_server_panel.utils import get_modules_data

register = template.Library()


@register.simple_tag()
def get_external_modules():
    return get_modules_data()