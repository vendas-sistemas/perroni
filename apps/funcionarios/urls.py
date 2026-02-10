from django.urls import path
from . import views

app_name = 'funcionarios'

urlpatterns = [
    path('', views.funcionario_list, name='funcionario_list'),
    path('<int:pk>/', views.funcionario_detail, name='funcionario_detail'),
    path('criar/', views.funcionario_create, name='funcionario_create'),
    path('<int:pk>/editar/', views.funcionario_update, name='funcionario_update'),
    path('<int:pk>/inativar/', views.funcionario_inativar, name='funcionario_inativar'),
    path('apontamentos/', views.apontamento_list, name='apontamento_list'),
    path('apontamentos/criar/', views.apontamento_create, name='apontamento_create'),
    path('fechamentos/', views.fechamento_list, name='fechamento_list'),
]
