"""
URL configuration for fiscalizacao_obras project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from config.views import home_redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_redirect, name='home'),
    
    # Apps URLs
    path('obras/', include('apps.obras.urls')),
    path('fiscalizacao/', include('apps.fiscalizacao.urls')),
    path('funcionarios/', include('apps.funcionarios.urls')),
    path('ferramentas/', include('apps.ferramentas.urls')),
    path('clientes/', include('apps.clientes.urls')),
    path('analytics/', include('apps.analytics.urls')),
    path('relatorios/', include('apps.relatorios.urls')),
    
    # Authentication
    path('accounts/', include('django.contrib.auth.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "Fiscalização de Obras - Administração"
admin.site.site_title = "Fiscalização de Obras"
admin.site.index_title = "Painel de Administração"
