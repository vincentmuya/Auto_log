# Generated by Django 4.2.6 on 2023-11-07 08:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_rename_item_amount_itemhistory_item_total_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemhistory',
            name='slug',
            field=models.SlugField(null=True),
        ),
    ]
