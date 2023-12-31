# Generated by Django 4.2.6 on 2023-11-01 08:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('slug', models.SlugField(null=True)),
                ('phone_number', models.IntegerField(blank=True, null=True)),
                ('item', models.CharField(max_length=50)),
                ('item_amount', models.IntegerField(blank=True, null=True)),
                ('item_collection_date', models.DateField(blank=True, null=True)),
                ('is_item_paid', models.BooleanField(default=False)),
                ('lender', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
