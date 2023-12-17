from django import forms
from django.utils.text import slugify
from .models import Client, Item
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class DateInput(forms.DateInput):
    input_type = 'date'


class NewClientItemForm(forms.Form):
    # Fields for Client model
    client_name = forms.CharField(max_length=50)
    client_phone_number = forms.IntegerField(required=False)
    client_id_number = forms.IntegerField(required=False)

    # Fields for Item model
    item_name = forms.CharField(max_length=50)
    item_quantity = forms.IntegerField(required=False)
    item_unit_price = forms.IntegerField(required=False)
    item_total_amount = forms.IntegerField(required=False)
    item_collection_date = forms.DateField(widget=DateInput(), required=False)

    # Additional fields, if needed

    # custom method to calculate item_total_amount
    def calculate_item_total_amount(self):
        item_quantity = self.cleaned_data.get('item_quantity')
        item_unit_price = self.cleaned_data.get('item_unit_price')
        if item_quantity is not None and item_unit_price is not None:
            return item_quantity * item_unit_price
        return None

    def save(self, current_user):
        # Extract data for Client model
        client_data = {
            'name': self.cleaned_data['client_name'],
            'phone_number': self.cleaned_data['client_phone_number'],
            'id_number': self.cleaned_data['client_id_number'],
        }
        client_instance = Client.objects.create(**client_data)

        # Extract data for Item model
        item_data = {
            'client': client_instance,
            'item': self.cleaned_data['item_name'],
            'item_quantity': self.cleaned_data['item_quantity'],
            'item_unit_price': self.cleaned_data['item_unit_price'],
            'item_total_amount': self.cleaned_data['item_total_amount'],
            'item_collection_date': self.cleaned_data['item_collection_date'],
            # Add other fields as needed
        }
        item_instance = Item.objects.create(lender=current_user, **item_data)

        # You can also perform additional actions or validations here

        return client_instance, item_instance


class NewUserForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super(NewUserForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class UpdateUnpaidItemsForm(forms.Form):
    unpaid_items_total = forms.DecimalField(
        label='Enter Unpaid Amount',
        min_value=0,
        widget=forms.NumberInput(attrs={'step': '0.01'})  # Adjust step as needed
    )
