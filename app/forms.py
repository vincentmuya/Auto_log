from django import forms
from .models import Client
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class DateInput(forms.DateInput):
    input_type = 'date'


class NewClientForm(forms.ModelForm):

    class Meta:
        model = Client
        exclude = ["slug", "lender", "is_item_paid"]
        widgets = {
            'item_collection_date': DateInput(),
        }

    # custom method to calculate item_total_amount
    def calculate_item_total_amount(self):
        item_quantity = self.cleaned_data.get('item_quantity')
        item_unit_price = self.cleaned_data.get('item_unit_price')
        if item_quantity is not None and item_unit_price is not None:
            return item_quantity * item_unit_price
        return None


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
