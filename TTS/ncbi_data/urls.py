from django.urls import path
from . import views

urlpatterns = [
    path('', views.ncbi_data_view, name='ncbi_data'),
]