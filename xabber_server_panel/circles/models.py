from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from xabber_server_panel.users.models import User


def validate_circle(value):
    # Specify the characters to be excluded
    excluded_characters = "!@#$%^&*()_+={}[]|\:;<>,.?/~`"

    # Check if any excluded character is present in the value
    if any(char in excluded_characters for char in value):
        raise ValidationError("Invalid characters in the field.")


class Circle(models.Model):

    class Meta:
        ordering = ['circle']

    circle = models.CharField(
        max_length=256,
        validators=[validate_circle]
    )
    host = models.CharField(max_length=256)
    name = models.CharField(
        max_length=100,
        null=True, blank=True
    )
    description = models.CharField(
        max_length=256,
        null=True,
        blank=True
    )
    subscribes = models.TextField(
        null=True,
        blank=True
    )
    created = models.DateTimeField(
        default=timezone.now,
        blank=True
    )
    prefix = models.CharField(
        max_length=10,
        null=True,
        blank=True
    )
    members = models.ManyToManyField(
        User,
        blank=True,
        related_name='circles'
    )

    class Meta:
        unique_together = ('circle', 'host')

    @property
    def full_jid(self):
        return u'{}@{}'.format(self.circle, self.host)

    @property
    def is_system(self):
        return self.prefix is not None

    @property
    def get_subscribes(self):
        if self.subscribes:
            return self.subscribes.split(',')
        else:
            return []

    @property
    def get_members_list(self):
        members = []
        for member in self.members.all():
            members += [member.full_jid]
        return members

    def __str__(self):
        return self.full_jid