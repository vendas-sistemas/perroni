#!/usr/bin/env python
"""
Script para gerar ferramentas com dados aleatórios.
Uso: python gerar_ferramentas.py
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.ferramentas.models import Ferramenta
from apps.obras.models import Obra


# Tipos de ferramentas
NOMES_FERRAMENTAS = {
    'manual': [
        'Martelo', 'Chave de Fenda', 'Alicate', 'Serrote', 'Machado', 'Pé de Cabra',
        'Chave Inglesa', 'Chave de Boca', 'Chave Phillips', 'Chave Estrela',
        'Escova de Aço', 'Raspadeira', 'Espaçador', 'Nível', 'Trena', 'Prumo',
    ],
    'eletrica': [
        'Furadeira', 'Parafusadeira', 'Serra Circular', 'Serra de Copo', 'Lixadeira',
        'Esmerilhadeira', 'Compressor', 'Pistola de Pregos', 'Martelete', 'Polidora',
        'Cortadora de Azulejo', 'Tupia', 'Plaina Elétrica', 'Tico-Tico', 'Jogo de Brocas',
    ],
    'medicao': [
        'Trena de 5m', 'Trena de 10m', 'Nível de Bolha', 'Nível Digital', 'Prumo de Aço',
        'Esquadro', 'Transferidor', 'Paquímetro', 'Micrômetro', 'Medidor de Energia',
    ],
    'seguranca': [
        'Capacete', 'Colete de Segurança', 'Luva de Proteção', 'Máscara Respiratória',
        'Óculos de Proteção', 'Protetor Auricular', 'Macacão', 'Bota de Segurança',
        'Cinto de Segurança', 'Corda de Segurança', 'Colchão de Queda',
    ],
    'outros': [
        'Escada de Alumínio', 'Andaime', 'Suporte Articulado', 'Manta de Proteção',
        'Caixa de Ferramentas', 'Corrente', 'Cabo de Aço', 'Roda', 'Cadeado',
    ],
}

STATUS_CHOICES = ['deposito', 'em_obra', 'manutencao', 'perdida', 'descartada']


def gerar_codigo_ferramenta():
    """Gera um código único para ferramenta."""
    prefixo = random.choice(['FRR', 'TLS', 'SEG', 'MED', 'OTR'])
    numero = random.randint(10000, 99999)
    return f"{prefixo}-{numero}"


def gerar_ferramentas(quantidade):
    """Cria N ferramentas com dados aleatórios."""
    criados = 0
    erros = 0
    obras = list(Obra.objects.filter(ativo=True))
    codigos_existentes = set(Ferramenta.objects.values_list('codigo', flat=True))
    
    print(f"\n{'='*60}")
    print(f"🔧 Gerando {quantidade} ferramentas...")
    print(f"{'='*60}\n")
    
    for i in range(quantidade):
        try:
            # Gera código único até 10 tentativas
            tentativas = 0
            while tentativas < 10:
                codigo = gerar_codigo_ferramenta()
                if codigo not in codigos_existentes:
                    break
                tentativas += 1
            
            if codigo in codigos_existentes:
                print(f"  ❌ [{i+1}/{quantidade}] Código único não gerado. Pulando...")
                erros += 1
                continue
            
            categoria = random.choice(list(NOMES_FERRAMENTAS.keys()))
            nome = random.choice(NOMES_FERRAMENTAS[categoria])
            status = random.choice(STATUS_CHOICES)
            
            # Se status for 'em_obra', associa a uma obra aleatória
            obra_atual = None
            if status == 'em_obra' and obras:
                obra_atual = random.choice(obras)
            
            # Dados adicionais
            descricao = f"Ferramenta {categoria} de qualidade"
            data_aquisicao = datetime.now().date() - timedelta(days=random.randint(1, 720))
            valor_aquisicao = Decimal(str(random.uniform(15.00, 2500.00))).quantize(Decimal('0.01'))
            
            ferramenta = Ferramenta.objects.create(
                codigo=codigo,
                nome=nome,
                categoria=categoria,
                descricao=descricao,
                status=status,
                obra_atual=obra_atual,
                data_aquisicao=data_aquisicao,
                valor_aquisicao=valor_aquisicao,
                ativo=True,
            )
            
            codigos_existentes.add(codigo)
            criados += 1
            print(f"  ✅ [{i+1}/{quantidade}] {ferramenta.codigo} - {ferramenta.nome}")
            
        except Exception as e:
            erros += 1
            print(f"  ❌ [{i+1}/{quantidade}] Erro ao criar ferramenta: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 Resultado: {criados} criadas, {erros} erros")
    print(f"{'='*60}\n")


def main():
    try:
        quantidade = input("Quantas ferramentas deseja criar? ").strip()
        
        if not quantidade.isdigit():
            print("❌ Favor informar um número inteiro válido.")
            sys.exit(1)
        
        quantidade = int(quantidade)
        if quantidade <= 0:
            print("❌ A quantidade deve ser maior que 0.")
            sys.exit(1)
        
        gerar_ferramentas(quantidade)
        
    except KeyboardInterrupt:
        print("\n\n⏸️  Operação cancelada pelo usuário.")
        sys.exit(0)


if __name__ == '__main__':
    main()
