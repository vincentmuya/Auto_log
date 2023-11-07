from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from slugify import slugify
from django.db.models.signals import post_save


# Create your models here.
class Client(models.Model):
    lender = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=False, null=True)
    phone_number = models.IntegerField(null=True, blank=True)
    item = models.CharField(max_length=50)
    item_quantity = models.IntegerField(null=True, blank=True)
    item_unit_price = models.IntegerField(null=True, blank=True)
    item_total_amount = models.IntegerField(null=True, blank=True)
    item_collection_date = models.DateField(null=True, blank=True)
    is_item_paid = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Client, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('client_detail', args=[self.slug])

    @classmethod
    def search_by_name(cls, search_term):
        search_result = cls.objects.filter(name__exact=search_term)
        return search_result


class ItemHistory(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, null=True, blank=True)
    phone_number = models.IntegerField(null=True, blank=True)
    item = models.CharField(max_length=50, null=True, blank=True)
    date_paid = models.DateField(auto_now_add=True)
    item_collection_date = models.DateField(null=True, blank=True)
    item_amount = models.IntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Copy item_collection_date and item_amount from the client when saving a new record in ItemHistory
        if not self.name:
            self.name = self.client.name
        if not self.phone_number:
            self.phone_number = self.client.phone_number
        if not self.item_collection_date:
            self.item_collection_date = self.client.item_collection_date
        if not self.item_amount:
            self.item_amount = self.client.item_amount
        if not self.item:
            self.item = self.client.item
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
