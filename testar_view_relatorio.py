#!/usr/bin/env python
"""Testar a view relatorio_dashboard"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

print("=" * 70)
print("TESTANDO VIEW: relatorio_dashboard")
print("=" * 70)

client = Client()
User = get_user_model()
user = User.objects.first()
client.force_login(user)

# Testar sem filtros
url = '/relatorios/'
print(f"\n📡 Acessando: {url} (sem filtros)")
response = client.get(url)

print(f"Status: {response.status_code}")

if response.status_code == 200:
    content = response.content.decode()
    
    # Verificar Etapa 2
    print("\n" + "=" * 70)
    print("VERIFICANDO ETAPA 2 NO HTML:")
    print("=" * 70)
    
    checks = [
        ('Etapa 2', 'Título da Etapa 2'),
        ('Estrutura', 'Subtítulo Estrutura'),
        ('Platibanda', 'Indicador Platibanda'),
        ('Respaldo', 'Indicador Respaldo'),
        ('Laje', 'Indicador Laje'),
        ('Cobertura', 'Indicador Cobertura'),
    ]
    
    for texto, descricao in checks:
        if texto in content:
            print(f"  ✅ {descricao}")
        else:
            print(f"  ❌ {descricao} NÃO ENCONTRADO")
    
    # Contar ocorrências
    print("\n" + "=" * 70)
    print("CONTAGEM DE INDICADORES NO HTML:")
    print("=" * 70)
    
    # Procurar por padrões específicos
    etapa2_count = content.count('Etapa 2')
    platibanda_count = content.count('Platibanda')
    respaldo_count = content.count('Respaldo')
    laje_count = content.count('Laje')
    cobertura_count = content.count('Cobertura')
    
    print(f"  'Etapa 2': {etapa2_count} ocorrências")
    print(f"  'Platibanda': {platibanda_count} ocorrências")
    print(f"  'Respaldo': {respaldo_count} ocorrências")
    print(f"  'Laje': {laje_count} ocorrências")
    print(f"  'Cobertura': {cobertura_count} ocorrências")
    
    # Verificar context
    print("\n" + "=" * 70)
    print("VERIFICANDO CONTEXT DA VIEW:")
    print("=" * 70)
    
    etapas = response.context.get('ranking_por_etapas', [])
    print(f"Total de etapas no context: {len(etapas)}")
    
    for etapa in etapas:
        if etapa['numero'] == 2:
            print(f"\n✅ Etapa 2 encontrada no context:")
            print(f"   Nome: {etapa['nome']}")
            print(f"   Indicadores: {len(etapa['indicadores'])}")
            
            for ind in etapa['indicadores']:
                print(f"      - {ind['nome']}")

else:
    print(f"❌ Erro: Status {response.status_code}")

print("\n" + "=" * 70)
