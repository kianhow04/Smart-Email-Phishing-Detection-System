from django.urls import path
from . import views

app_name = 'detector'

urlpatterns = [
    # The empty string '' means this will be the homepage
    path('', views.scanner_view, name='scanner'),
]
