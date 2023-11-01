from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path as url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url("new/client", views.new_client, name="new_client"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
