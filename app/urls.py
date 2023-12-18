from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path as url
from . import views
from .views import update_unpaid_items_view


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url("new/client", views.new_client, name="new_client"),
    url("new/item", views.new_item, name="new_item"),
    url("client_list", views.client_list, name="client_list"),
    url(r'^(?P<slug>[-\w]+)/update_unpaid_items/$', update_unpaid_items_view, name='update_unpaid_items'),
    url(r'^(?P<slug>[-\w]+)/$', views.client_detail, name='client_detail'),
    url(r'^update/client/(?P<pk>\d+)/$', views.update_client, name='update-client'),
    url(r'^search$', views.search_results, name='search_results'),
    url('item_paid/(?P<slug>[-\w]+)/$', views.item_paid, name='item_paid'),
    url(r'^profile/(?P<username>[\w\-]+)/$', views.profile, name='profile'),
    url("login", views.login_request, name="login"),
    url("register", views.register_request, name="register"),
    url("users", views.registered_users, name="registered_users"),
    url(r'^user/(?P<id>\d+)/$', views.user_detail, name='user_detail'),
    url("logout", views.logout_request, name="logout"),
    url('mark_all_items_paid/(?P<slug>[-\w]+)/$', views.mark_all_items_paid, name='mark_all_items_paid'),
    url(r'^delete/client/(?P<pk>\d+)/$', views.delete_client, name='delete_client'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
