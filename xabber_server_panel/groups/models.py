from django.db import models
from django.utils import timezone


class GroupChat(models.Model):
    name = models.CharField(max_length=256)
    host = models.CharField(max_length=256)
    owner = models.CharField(max_length=256)
    members = models.PositiveSmallIntegerField()
    created = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('name', 'host')

    @property
    def full_jid(self):
        return '{}@{}'.format(self.name, self.host)

    def __str__(self):
        return self.full_jid