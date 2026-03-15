from django.urls import path

from . import views

app_name = 'fornecedores'

urlpatterns = [
    path('', views.fornecedor_list, name='fornecedor_list'),
    path('criar/', views.fornecedor_create, name='fornecedor_create'),
    path('<int:pk>/', views.fornecedor_detail, name='fornecedor_detail'),
    path('<int:pk>/editar/', views.fornecedor_update, name='fornecedor_update'),
]

