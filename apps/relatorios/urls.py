from django.urls import path
from . import views

app_name = 'relatorios'

urlpatterns = [
    # Dashboard principal de relatórios
    path('', views.relatorio_dashboard, name='dashboard'),

    # Exportações
    path('exportar/pdf/', views.exportar_relatorio_pdf, name='exportar_pdf'),
    path('exportar/excel/', views.exportar_relatorio_excel, name='exportar_excel'),
]
