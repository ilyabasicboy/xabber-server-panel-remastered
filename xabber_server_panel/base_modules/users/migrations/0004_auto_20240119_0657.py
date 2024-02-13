# Generated by Django 3.2.23 on 2024-01-19 06:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20231212_1232'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permission', models.CharField(choices=[('read', 'read'), ('write', 'write')], max_length=10)),
                ('app', models.CharField(choices=[('dashboard', 'Dashboard'), ('users', 'Users'), ('circles', 'Circles'), ('groups', 'Groups'), ('registration', 'Registration'), ('settings', 'Settings')], max_length=100)),
            ],
        ),
        migrations.AlterField(
            model_name='user',
            name='auth_backend',
            field=models.CharField(blank=True, choices=[('sql', 'sql'), ('ldap', 'LDAP')], default='sql', max_length=128),
        ),
        migrations.AddField(
            model_name='user',
            name='permissions',
            field=models.ManyToManyField(blank=True, to='users.CustomPermission'),
        ),
    ]