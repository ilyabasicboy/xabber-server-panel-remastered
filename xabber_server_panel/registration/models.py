from django.db import models
from xabber_server_panel.dashboard.models import VirtualHost


class RegistrationSettings(models.Model):
    STATUS_CHOICES = [
        ('disabled', 'disabled'),
        ('link', 'link'),
        ('public', 'public'),
    ]

    host = models.ForeignKey(
        VirtualHost,
        on_delete=models.CASCADE
    )
    status = models.CharField(
        default='disabled',
        max_length=50,
        choices=STATUS_CHOICES
    )
    url = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.host.name