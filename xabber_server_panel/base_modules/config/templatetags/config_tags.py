from django import template

from xabber_server_panel.utils import get_modules_data
from xabber_server_panel.base_modules.config.utils import get_srv_records

register = template.Library()


@register.simple_tag()
def get_external_modules():
    return get_modules_data()


@register.simple_tag()
def check_host_in_dns(host):
    records = get_srv_records(host)
    return 'error' not in records