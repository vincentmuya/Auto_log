# Generated by Django 4.2.6 on 2023-12-19 09:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_rename_item_quantity_client_id_number_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='itemhistory',
            name='name',
        ),
    ]
