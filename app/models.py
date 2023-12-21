from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from slugify import slugify
from django.db.models.signals import post_save


# Create your models here.
class Client(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=False, null=True)
    phone_number = models.IntegerField(null=True, blank=True)
    id_number = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Client, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('client_detail', args=[self.slug])

    @classmethod
    def search_by_name(cls, search_term):
        search_result = cls.objects.filter(name__icontains=search_term)
        return search_result


class Item(models.Model):
    lender = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, related_name='items', null=True, on_delete=models.CASCADE)
    item = models.CharField(max_length=50)
    slug = models.SlugField(unique=False, null=True)
    item_quantity = models.IntegerField(null=True, blank=True)
    item_unit_price = models.IntegerField(null=True, blank=True)
    item_total_amount = models.IntegerField(null=True, blank=True)
    item_collection_date = models.DateField(null=True, blank=True)
    is_item_paid = models.BooleanField(default=False)

    def __str__(self):
        return self.item

    def save(self, *args, **kwargs):
        self.slug = slugify(self.item)
        super(Item, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('item_detail', args=[self.slug])

    @classmethod
    def search_by_name(cls, search_term):
        search_result = cls.objects.filter(name__icontains=search_term)
        return search_result


class ItemHistory(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    slug = models.SlugField(unique=False, null=True)
    phone_number = models.IntegerField(null=True, blank=True)
    date_paid = models.DateField(auto_now_add=True)
    item_collection_date = models.DateField(null=True, blank=True)
    item_total_amount = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Copy item_collection_date and item_amount from the client when saving a new record in ItemHistory
        if not self.item:
            self.item = self.item.item
        if not self.slug:
            self.slug = self.item.slug
        if not self.phone_number:
            self.phone_number = self.item.client.phone_number
        if not self.item_collection_date:
            self.item_collection_date = self.item.item_collection_date
        if not self.item_total_amount:
            self.item_total_amount = self.item.item_total_amount
        super(ItemHistory, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.client.name} - Paid on: {self.date_paid}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def save_profile(self):
        self.save()

    def __str__(self):
        return self.user

    @classmethod
    def this_profile(cls):
        profile = cls.objects.all()
        return profile


def Create_profile(sender, **kwargs):
    if kwargs['created']:
        user_profile = Profile.objects.create(user=kwargs['instance'])


post_save.connect(Create_profile, sender=User)
