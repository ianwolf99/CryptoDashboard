from django.urls import path
from . import views

urlpatterns = [
    path('plot/', views.plot_cryptos, name='plot_cryptos'),
]
