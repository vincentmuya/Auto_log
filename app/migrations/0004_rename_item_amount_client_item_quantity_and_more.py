# Generated by Django 4.2.6 on 2023-11-06 09:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_profile'),
    ]

    operations = [
        migrations.RenameField(
            model_name='client',
            old_name='item_amount',
            new_name='item_quantity',
        ),
        migrations.AddField(
            model_name='client',
            name='item_total_amount',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='client',
            name='item_unit_price',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
