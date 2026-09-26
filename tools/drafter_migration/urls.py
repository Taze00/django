"""Preview routes only; repository and production URL configuration stay intact."""
from django.urls import include, path
urlpatterns = [path('draft/', include('drafter.urls'))]
