# Generated by Django 5.0.3 on 2024-05-06 17:44

import django.db.models.deletion
import utils.upload
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('files', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Picture',
            fields=[
                ('basefile_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='files.basefile')),
                ('original', models.ImageField(help_text='The original uploaded picture.', max_length=255, upload_to=utils.upload.get_upload_path)),
            ],
            options={
                'abstract': False,
                'base_manager_name': 'objects',
            },
            bases=('files.basefile',),
        ),
    ]
