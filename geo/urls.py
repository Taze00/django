from django.urls import path, re_path, include
from . import views

urlpatterns = [
    path('api/', include('geo.api_urls')),
    re_path(r'^.*$', views.geo_page, name='geo_catch_all'),
]
