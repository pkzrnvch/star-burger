# Generated by Django 3.2 on 2022-05-23 17:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0042_auto_20220523_1729'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='OrderItem',
            new_name='OrderProductItem',
        ),
    ]