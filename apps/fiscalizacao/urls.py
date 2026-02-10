from django.urls import path
from . import views

app_name = 'fiscalizacao'

urlpatterns = [
    path('', views.fiscalizacao_list, name='fiscalizacao_list'),
    path('criar/', views.fiscalizacao_create, name='fiscalizacao_create'),
    path('<int:pk>/', views.fiscalizacao_detail, name='fiscalizacao_detail'),
    # edit view removed for safety; editing is not available from the UI
]
