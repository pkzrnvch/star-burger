# Generated by Django 3.2 on 2022-05-26 06:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0048_auto_20220526_0545'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('B', 'Картой'), ('C', 'Наличными'), ('N', 'Не определен')], db_index=True, default='N', max_length=1, verbose_name='способ платежа'),
        ),
    ]