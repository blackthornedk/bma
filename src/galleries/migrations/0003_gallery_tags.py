# Generated by Django 3.2.12 on 2022-08-28 10:44

from django.db import migrations
import taggit.managers


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('taggit', '0005_auto_20220424_2025'),
        ('galleries', '0002_gallery_owner'),
        ('utils', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='gallery',
            name='tags',
            field=taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', through='utils.UUIDTaggedItem', to='taggit.Tag', verbose_name='Tags'),
        ),
    ]