from django.shortcuts import render, get_object_or_404, HttpResponse, get_list_or_404
from .forms import NewClientForm
from django.http import HttpResponseRedirect
from .models import Client, ItemHistory, Profile
from django.contrib.humanize.templatetags.humanize import intcomma
from datetime import datetime
from django.db.models import Count, Sum, F
from django.db.models.functions import TruncMonth


# Create your views here.
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


def new_client(request):
    current_user = request.user
    if request.method == 'POST':
        form = NewClientForm(request.POST, request.FILES)
        if form.is_valid():
            client = form.save(commit=False)
            client.save()
            return HttpResponseRedirect('/')
    else:
        form = NewClientForm()

    return render(request, 'new_client.html', {"form": form})


def client_list(request):
    client = Client.objects.filter(is_item_paid=False)[::-1]
    for clients in client:
        clients.item_amount = intcomma(clients.item_amount)
    return render(request, 'client.html', {'client': client})


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


def update_client(request, pk):
    instance = get_object_or_404(Client, pk=pk)
    form = NewClientForm(request.POST or None, instance=instance)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect('/')
    return render(request, 'update_client.html', {'form': form})


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
