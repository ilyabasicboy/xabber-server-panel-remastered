# Generated by Django 3.2.25 on 2024-05-02 09:22

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Certificate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('domain', models.TextField()),
                ('expiration_date', models.DateTimeField(blank=True, null=True)),
                ('status', models.IntegerField(choices=[(0, 'Success'), (1, 'Pending'), (2, 'Error')], default=0)),
                ('reason', models.TextField(blank=True, null=True)),
            ],
        ),
    ]