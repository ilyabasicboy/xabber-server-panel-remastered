from django import template
from django.conf import settings

from xabber_server_panel.utils import get_modules

import os


register = template.Library()


@register.simple_tag()
def get_external_modules():
    return get_modules()