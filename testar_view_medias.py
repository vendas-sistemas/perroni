#!/usr/bin/env python
"""Testar a view funcionario_medias_individuais"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

print("=" * 70)
print("TESTANDO VIEW: funcionario_medias_individuais")
print("=" * 70)

# Criar cliente e fazer login
client = Client()
User = get_user_model()
user = User.objects.first()

if not user:
    print("❌ Nenhum usuário encontrado!")
    sys.exit(1)

client.force_login(user)
print(f"\n✅ Logado como: {user.username}")

# Testar a URL
url = '/funcionarios/1/medias/'
print(f"\n📡 Acessando: {url}")

try:
    response = client.get(url)
    print(f"✅ Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Página carregou com sucesso!")
        
        # Verificar se há conteúdo esperado
        content = response.content.decode()
        
        checks = [
            ('Eduardo', 'Nome do funcionário'),
            ('Médias', 'Título da página'),
            ('ETAPA', 'Seções de etapas'),
            ('total_dias_trabalhados', 'Dados de produção'),
        ]
        
        print("\n📋 Verificações de conteúdo:")
        for texto, descricao in checks:
            if texto in content:
                print(f"  ✅ {descricao}: encontrado")
            else:
                print(f"  ⚠️ {descricao}: não encontrado")
                
    elif response.status_code == 404:
        print("❌ Página não encontrada (404)")
    elif response.status_code == 500:
        print("❌ Erro no servidor (500)")
        print(f"Erro: {response.content.decode()[:500]}")
    else:
        print(f"⚠️ Status inesperado: {response.status_code}")
        
except Exception as e:
    print(f"❌ ERRO: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("✅ TESTE CONCLUÍDO")
print("=" * 70)
