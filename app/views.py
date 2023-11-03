from django.shortcuts import render, get_object_or_404, HttpResponse, get_list_or_404, redirect
from .forms import NewClientForm, NewUserForm
from django.http import HttpResponseRedirect
from .models import Client, ItemHistory, Profile, User
from django.contrib.humanize.templatetags.humanize import intcomma
from datetime import datetime
from django.db.models import Count, Sum, F
from django.db.models.functions import TruncMonth
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required


# Create your views here.
@login_required(login_url='/accounts/login')
def index(request):
    items_by_user = Client.objects.filter(lender_id=request.user)
    total_by_user = sum(client.item_amount for client in items_by_user)
    unpaid_clients = Client.objects.filter(lender_id=request.user, is_item_paid=False)
    paid_clients = Client.objects.filter(lender_id=request.user, is_item_paid=True)
    total_paid_balance = sum(client.item_amount for client in paid_clients)
    total_unpaid_balance = sum(client.item_amount for client in unpaid_clients)
    items_number_by_user = Client.objects.filter(lender_id=request.user).count
    unpaid_items_by_user = Client.objects.filter(lender_id=request.user, is_item_paid=False).count
    paid_items_by_user = Client.objects.filter(lender_id=request.user, is_item_paid=True).count
    total_item_amount = current_month_items_amount(request)
    total_item_amount_users = monthly_item_stats(request)

    return render(request, "index.html", {'total_unpaid_balance': intcomma(total_unpaid_balance), 'total_by_user': intcomma(total_by_user), 'unpaid_items_by_user': unpaid_items_by_user, 'paid_items_by_user': paid_items_by_user, 'items_number_by_user': items_number_by_user, 'total_item_amount': intcomma(total_item_amount), 'total_paid_balance': intcomma(total_paid_balance), 'total_item_amount_users': total_item_amount_users})


@login_required(login_url='/accounts/login')
def new_client(request):
    current_user = request.user
    if request.method == 'POST':
        form = NewClientForm(request.POST, request.FILES)
        if form.is_valid():
            client = form.save(commit=False)
            client.lender = current_user
            client.save()
            return HttpResponseRedirect('/')
    else:
        form = NewClientForm()

    return render(request, 'new_client.html', {"form": form})


@login_required(login_url='/accounts/login')
def client_list(request):
    client = Client.objects.filter(is_item_paid=False)[::-1]
    total = sum(client_obj.item_amount for client_obj in client)
    for clients in client:
        clients.item_amount = intcomma(clients.item_amount)
    return render(request, 'client.html', {'client': client, 'total': total})


@login_required(login_url='/accounts/login')
def client_detail(request, slug, ):
    client = get_object_or_404(Client, slug=slug)
    history = ItemHistory.objects.filter(name=client.name)  # Get item history for the client's name
    all_clients = Client.objects.filter(name=client.name)   # Get all clients with the same name

    # Prepare the list of names present in ItemHistory and all Clients with the same name
    history_names = list(history.values_list('name', flat=True))
    clients_with_item = list(all_clients.values_list('name', flat=True))

    # Check if all items are paid for the client's name
    all_item_paid = client.is_item_paid and all(client.is_item_paid for client in all_clients)

    # Format the item_amount fields with commas
    for client in all_clients:
        client.item_amount = intcomma(client.item_amount)

    for clients in history:
        clients.item_amount = intcomma(clients.item_amount)
    return render(request, 'client_detail.html', {'client': client, 'history': history,
                                                  'history_names': history_names, 'clients_with_item': clients_with_item, 'all_item_paid': all_item_paid})


@login_required(login_url='/accounts/login')
def update_client(request, pk):
    instance = get_object_or_404(Client, pk=pk)
    form = NewClientForm(request.POST or None, instance=instance)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect('/')
    return render(request, 'update_client.html', {'form': form})


@login_required(login_url='/accounts/login')
def search_results(request):
    if 'name' in request.GET and request.GET["name"]:
        search_term = request.GET.get("name")
        searched_ref = Client.search_by_name(search_term)
        message = f"{search_term}"
        return render(request, "search.html", {"message": message, "name": searched_ref})


def item_paid(request,  slug):
    client = get_list_or_404(Client, slug=slug)
    if len(client) > 1:
        # If multiple clients found, choose the first one and save it
        client = client[0]
    else:
        # If only one client found, use that client for item payment
        client = client[0]

    # Mark the item as paid and save
    client.is_item_paid = True
    client.save()

    # Create item history entry
    ItemHistory.objects.create(client=client)

    return HttpResponse("item Paid Successfully!")


@login_required(login_url='/accounts/login')
def profile(request, username):
    user_profile = Profile.objects.filter(user_id=request.user.id)[::-1]
    lender_list = Client.objects.filter(lender_id=request.user).order_by('item_collection_date')[::-1]
    unpaid_clients = Client.objects.filter(lender_id=request.user, is_item_paid=False)
    total_unpaid_balance = sum(client.item_amount for client in unpaid_clients)
    client = Client.objects.all()

    # Format the item_amount fields with commas
    for client in lender_list:
        client.item_amount = intcomma(client.item_amount)
    return render(request, "profile.html", {"user_profile": user_profile, "lender_list": lender_list,
                                            "total_unpaid_balance": intcomma(total_unpaid_balance)})


def current_month_items_amount(request):
    # Get the current date
    today = datetime.now()

    # Filter items for the current month
    items_this_month = Client.objects.filter(item_collection_date__month=today.month, item_collection_date__year=today.year)

    # Calculate the sum of item amounts
    total_item_amount_monthly = items_this_month.aggregate(Sum('item_amount'))['item_amount__sum']

    if total_item_amount_monthly is None:
        total_item_amount_monthly = 0

    return total_item_amount_monthly


def monthly_item_stats(request):
    # Calculate total item balance given monthly
    monthly_item_balance = Client.objects.annotate(
        year_month=TruncMonth('item_collection_date')
    ).values('year_month').annotate(
        total_balance=Sum('item_amount')
    )

    # Calculate paid items amount
    paid_items_amount = Client.objects.filter(is_item_paid=True).aggregate(
        total_paid=Sum('item_amount')
    )['total_paid']

    # Calculate unpaid items balance
    unpaid_item_balance = Client.objects.filter(is_item_paid=False).aggregate(
        total_unpaid_balance=Sum('item_amount')
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
        items_given = Client.objects.filter(lender=user)
        total_items_given = sum(client.item_amount for client in items_given)
        paid_items = items_given.filter(is_item_paid=True)
        paid_items = sum(client.item_amount for client in paid_items)
        unpaid_items = items_given.filter(is_item_paid=False)
        unpaid_items = sum(client.item_amount for client in unpaid_items)

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

    items_given = Client.objects.filter(lender=user_info)
    total_items_given = sum(client.item_amount for client in items_given)
    total_paid_items = items_given.filter(is_item_paid=True)
    total_paid_amount = sum(client.item_amount for client in total_paid_items)
    total_unpaid_items = items_given.filter(is_item_paid=False)
    total_unpaid_amount = sum(client.item_amount for client in total_unpaid_items)

    # Annotate items with year and month information
    items_given = items_given.annotate(
        year_month=TruncMonth('item_collection_date')
    )

    # Calculate the count of items given per month
    items_given_monthly = items_given.values('year_month').annotate(count=Count('id'), amount=Sum('item_amount'), unpaid=Sum('item_amount', filter=F('is_item_paid') == False))
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
