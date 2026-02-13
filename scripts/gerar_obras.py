#!/usr/bin/env python
"""
Script para gerar obras com dados aleatórios.
Uso: python gerar_obras.py
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.obras.models import Obra
from apps.clientes.models import Cliente


# Tipos de imóveis
TIPOS_IMOVEIS = [
    'Casa', 'Residência', 'Apartamento', 'Edifício', 'Comercial', 'Galpão',
    'Sobrado', 'Condomínio', 'Empreendimento', 'Reforma',
]

# Locais/bairros
BAIRROS = [
    'Centro', 'Liberdade', 'Vila Mariana', 'Pinheiros', 'Jardins', 'Tatuapé',
    'Morumbi', 'Vila Madalena', 'Consolação', 'Santa Cecília', 'Alto da Lapa',
    'Bom Retiro', 'Saúde', 'Aclimação', 'Vila Sônia', 'Itaim Bibi', 'Perdizes',
]

# Endereços
RUAS = [
    'Rua', 'Avenida', 'Alameda', 'Travessa', 'Largo',
]

# Sufixos para nomes de obras
SUFIXOS = [
    'Residencial', 'Empreendimento', 'Condomínio', 'Loteamento', 'Projeto',
]


def gerar_nome_obra():
    """Gera um nome para a obra."""
    tipo = random.choice(TIPOS_IMOVEIS)
    sufixo = random.choice(SUFIXOS)
    numero = random.randint(1, 999)
    return f"{tipo} {sufixo} {numero}"


def gerar_endereco():
    """Gera um endereço aleatório."""
    rua = random.choice(RUAS)
    nome_rua = f"do {random.choice(BAIRROS)}" if random.choice([True, False]) else f"{random.choice(BAIRROS)}"
    numero = random.randint(1, 9999)
    bairro = random.choice(BAIRROS)
    cep_1 = random.randint(1000, 9999)
    cep_2 = random.randint(100, 999)
    return f"{rua} {nome_rua}, {numero} - {bairro}, São Paulo - SP, {cep_1:04d}-{cep_2:03d}"


def gerar_datas():
    """Gera datas de início e previsão de término."""
    hoje = datetime.now().date()
    # Data de início entre 60 dias atrás e 30 dias no futuro
    data_inicio = hoje + timedelta(days=random.randint(-60, 30))
    # Previsão de término entre 30 e 360 dias após o início
    dias_duracao = random.randint(30, 360)
    data_fim = data_inicio + timedelta(days=dias_duracao)
    return data_inicio, data_fim


def gerar_obras(quantidade):
    """Cria N obras com dados aleatórios."""
    criados = 0
    erros = 0
    clientes = list(Cliente.objects.filter(ativo=True))
    
    if not clientes:
        print("⚠️  Nenhum cliente ativo encontrado. Crie clientes primeiro com 'gerar_clientes.py'")
        print("   Continuando com obras sem cliente associado...\n")
    
    print(f"\n{'='*60}")
    print(f"🏗️  Gerando {quantidade} obras...")
    print(f"{'='*60}\n")
    
    for i in range(quantidade):
        try:
            nome = gerar_nome_obra()
            endereco = gerar_endereco()
            data_inicio, data_previsao = gerar_datas()
            status = random.choice(['planejamento', 'em_andamento', 'concluida'])
            cliente = random.choice(clientes) if clientes else None
            
            obra = Obra.objects.create(
                nome=nome,
                endereco=endereco,
                cliente=cliente,
                data_inicio=data_inicio,
                data_previsao_termino=data_previsao,
                status=status,
                ativo=True,
            )
            
            criados += 1
            cliente_str = f" ({cliente.nome})" if cliente else ""
            print(f"  ✅ [{i+1}/{quantidade}] {obra.nome}{cliente_str}")
            
        except Exception as e:
            erros += 1
            print(f"  ❌ [{i+1}/{quantidade}] Erro ao criar obra: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 Resultado: {criados} criadas, {erros} erros")
    print(f"{'='*60}\n")


def main():
    try:
        quantidade = input("Quantas obras deseja criar? ").strip()
        
        if not quantidade.isdigit():
            print("❌ Favor informar um número inteiro válido.")
            sys.exit(1)
        
        quantidade = int(quantidade)
        if quantidade <= 0:
            print("❌ A quantidade deve ser maior que 0.")
            sys.exit(1)
        
        gerar_obras(quantidade)
        
    except KeyboardInterrupt:
        print("\n\n⏸️  Operação cancelada pelo usuário.")
        sys.exit(0)


if __name__ == '__main__':
    main()
