# Generated by Django 3.2.23 on 2024-02-01 10:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BaseXmppModule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='BaseXmppOption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='RootPage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('module', models.CharField(default='home', max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='VirtualHost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='LDAPSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('encrypt', models.CharField(blank=True, choices=[('none', 'none'), ('tls', 'tls')], max_length=10, null=True)),
                ('tls_verify', models.CharField(blank=True, choices=[('false', 'false'), ('soft', 'soft'), ('hard', 'hard')], max_length=10, null=True)),
                ('tls_cacertfile', models.CharField(blank=True, max_length=100, null=True)),
                ('tls_depth', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('port', models.PositiveSmallIntegerField(default=389)),
                ('rootdn', models.CharField(blank=True, max_length=100, null=True)),
                ('password', models.CharField(blank=True, max_length=50, null=True)),
                ('defer_aliases', models.CharField(blank=True, choices=[('never', 'never'), ('always', 'always'), ('finding', 'finding'), ('searching', 'searching')], max_length=100, null=True)),
                ('base', models.CharField(max_length=100)),
                ('uids', models.CharField(blank=True, max_length=256, null=True)),
                ('filter', models.CharField(blank=True, max_length=256, null=True)),
                ('dn_filter', models.CharField(blank=True, max_length=256, null=True)),
                ('enabled', models.BooleanField(default=False)),
                ('host', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='config.virtualhost')),
            ],
        ),
        migrations.CreateModel(
            name='LDAPServer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('server', models.CharField(max_length=50)),
                ('settings', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='servers', to='config.ldapsettings')),
            ],
        ),
    ]
