# Generated by Django 5.0.3 on 2024-05-06 17:44

import users.sentinel
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('albums', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='album',
            name='owner',
            field=models.ForeignKey(help_text='The creator of this album.', on_delete=models.SET(users.sentinel.get_sentinel_user), related_name='albums', to=settings.AUTH_USER_MODEL),
        ),
    ]
