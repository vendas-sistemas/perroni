from django.urls import path
from . import views

app_name = 'obras'

urlpatterns = [
    path('', views.obra_list, name='obra_list'),
    path('<int:pk>/', views.obra_detail, name='obra_detail'),
    path('criar/', views.obra_create, name='obra_create'),
    path('<int:pk>/editar/', views.obra_update, name='obra_update'),
    path('<int:pk>/etapas/', views.obra_etapas, name='obra_etapas'),
    path('<int:pk>/fotos/', views.obra_fotos, name='obra_fotos'),
    path('<int:pk>/fotos/<int:foto_id>/excluir/', views.obra_foto_delete, name='obra_foto_delete'),
    path('allocacoes/<int:pk>/', views.obra_allocations, name='obra_allocations'),
    path('allocacoes/<int:pk>/csv/', views.obra_allocations_csv, name='obra_allocations_csv'),
    path('etapa/<int:pk>/', views.etapa_detail, name='etapa_detail'),
    path('etapa/<int:pk>/fundacao/', views.etapa1_detail, name='etapa1_detail'),
    path('etapa/<int:pk>/estrutura/', views.etapa2_detail, name='etapa2_detail'),
    path('etapa/<int:pk>/instalacoes/', views.etapa3_detail, name='etapa3_detail'),
    path('etapa/<int:pk>/acabamentos/', views.etapa4_detail, name='etapa4_detail'),
    path('etapa/<int:pk>/finalizacao/', views.etapa5_detail, name='etapa5_detail'),
    path('etapa/<int:pk>/editar/', views.etapa_edit, name='etapa_edit'),
    path('excluidos/', views.obras_trash, name='excluidos'),
    path('<int:pk>/delete/', views.obra_delete, name='obra_delete'),
    path('<int:pk>/restore/', views.obra_restore, name='obra_restore'),
    path('<int:pk>/hard-delete/', views.obra_hard_delete, name='obra_hard_delete'),
]
