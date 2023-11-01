from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from slugify import slugify


# Create your models here.
class Client(models.Model):
    lender = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=False, null=True)
    phone_number = models.IntegerField(null=True, blank=True)
    item = models.CharField(max_length=50)
    item_amount = models.IntegerField(null=True, blank=True)
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
