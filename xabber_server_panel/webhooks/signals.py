import django.dispatch
from django.dispatch import receiver
from django.http import HttpResponse
from datetime import timedelta
from django.conf import settings
from django.utils import timezone

from xabber_server_panel.webhooks.utils import check_signature, WebHookResponse
from xabber_server_panel.base_modules.users.models import User

import json

webhook_received = django.dispatch.Signal()


@receiver(webhook_received)
def webhook_received_handler(sender, **kwargs):
    """
    Request path: "/xmppserver"
    Request body:
        { "target": "user",
          "action": "create/remove",
          "username": "bob",
          "host": "domain.com"
        }
    """

    path = kwargs.get('path')
    if path.rstrip('/') != 'xmppserver':
        return
    request = kwargs.get('request')
    if not check_signature(request):
        raise WebHookResponse(response=HttpResponse('Unauthorized', status=401))
    try:
        _json = json.loads(request.body)
    except:
        raise WebHookResponse(response=HttpResponse(status=400))
    if _json.get('target') == 'user':
        if _json.get('action') == 'create' and _json.get('username') and _json.get('host'):
            if User.objects.filter(username=_json.get('username'), host=_json.get('host')).exists():
                raise WebHookResponse(response=HttpResponse(status=201))
            new_user = User(username=_json.get('username'), host=_json.get('host'))
            if settings.DEFAULT_ACCOUNT_LIFETIME > 0:
                expires = timezone.now() + timedelta(days=settings.DEFAULT_ACCOUNT_LIFETIME)
                new_user.expires = expires
            new_user.save()
            raise WebHookResponse(response=HttpResponse(status=201))

        if _json.get('action') == 'remove' and _json.get('username') and _json.get('host'):
            User.objects.filter(username=_json.get('username'), host=_json.get('host')).delete()
            raise WebHookResponse(response=HttpResponse(status=201))
    return