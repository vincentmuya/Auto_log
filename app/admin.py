from django.contrib import admin
from .models import Client, ItemHistory

# Register your models here.
admin.site.register(Client)
admin.site.register(ItemHistory)
