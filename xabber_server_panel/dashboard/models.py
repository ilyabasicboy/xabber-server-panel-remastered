from django.db import models


class VirtualHost(models.Model):
    name = models.CharField(max_length=256)

    def __str__(self):
        return self.name