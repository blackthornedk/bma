# Generated by Django 3.2.12 on 2022-08-28 10:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('taggit', '0005_auto_20220424_2025'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='UUIDTaggedItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.UUIDField(db_index=True, verbose_name='object ID')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='utils_uuidtaggeditem_tagged_items', to='contenttypes.contenttype', verbose_name='content type')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='utils_uuidtaggeditem_items', to='taggit.tag')),
            ],
            options={
                'verbose_name': 'Tag',
                'verbose_name_plural': 'Tags',
            },
        ),
    ]