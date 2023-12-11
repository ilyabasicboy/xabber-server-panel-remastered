# Generated by Django 3.2.23 on 2023-11-22 11:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='auth_backend',
            field=models.CharField(choices=[('sql', 'internal'), ('ldap', 'LDAP')], default='sql', max_length=128),
        ),
    ]
