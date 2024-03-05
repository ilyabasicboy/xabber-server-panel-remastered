from django import template

from xabber_server_panel.base_modules.config.utils import get_srv_records, get_modules_data

register = template.Library()


@register.simple_tag()
def get_external_modules():
    return get_modules_data()