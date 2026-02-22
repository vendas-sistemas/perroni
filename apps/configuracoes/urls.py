from django.urls import path

from . import views

app_name = 'configuracoes'

urlpatterns = [
    path('', views.configuracoes_home, name='home'),
    path('grupos/', views.group_list, name='group_list'),
    path('grupos/novo/', views.group_create, name='group_create'),
    path('grupos/<int:pk>/editar/', views.group_update, name='group_update'),
    path('grupos/<int:pk>/excluir/', views.group_delete, name='group_delete'),
    path('usuarios/', views.user_list, name='user_list'),
    path('usuarios/novo/', views.user_create, name='user_create'),
    path('usuarios/<int:pk>/editar/', views.user_update, name='user_update'),
]

