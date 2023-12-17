# Generated by Django 4.2.6 on 2023-12-17 11:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app', '0006_itemhistory_slug'),
    ]

    operations = [
        migrations.RenameField(
            model_name='client',
            old_name='item_quantity',
            new_name='id_number',
        ),
        migrations.RemoveField(
            model_name='client',
            name='is_item_paid',
        ),
        migrations.RemoveField(
            model_name='client',
            name='item',
        ),
        migrations.RemoveField(
            model_name='client',
            name='item_collection_date',
        ),
        migrations.RemoveField(
            model_name='client',
            name='item_total_amount',
        ),
        migrations.RemoveField(
            model_name='client',
            name='item_unit_price',
        ),
        migrations.RemoveField(
            model_name='client',
            name='lender',
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item', models.CharField(max_length=50)),
                ('slug', models.SlugField(null=True)),
                ('item_quantity', models.IntegerField(blank=True, null=True)),
                ('item_unit_price', models.IntegerField(blank=True, null=True)),
                ('item_total_amount', models.IntegerField(blank=True, null=True)),
                ('item_collection_date', models.DateField(blank=True, null=True)),
                ('is_item_paid', models.BooleanField(default=False)),
                ('client', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='app.client')),
                ('lender', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterField(
            model_name='itemhistory',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.item'),
        ),
    ]
