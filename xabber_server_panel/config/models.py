from django.db import models

from xabber_server_panel.dashboard.models import VirtualHost


class LDAPSettings(models.Model):
    ENCRYPT_CHOICES = (
        ('none', 'none'),
        ('tls', 'tls')
    )

    TLS_VERIFY_CHOICES = (
        ('false', 'false'),
        ('soft', 'soft'),
        ('hard', 'hard'),
    )

    DEFER_ALIASES_CHOICES = (
        ('never', 'never'),
        ('always', 'always'),
        ('finding', 'finding'),
        ('searching', 'searching'),
    )

    encrypt = models.CharField(
        max_length=10,
        choices=ENCRYPT_CHOICES,
        null=True, blank=True
    )
    tls_verify = models.CharField(
        max_length=10,
        choices=TLS_VERIFY_CHOICES,
        null=True, blank=True
    )
    tls_cacertfile = models.CharField(
        max_length=100,
        null=True, blank=True
    )
    tls_depth = models.PositiveSmallIntegerField(
        null=True, blank=True
    )
    port = models.PositiveSmallIntegerField(
        default=389
    )
    rootdn = models.CharField(
        max_length=100,
        null=True, blank=True
    )
    password = models.CharField(
        max_length=50,
        null=True, blank=True
    )
    defer_aliases = models.CharField(
        max_length=100,
        choices=DEFER_ALIASES_CHOICES,
        null=True, blank=True
    )
    base = models.CharField(
        max_length=100
    )
    uids = models.CharField(
        max_length=256,
        null=True, blank=True
    )
    filter = models.CharField(
        max_length=256,
        null=True, blank=True
    )
    dn_filter = models.CharField(
        max_length=256,
        null=True, blank=True
    )
    host = models.ForeignKey(
        VirtualHost,
        on_delete=models.CASCADE
    )
    enabled = models.BooleanField(
        default=False
    )

    def __str__(self):
        return f'LDAP Settings {self.host.name}'


class LDAPServer(models.Model):
    server = models.CharField(max_length=50)
    settings = models.ForeignKey(
        LDAPSettings,
        on_delete=models.CASCADE,
        related_name='servers'
    )

    def __str__(self):
        return 'LDAP Settings {}'.format(self.server)