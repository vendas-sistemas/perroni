from django.urls import path
from . import views

app_name = 'ferramentas'

urlpatterns = [
    path('', views.ferramenta_list, name='ferramenta_list'),
    path('<int:pk>/', views.ferramenta_detail, name='ferramenta_detail'),
    path('<int:pk>/editar/', views.ferramenta_update, name='ferramenta_update'),
    path('criar/', views.ferramenta_create, name='ferramenta_create'),
    path('movimentar/', views.movimentacao_create, name='movimentacao_create'),
    path('movimentar/criar/', views.MovimentacaoCreateView.as_view(), name='movimentacao_create_cbv'),
    
    # Conferências - ORDEM IMPORTANTE!
    path('conferencia/', views.conferencia_list, name='conferencia_list'),
    path('conferencia/criar/', views.conferencia_create, name='conferencia_create'),
    path('conferencia/<int:pk>/', views.conferencia_detail, name='conferencia_detail'),
    path('conferencia/<int:pk>/conferir/', views.conferencia_conferir, name='conferencia_conferir'),  # NOVA ROTA
    
    # Alternativas antigas (manter por compatibilidade)
    path('conferencia/criar-cbv/', views.ConferenciaCreateView.as_view(), name='conferencia_create_cbv'),
    path('conferencia/criar-multi/', views.ConferenciaWithItemsCreateView.as_view(), name='conferencia_create_multi'),
    path('conferencia/<int:conferencia_pk>/itens/criar/', views.ConferenciaItemsManageView.as_view(), name='itemconferencia_create'),
]
