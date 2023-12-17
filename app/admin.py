from django.contrib import admin
from .models import Client, ItemHistory, Item

# Register your models here.
admin.site.register(Client)
admin.site.register(ItemHistory)
admin.site.register(Item)
