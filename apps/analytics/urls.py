from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('rankings/', views.rankings, name='rankings'),
    path('pedreiro/<int:pk>/rendimento/', views.pedreiro_rendimento, name='pedreiro_rendimento'),
    path('obra/<int:pk>/custos/', views.obra_custos, name='obra_custos'),
]
