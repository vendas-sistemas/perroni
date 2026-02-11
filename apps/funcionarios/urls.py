from django.urls import path
from . import views

app_name = 'funcionarios'

urlpatterns = [
    # Funcionários
    path('', views.funcionario_list, name='funcionario_list'),
    path('<int:pk>/', views.funcionario_detail, name='funcionario_detail'),
    path('criar/', views.funcionario_create, name='funcionario_create'),
    path('<int:pk>/editar/', views.funcionario_update, name='funcionario_update'),
    path('<int:pk>/inativar/', views.funcionario_inativar, name='funcionario_inativar'),
    path('<int:pk>/historico/', views.funcionario_historico, name='funcionario_historico'),

    # Apontamentos
    path('apontamentos/', views.apontamento_list, name='apontamento_list'),
    path('apontamentos/criar/', views.apontamento_create, name='apontamento_create'),
    path('apontamentos/diario/', views.apontamento_diario, name='apontamento_diario'),
    path('apontamentos/<int:pk>/excluir/', views.apontamento_delete, name='apontamento_delete'),

    # Fechamentos
    path('fechamentos/', views.fechamento_list, name='fechamento_list'),
    path('fechamentos/criar/', views.fechamento_create, name='fechamento_create'),
    path('fechamentos/auto/', views.fechamento_auto, name='fechamento_auto'),
    path('fechamentos/semana/<str:data_inicio>/', views.fechamento_semana_detail, name='fechamento_semana_detail'),
    path('fechamentos/<int:pk>/', views.fechamento_detail, name='fechamento_detail'),

    # Visão por obra
    path('obra/<int:pk>/mao-de-obra/', views.obra_mao_de_obra, name='obra_mao_de_obra'),

    # APIs
    path('api/apontamentos/', views.apontamentos_api, name='apontamentos_api'),
    path('api/etapas-por-obra/', views.etapas_por_obra_api, name='etapas_por_obra_api'),
]
