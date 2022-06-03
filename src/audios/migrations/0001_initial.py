# Generated by Django 3.2.12 on 2022-06-03 20:07

import audios.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('galleries', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Audio',
            fields=[
                ('galleryfile_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='galleries.galleryfile')),
                ('original', models.FileField(help_text='The original uploaded file.', upload_to=audios.models.get_audio_upload_path)),
                ('gallery', models.ForeignKey(help_text='The gallery this audio belongs to.', on_delete=django.db.models.deletion.CASCADE, related_name='audios', to='galleries.gallery')),
            ],
            options={
                'abstract': False,
            },
            bases=('galleries.galleryfile',),
        ),
    ]
