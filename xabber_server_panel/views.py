from django.shortcuts import render, reverse
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView

from xabber_server_panel.config.models import RootPage


class HomePage(TemplateView):

    template_name = 'home.html'

    def get(self, request, *args, **kwargs):

        # redirect to module root
        rp = RootPage.objects.first()
        if rp and rp.module:
            if rp.module != 'home':
                return HttpResponseRedirect(
                    reverse(f'{rp.module}:root')
                )

        context = {}
        return self.render_to_response(context, **kwargs)