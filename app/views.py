from django.shortcuts import render, get_object_or_404, HttpResponseRedirect, get_list_or_404, redirect, reverse
from .forms import NewItemForm, NewUserForm, UpdateUnpaidItemsForm, NewClientForm
from django.http import HttpResponseRedirect
from .models import Client, ItemHistory, Profile, User, Item
from django.contrib.humanize.templatetags.humanize import intcomma
from datetime import datetime
from django.db.models import Count, Sum, F, DecimalField
from django.db.models.functions import TruncMonth
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from urllib.parse import unquote  # Import unquote from urllib.parse
from decimal import Decimal
from django.db.models.functions import Coalesce
from django.db import transaction, models
from django.db.models import Q


# Create your views here.
@login_required(login_url='/accounts/login')
def index(request):
    items_by_user = Item.objects.filter(lender_id=request.user)
    total_by_user = sum(client.item_total_amount for client in items_by_user)
    unpaid_clients = Item.objects.filter(lender_id=request.user, is_item_paid=False)
    paid_clients = Item.objects.filter(lender_id=request.user, is_item_paid=True)
    total_paid_balance = sum(client.item_total_amount for client in paid_clients)
    total_unpaid_balance = sum(client.item_total_amount for client in unpaid_clients)
    items_number_by_user = Item.objects.filter(lender_id=request.user).count
    unpaid_items_by_user = Item.objects.filter(lender_id=request.user, is_item_paid=False).count
    paid_items_by_user = Item.objects.filter(lender_id=request.user, is_item_paid=True).count
    total_item_amount = current_month_items_amount(request)
    total_item_amount_users = monthly_item_stats(request)
    today = datetime.now()

    return render(request, "index.html", {'total_unpaid_balance': intcomma(total_unpaid_balance), 'total_by_user': intcomma(total_by_user), 'unpaid_items_by_user': unpaid_items_by_user, 'paid_items_by_user': paid_items_by_user, 'items_number_by_user': items_number_by_user, 'total_item_amount': intcomma(total_item_amount), 'total_paid_balance': intcomma(total_paid_balance), 'total_item_amount_users': total_item_amount_users, 'today': today})


@login_required(login_url='/accounts/login')
def new_client(request):
    if request.method == 'POST':
        form = NewClientForm(request.POST, request.FILES)
        if form.is_valid():
            client = form.save(commit=False)
            client.save()

            # Get the slug from the form details
            client_slug = client.slug  # Replace 'slug' with the actual identifier field

            # Construct the URL for the client_detail view
            client_detail_url = reverse('client_detail', kwargs={'slug': client_slug})

            # Redirect to the client detail page
            return HttpResponseRedirect(client_detail_url)
    else:
        form = NewClientForm()

    return render(request, 'new_client.html', {"form": form})


@login_required(login_url='/accounts/login')
def new_item(request):
    current_user = request.user
    client_id = request.GET.get('client_id')
    client_slug = request.GET.get('client_slug')

    # Retrieve the client based on the provided ID and slug
    client = get_object_or_404(Client, id=client_id, slug=client_slug)

    if request.method == 'POST':
        form = NewItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.lender = current_user
            item.client = client  # Set the client for the new item
            item.save()

            # Construct the URL for the client_detail view
            client_detail_url = reverse('client_detail', kwargs={'slug': client_slug})

            return HttpResponseRedirect(client_detail_url)
    else:
        # Create a form instance with the initial client data
        form = NewItemForm(initial={'client': client})

    return render(request, 'new_item.html', {"form": form, "client": client})


@login_required(login_url='/accounts/login')
def client_list(request):
    clients = Client.objects.all().prefetch_related('item_set')  # Fetch all clients

    total = 0  # Initialize total

    # Iterate over clients and their associated items
    for client in clients:
        # Iterate over items and filter only unpaid items
        unpaid_items = [item for item in client.item_set.all() if not item.is_item_paid]

        # Calculate the total for each client
        client.total_amount = sum(item.item_total_amount for item in unpaid_items)

        # Add the client's total to the overall total
        total += client.total_amount

        # Assign the filtered unpaid_items list back to the client
        client.unpaid_items = unpaid_items

    return render(request, 'client.html', {'clients': clients, 'total': total})


def update_unpaid_items(client, updated_total):
    with transaction.atomic():
        unpaid_items = Item.objects.filter(client=client, is_item_paid=False).order_by('item_collection_date')

        for item in unpaid_items:
            if updated_total > 0:
                if item.item_total_amount <= updated_total:
                    # If the item amount is less than or equal to the remaining amount, deduct the item amount
                    updated_total -= item.item_total_amount
                    item.item_total_amount = Decimal('0')
                    item.is_item_paid = True
                    item.save()
                else:
                    # If the item has more amount than needed, deduct the remaining amount and break
                    item.item_total_amount -= updated_total
                    item.save()
                    break

        # Return the deducted amount
        return updated_total


@login_required(login_url='/accounts/login')
def client_detail(request, slug):
    client = get_object_or_404(Client, slug=slug)
    items = Item.objects.filter(client=client)
    # Calculate the total of unpaid items for the client
    unpaid_items_total = items.filter(is_item_paid=False).aggregate(
        total=Coalesce(Sum('item_total_amount', output_field=DecimalField()), Decimal('0')))['total']
    # history = ItemHistory.objects.filter(name__in=clients.values_list('name', flat=True))
    # all_clients = Client.objects.filter(name__in=clients.values_list('name', flat=True))
    #
    # # Prepare the list of names present in ItemHistory and all Clients with the same name
    # history_names = list(history.values_list('name', flat=True))
    # clients_with_item = list(all_clients.values_list('name', flat=True))
    #
    # # Check if all items are paid for all clients with the same slug
    # all_item_paid = all(item.is_item_paid for item in items)
    #
    # # Calculate the total of unpaid items for the client
    # unpaid_items_total = items.filter(is_item_paid=False).aggregate(
    #     total=Coalesce(Sum('item_total_amount', output_field=DecimalField()), Decimal('0')))['total']
    #
    # form = UpdateUnpaidItemsForm()
    #
    # updated_total = 0
    # new_unpaid_item = Decimal('0')
    #
    # if request.method == 'POST':
    #     # Assuming you have a form with the updated total in the POST data
    #     updated_total = Decimal(request.POST.get('updated_total', '0'))
    #     print(f"Updated Total: {updated_total}")
    #
    #     # Move the loop outside the calculation of unpaid_items_total
    #     for client in clients:
    #         new_unpaid_item = update_unpaid_items(client, updated_total)
    #
    #     # Update the unpaid_items_total after the changes
    #     unpaid_items_total += new_unpaid_item
    #
    # # Format the item_amount fields with commas
    # for item in items:
    #     items.item_total_amount = intcomma(items.item_total_amount)

    return render(request, 'client_detail.html', {'client': client, 'items': items, 'unpaid_items_total': unpaid_items_total})


@login_required(login_url='/accounts/login')
def update_unpaid_items_view(request, slug):
    if request.method == 'POST':
        updated_total = Decimal(request.POST.get('updated_total', '0'))
        print(f"update_unpaid_items_view called with slug: {slug}")
        print(f"Updated Total in POST: {updated_total}")

        client = get_object_or_404(Client, slug=slug)

        unpaid_items_total = Item.objects.filter(client=client, is_item_paid=False).aggregate(
            total=Coalesce(Sum('item_total_amount', output_field=DecimalField()), Decimal('0')))['total']

        new_unpaid_item_amount = update_unpaid_items(client, updated_total)
        unpaid_items_total += new_unpaid_item_amount

    return redirect('client_detail', slug=slug)


@login_required(login_url='/accounts/login')
def update_item(request, pk):
    instance = get_object_or_404(Item, pk=pk)
    form = NewItemForm(request.POST or None, instance=instance)
    if form.is_valid():
        form.save()
        # Get the slug or any other identifier for the newly created client
        update_item_slug = instance.slug  # Replace 'slug' with the actual identifier field

        # Construct the URL for the client_detail view
        client_detail_url = reverse('client_detail', kwargs={'slug': update_item_slug})

        return HttpResponseRedirect(client_detail_url)
    return render(request, 'update_client.html', {'form': form})


@login_required(login_url='/accounts/login')
def search_results(request):
    if 'name' in request.GET and request.GET["name"]:
        search_term = request.GET.get("name")
        searched_clients = Client.objects.filter(Q(name__icontains=search_term) | Q(id_number__icontains=search_term))

        # Create a list to store results along with unpaid items total
        results_with_unpaid = []

        for client in searched_clients:
            items = Item.objects.filter(client=client)

            # Calculate the total of unpaid items for the client
            unpaid_items_total = items.filter(is_item_paid=False).aggregate(
                total=Coalesce(Sum('item_total_amount', output_field=DecimalField()), Decimal('0')))['total']

            # Append the client and total unpaid items to the results list
            results_with_unpaid.append({
                'client': client,
                'unpaid_items_total': unpaid_items_total,
            })

        message = f"{search_term}"
        return render(request, "search.html", {"message": message, "name": searched_clients, "unpaid_items_total": unpaid_items_total, "results_with_unpaid": results_with_unpaid})


def item_paid(request,  pk):
    item = get_object_or_404(Item, pk=pk)

    # Mark the item as paid and save
    item.is_item_paid = True
    item.save()

    # Create item history entry
    ItemHistory.objects.create(item=item)

    # Get the slug of the client for redirection
    item_slug = item.client.slug

    # Construct the URL for the client_detail view
    client_detail_url = reverse('client_detail', kwargs={'slug': item_slug})

    return HttpResponseRedirect(client_detail_url)


def mark_all_items_paid(request, slug):
    # Retrieve the client based on the provided slug
    client = get_object_or_404(Client, slug=slug)

    items = Item.objects.filter(client=client)

    for item in items:
        if not item.is_item_paid:
            item.is_item_paid = True
            item.save()
            # Create item history entry for each item
            ItemHistory.objects.create(item=item)

    # Construct the URL for the client_detail view
    client_detail_url = reverse('client_detail', kwargs={'slug': slug})

    return HttpResponseRedirect(client_detail_url)


@login_required(login_url='/accounts/login')
def profile(request, username):
    user_profile = Profile.objects.filter(user_id=request.user.id)[::-1]
    # Fetch items associated with the current user and include related client information
    lender_list = Item.objects.filter(lender_id=request.user).select_related('client').order_by('item_collection_date')[::-1]

    unpaid_items = Item.objects.filter(lender_id=request.user, is_item_paid=False)
    total_unpaid_balance = sum(item.item_total_amount for item in unpaid_items)
    client = Client.objects.all()

    # Format the item_amount fields with commas
    for item in lender_list:
        item.item_total_amount = intcomma(item.item_total_amount)
    return render(request, "profile.html", {"user_profile": user_profile, "lender_list": lender_list,
                                            "total_unpaid_balance": intcomma(total_unpaid_balance)})


def current_month_items_amount(request):
    # Get the current date
    today = datetime.now()

    # Filter items for the current month
    items_this_month = Item.objects.filter(item_collection_date__month=today.month, item_collection_date__year=today.year)

    # Calculate the sum of item amounts
    total_item_amount_monthly = items_this_month.aggregate(Sum('item_total_amount'))['item_total_amount__sum']

    if total_item_amount_monthly is None:
        total_item_amount_monthly = 0

    return total_item_amount_monthly


def monthly_item_stats(request):
    # Calculate total item balance given monthly
    monthly_item_balance = Item.objects.annotate(year_month=TruncMonth('item_collection_date')).values('year_month').annotate(total_balance=Sum('item_total_amount'))

    # Calculate paid items amount
    paid_items_amount = Item.objects.filter(is_item_paid=True).aggregate(
        total_paid=Sum('item_total_amount')
    )['total_paid']

    # Calculate unpaid items balance
    unpaid_item_balance = Item.objects.filter(is_item_paid=False).aggregate(
        total_unpaid_balance=Sum('item_total_amount')
    )['total_unpaid_balance']

    context = {
        'monthly_item_balance': monthly_item_balance,
        'paid_items_amount': paid_items_amount,
        'unpaid_item_balance': unpaid_item_balance,
    }
    return context


def login_request(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                return redirect("/")
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


def register_request(request):
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful." )
            return redirect("/home")
        messages.error(request, "Unsuccessful registration. Invalid information.")
    form = NewUserForm()
    return render(request, 'registration/register.html', {'form': form})


def logout_request(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect("/")


def registered_users(request):
    users_in_db = User.objects.all()

    user_stats = []

    for user in users_in_db:
        items_given = Item.objects.filter(lender=user)
        total_items_given = sum(item.item_total_amount for item in items_given)
        paid_items = items_given.filter(is_item_paid=True)
        paid_items = sum(item.item_total_amount for item in paid_items)
        unpaid_items = items_given.filter(is_item_paid=False)
        unpaid_items = sum(item.item_total_amount for item in unpaid_items)

        user_stat = {
            'user': user,
            'total_items_given': intcomma(total_items_given),
            'total_paid_items': intcomma(paid_items),
            'total_unpaid_items': intcomma(unpaid_items),
            'user_id': user.id,  # Add the user's ID to the dictionary
        }
        user_stats.append(user_stat)
    return render(request, "users.html", {"users_in_db": users_in_db, 'user_stats': user_stats})


def user_detail(request, id):
    user_info = get_object_or_404(User, id=id)

    items_given = Item.objects.filter(lender=user_info)
    total_items_given = sum(item.item_total_amount for item in items_given)
    total_paid_items = items_given.filter(is_item_paid=True)
    total_paid_amount = sum(item.item_total_amount for item in total_paid_items)
    total_unpaid_items = items_given.filter(is_item_paid=False)
    total_unpaid_amount = sum(item.item_total_amount for item in total_unpaid_items)

    # Annotate items with year and month information
    items_given = items_given.annotate(
        year_month=TruncMonth('item_collection_date')
    )

    # Calculate the count of items given per month
    items_given_monthly = items_given.values('year_month').annotate(count=Count('id'), amount=Sum('item_total_amount'), unpaid=Sum('item_total_amount', filter=F('is_item_paid') == False))
    # You can calculate other variables from the Client model here

    context = {
        'user_info': user_info,
        'total_items_given': intcomma(total_items_given),
        'total_paid_amount': intcomma(total_paid_amount),
        'total_unpaid_amount': intcomma(total_unpaid_amount),
        'items_given_monthly': items_given_monthly,
        # Add other variables you want to display in the template
    }
    return render(request, 'user_detail.html', context)


def delete_item(request, pk):
    item_instance = get_object_or_404(Item, pk=pk)

    # Save the client details for redirecting later
    delete_item_client_slug = item_instance.client.slug

    item_instance.delete()

    # Construct the URL for the client_detail view
    client_detail_url = reverse('client_detail', kwargs={'slug': delete_item_client_slug})

    return HttpResponseRedirect(client_detail_url)
