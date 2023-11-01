from django.shortcuts import render
from .forms import NewClientForm
from django.http import HttpResponseRedirect
from .models import Client


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
    return render(request, 'client.html', {'client': client})
