from django.db import models
from django.utils import timezone
from django.apps import apps
from django.contrib.auth.hashers import make_password
from django.contrib.auth import _get_backends, load_backend
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.contrib.auth.validators import UnicodeUsernameValidator

from xabber_server_panel.utils import token_to_int
from xabber_server_panel.api.api import EjabberdAPI

import pytz


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, password, **extra_fields):
        """
        Create and save a user with the given username and password.
        """
        if not username:
            raise ValueError('The given username must be set')
        # Lookup the real model class from the global app registry so this
        # manager method can be used in migrations. This is fine because
        # managers are by definition working on the real model.
        GlobalUserModel = apps.get_model(self.model._meta.app_label, self.model._meta.object_name)
        username = GlobalUserModel.normalize_username(username)
        user = self.model(username=username, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, password, **extra_fields)

    def with_perm(self, perm, is_active=True, include_superusers=True, backend=None, obj=None):
        if backend is None:
            backends = _get_backends(return_tuples=True)
            if len(backends) == 1:
                backend, _ = backends[0]
            else:
                raise ValueError(
                    'You have multiple authentication backends configured and '
                    'therefore must provide the `backend` argument.'
                )
        elif not isinstance(backend, str):
            raise TypeError(
                'backend must be a dotted import path string (got %r).'
                % backend
            )
        else:
            backend = load_backend(backend)
        if hasattr(backend, 'with_perm'):
            return backend.with_perm(
                perm,
                is_active=is_active,
                include_superusers=include_superusers,
                obj=obj,
            )
        return self.none()


class User(AbstractBaseUser, PermissionsMixin):

    AUTH_BACKENDS = [
        ('sql', 'sql'),
        ('ldap', 'LDAP')
    ]

    STATUSES = [
        ('ACTIVE', 'ACTIVE'),
        ('BANNED', 'BANNED'),
        ('EXPIRED', 'EXPIRED'),
        ('SUSPENDED', 'SUSPENDED'),
    ]
    USERNAME_FIELD = 'username'
    username_validator = UnicodeUsernameValidator()
    objects = UserManager()

    token = models.TextField(
        blank=True,
        null=True
    )
    username = models.CharField(
        max_length=256,
        unique=True,
        validators=[username_validator],
        error_messages={
            'unique': "A user with that username already exists.",
        },
    )
    password = models.CharField(max_length=128, null=True)
    auth_backend = models.CharField(
        max_length=128,
        choices=AUTH_BACKENDS,
        default='sql',
        blank=True
    )
    is_admin = models.BooleanField(default=False)
    host = models.CharField(max_length=256)
    nickname = models.CharField(max_length=100, null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    # photo = models.ImageField(
    #     verbose_name='Photo',
    #     upload_to='upload',
    #     validators=[
    #         FileExtensionValidator(allowed_extensions=['jpg', 'png', 'jpeg'])],
    #     null=True
    # )
    created = models.DateTimeField(
        default=timezone.now,
        blank=True
    )
    expires = models.DateTimeField(
        null=True,
        blank=True
    )
    status = models.CharField(
        choices=STATUSES,
        default='ACTIVE',
        max_length=255,
        blank=True
    )

    class Meta:
        unique_together = ('username', 'host')

    @property
    def is_active(self):
        return self.status == 'ACTIVE'

    @property
    def full_jid(self):
        return u'{}@{}'.format(self.username, self.host)

    @property
    def get_initials(self):
        if self.first_name and self.last_name:
            return u"{}{}".format(self.first_name[0], self.last_name[0])
        else:
            return self.username[0:2]

    @property
    def api(self):
        api = EjabberdAPI()
        if self.token:
            api.fetch_token(self.token)
        return api

    @property
    def is_expired(self):
        return self.expires and self.expires < timezone.now()

    # @property
    # def full_name(self):
    #     if self.first_name and self.last_name:
    #         formatted_name = u'{} {}'.format(self.first_name, self.last_name).strip()
    #         if len(formatted_name) > 0:
    #             return formatted_name
    #         else:
    #             return self.full_jid
    #     else:
    #         return self.full_jid
    #
    # def get_full_name(self):
    #     full_name = u'{}@{}'.format(self.first_name, self.last_name)
    #     return full_name.strip()
    #
    # def get_short_name(self):
    #     return self.first_name
    #
    # @property
    # def vhost(self):
    #     try:
    #         return VirtualHost.objects.get(name=self.host)
    #     except VirtualHost.DoesNotExist:
    #         return None
    #
    # @property
    # def allowed_delete(self):
    #     return False if self.auth_backend == 'ldap' else True
    #
    # @property
    # def allowed_change_vcard(self):
    #     return True
    #
    # @property
    # def allowed_change_password(self):
    #     return False if self.auth_backend == 'ldap' else True
    #
    # def __str__(self):
    #     return self.full_jid
    #
    # def has_perm(self, perm, obj=None):
    #     """
    #     Return True if the user has the specified permission. Query all
    #     available auth backends, but return immediately if any backend returns
    #     True. Thus, a user who has permission from a single auth backend is
    #     assumed to have permission in general. If an object is provided, check
    #     permissions for that object.
    #     """
    #     # # Active superusers have all permissions.
    #     if self.is_active and self.is_superuser or self.is_active and self.is_admin:
    #         return True
    #
    #     # Otherwise we need to check the backends.
    #     return _user_has_perm(self, perm, obj)