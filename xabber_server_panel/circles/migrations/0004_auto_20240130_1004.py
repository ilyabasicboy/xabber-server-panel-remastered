# Generated by Django 3.2.23 on 2024-01-30 10:04

from django.db import migrations, models
import xabber_server_panel.circles.models


class Migration(migrations.Migration):

    dependencies = [
        ('circles', '0003_alter_circle_subscribes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='circle',
            name='circle',
            field=models.CharField(max_length=256, validators=[xabber_server_panel.circles.models.validate_circle]),
        ),
        migrations.AlterField(
            model_name='circle',
            name='description',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
        migrations.AlterField(
            model_name='circle',
            name='name',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
