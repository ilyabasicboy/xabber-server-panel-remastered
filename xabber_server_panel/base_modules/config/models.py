from django.db import models


class VirtualHost(models.Model):
    name = models.CharField(
        max_length=256,
        unique=True
    )
    check_dns = models.BooleanField(default=False)

    def __str__(self):
        return self.name


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
    deref_aliases = models.CharField(
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
        on_delete=models.CASCADE,
        related_name='ldap_settings'
    )
    enabled = models.BooleanField(
        default=False
    )

    def __str__(self):
        return 'LDAP Settings %s' % self.host.name


class LDAPServer(models.Model):
    server = models.CharField(max_length=50)
    settings = models.ForeignKey(
        LDAPSettings,
        on_delete=models.CASCADE,
        related_name='servers'
    )

    def __str__(self):
        return 'LDAP Settings {}'.format(self.server)


class RootPage(models.Model):
    module = models.CharField(
        max_length=100,
        default="home"
    )

    def __str__(self):
        return self.module


class Module(models.Model):

    name = models.CharField(
        max_length=30
    )
    verbose_name = models.TextField(
        blank=True,
        null=True
    )
    version = models.CharField(
        max_length=20
    )
    files = models.TextField(
        blank=True,
        null=True
    )
    root_page = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.name


def check_vhost(vhost):
    return VirtualHost.objects.filter(name=vhost).exists() or vhost == "global"


class BaseXmppModule(models.Model):

    class Meta:
        managed = False

    def __init__(self, vhost, name, module_options):
        self.vhost = vhost
        self.name = name
        self.module_options = module_options
        if not check_vhost(self.vhost):
            raise ValueError("Virtualhost doesn`t exist")
        if not isinstance(self.module_options, dict):
            raise ValueError("Module options must be a dictionary")

    def get_config(self):
        return {
            "type": "module",
            "vhost": self.vhost,
            "name": self.name,
            "module_options": self.module_options
        }

    def __str__(self):
        return self.name


class BaseXmppOption(models.Model):
    class Meta:
        managed = False

    def __init__(self, vhost, name, value):
        self.vhost = vhost
        self.name = name
        self.value = value
        if not check_vhost(self.vhost):
            raise ValueError("Virtualhost doesn`t exist")
        if isinstance(value, dict):
            raise ValueError("Value must not be a dictionary")

    def get_config(self):
        return {
            "type": "option",
            "vhost": self.vhost,
            "name": self.name,
            "value": self.value
        }

    def __str__(self):
        return self.name


class BaseModuleConfig(models.Model):
    GLOBAL_HOST_NAME = "global"

    class Meta:
        managed = False

    virtual_host = models.CharField(
        max_length=255,
        verbose_name="Related virtual host",
        blank=False,
        null=False
    )