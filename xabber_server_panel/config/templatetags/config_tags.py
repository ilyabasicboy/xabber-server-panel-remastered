from django import template
from django.conf import settings

import os


register = template.Library()


@register.simple_tag()
def get_external_modules():
    if os.path.isdir(settings.MODULES_DIR):
        return os.listdir(settings.MODULES_DIR)
    return