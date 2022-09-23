# Generated by Django 3.2.12 on 2022-08-29 18:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('galleries', '0003_gallery_tags'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='galleryfile',
            options={'ordering': ['created']},
        ),
        migrations.AddField(
            model_name='galleryfile',
            name='description',
            field=models.TextField(blank=True, help_text='The description of this file. Optional.'),
        ),
        migrations.AlterField(
            model_name='gallery',
            name='status',
            field=models.CharField(choices=[('PENDING_MODERATION', 'Pending Moderation'), ('UNPUBLISHED', 'Unpublished'), ('PUBLISHED', 'Published'), ('PENDING_DELETION', 'Pending Deletion')], default='PENDING_MODERATION', help_text='The status of this gallery. Only published galleries are visible on the website.', max_length=20),
        ),
        migrations.AlterField(
            model_name='galleryfile',
            name='gallery',
            field=models.ForeignKey(help_text='The gallery this file belongs to.', on_delete=django.db.models.deletion.CASCADE, related_name='galleryfiles', to='galleries.gallery'),
        ),
        migrations.AlterField(
            model_name='galleryfile',
            name='status',
            field=models.CharField(choices=[('PENDING_MODERATION', 'Pending Moderation'), ('UNPUBLISHED', 'Unpublished'), ('PUBLISHED', 'Published'), ('PENDING_DELETION', 'Pending Deletion')], default='PENDING_MODERATION', help_text='The status of this file. Only published files are visible on the public website (as long as the gallery is also published).', max_length=20),
        ),
    ]
