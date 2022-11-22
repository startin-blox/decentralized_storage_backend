# Generated by Django 4.1.2 on 2022-11-22 18:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oceandbs', '0015_rename_original_url_file_public_url_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='quote',
            name='upload_status',
        ),
        migrations.AddField(
            model_name='quote',
            name='status',
            field=models.CharField(blank=True, choices=[('0', 'No such quote'), ('1', 'Waiting for files to be uploaded'), ('100', 'Processing payment'), ('200', 'Processing payment failure modes'), ('300', 'Uploading file to storage'), ('400', 'Upload done'), ('401', 'Upload failure modes')], max_length=256, null=True),
        ),
    ]
