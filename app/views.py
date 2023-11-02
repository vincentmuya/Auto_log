from django.shortcuts import render, get_object_or_404, HttpResponse, get_list_or_404
from .forms import NewClientForm
from django.http import HttpResponseRedirect
from .models import Client, ItemHistory
from django.contrib.humanize.templatetags.humanize import intcomma


# Create your views here.
def index(request):

    return render(request, "index.html")


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
    return render(request, 'client_detail.html', {'client': client, 'history': history, 'history_names': history_names, 'clients_with_item': clients_with_item, 'all_item_paid': all_item_paid})


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
