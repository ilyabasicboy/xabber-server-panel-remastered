from django.http import HttpResponseRedirect
from django.shortcuts import reverse
from django.conf import settings

from xabber_server_panel.utils import server_installed

from .utils import check_predefined_config


class InstallationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        """
         Server installation check.
         Redirect to installation page if server is installed
        """

        response = self.get_response(request)

        # check server installed
        if not server_installed() and not request.path.startswith(settings.MEDIA_URL):

            # check predefined config
            if check_predefined_config():

                # redirect to quick install
                if request.path != reverse('installation:quick'):
                    return HttpResponseRedirect(reverse('installation:quick'))
            else:

                # redirect to base installation page
                if request.path != reverse('installation:steps'):
                    return HttpResponseRedirect(reverse('installation:steps'))

        return response