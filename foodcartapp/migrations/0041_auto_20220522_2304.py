# Generated by Django 3.2 on 2022-05-22 23:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0040_auto_20220522_2302'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='client_name',
            new_name='firstname',
        ),
        migrations.RenameField(
            model_name='order',
            old_name='client_surname',
            new_name='lastname',
        ),
        migrations.RenameField(
            model_name='order',
            old_name='contact_phone',
            new_name='phonenumber',
        ),
    ]