# Generated by Django 4.1.2 on 2022-11-09 21:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('oceandbs', '0003_remove_storage_payment_methods_paymentmethod_storage_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='paymentmethod',
            name='title',
        ),
    ]