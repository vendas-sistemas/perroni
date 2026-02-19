"""
Script para validar se os cálculos de média estão corretos.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.funcionarios.models import Funcionario, RegistroProducao
from apps.funcionarios.relatorios import RelatorioProducao
from apps.obras.models import Obra, Etapa
from datetime import date
from decimal import Decimal

print("=" * 70)
print("🧪 VALIDAÇÃO DE CÁLCULOS DE MÉDIA")
print("=" * 70)

# Buscar um pedreiro de teste
pedreiro = Funcionario.objects.filter(funcao='pedreiro').first()

if not pedreiro:
    print("❌ Nenhum pedreiro encontrado para teste!")
    print("   Criando um pedreiro de teste...")
    pedreiro = Funcionario.objects.create(
        nome_completo='Teste Validação',
        cpf='999.999.999-99',
        telefone='(99) 99999-9999',
        endereco='Rua Teste',
        cidade='Teste',
        estado='TS',
        cep='99999-999',
        funcao='pedreiro',
        valor_diaria=Decimal('150.00')
    )

print(f"\n📋 Testando com: {pedreiro.nome_completo}")

# Buscar obra e etapa para os testes
obra = Obra.objects.first()
if not obra:
    print("❌ Nenhuma obra encontrada!")
    sys.exit(1)

etapa = Etapa.objects.filter(obra=obra, numero_etapa=1).first()
if not etapa:
    print("❌ Nenhuma etapa encontrada!")
    sys.exit(1)

# Teste 1: Parede 7 Fiadas
print("\n" + "─" * 70)
print("TESTE 1: Parede 7 Fiadas (Blocos)")
print("─" * 70)

# Limpar dados anteriores
RegistroProducao.objects.filter(
    funcionario=pedreiro,
    indicador='parede_7fiadas'
).delete()

# Criar dados de teste
RegistroProducao.objects.create(
    funcionario=pedreiro,
    data=date(2025, 3, 1),
    indicador='parede_7fiadas',
    quantidade=Decimal('200'),
    obra=obra,
    etapa=etapa
)

RegistroProducao.objects.create(
    funcionario=pedreiro,
    data=date(2025, 3, 2),
    indicador='parede_7fiadas',
    quantidade=Decimal('100'),
    obra=obra,
    etapa=etapa
)

print("Dados de entrada:")
print("  Dia 01/03: 200 blocos")
print("  Dia 02/03: 100 blocos")
print("\nCálculo esperado:")
print("  Total: 200 + 100 = 300 blocos")
print("  Dias: 2 dias")
print("  Média: 300 ÷ 2 = 150 blocos/dia")

# Testar ranking
ranking = RelatorioProducao.ranking_indicador(
    'parede_7fiadas',
    date(2025, 3, 1),
    date(2025, 3, 2),
    top=1
)

if ranking:
    item = ranking[0]
    print("\nResultado do sistema:")
    print(f"  Total: {item['total_valor']} blocos")
    print(f"  Dias: {item['total_dias']} dias")
    print(f"  Média: {item['media_dia']} blocos/dia")
    
    # Validar
    if item['media_dia'] == 150.0:
        print("\n✅ TESTE 1 PASSOU! Cálculo correto.")
    else:
        print(f"\n❌ TESTE 1 FALHOU! Esperado: 150.0, Obtido: {item['media_dia']}")
else:
    print("\n❌ TESTE 1 FALHOU! Nenhum ranking retornado.")

# Teste 2: Levantar Alicerce
print("\n" + "─" * 70)
print("TESTE 2: Levantar Alicerce (Percentual)")
print("─" * 70)

# Limpar dados anteriores
RegistroProducao.objects.filter(
    funcionario=pedreiro,
    indicador='alicerce_percentual'
).delete()

# Criar dados de teste
RegistroProducao.objects.create(
    funcionario=pedreiro,
    data=date(2025, 3, 1),
    indicador='alicerce_percentual',
    quantidade=Decimal('10'),
    obra=obra,
    etapa=etapa
)

RegistroProducao.objects.create(
    funcionario=pedreiro,
    data=date(2025, 3, 2),
    indicador='alicerce_percentual',
    quantidade=Decimal('2'),
    obra=obra,
    etapa=etapa
)

print("Dados de entrada:")
print("  Dia 01/03: 10%")
print("  Dia 02/03: 2%")
print("\nCálculo esperado:")
print("  Total: 10 + 2 = 12%")
print("  Dias: 2 dias")
print("  Média: 12 ÷ 2 = 6%/dia")

# Testar ranking
ranking = RelatorioProducao.ranking_indicador(
    'alicerce_percentual',
    date(2025, 3, 1),
    date(2025, 3, 2),
    top=1
)

if ranking:
    item = ranking[0]
    print("\nResultado do sistema:")
    print(f"  Total: {item['total_valor']}%")
    print(f"  Dias: {item['total_dias']} dias")
    print(f"  Média: {item['media_dia']}%/dia")
    
    # Validar
    if item['media_dia'] == 6.0:
        print("\n✅ TESTE 2 PASSOU! Cálculo correto.")
    else:
        print(f"\n❌ TESTE 2 FALHOU! Esperado: 6.0, Obtido: {item['media_dia']}")
else:
    print("\n❌ TESTE 2 FALHOU! Nenhum ranking retornado.")

# Teste 3: Múltiplos dias com valores diferentes
print("\n" + "─" * 70)
print("TESTE 3: Reboco Externo (m²) - 5 dias")
print("─" * 70)

# Limpar dados anteriores
RegistroProducao.objects.filter(
    funcionario=pedreiro,
    indicador='reboco_externo'
).delete()

# Buscar etapa 3
etapa3 = Etapa.objects.filter(obra=obra, numero_etapa=3).first()
if not etapa3:
    etapa3 = etapa

# Criar dados de teste
valores = [25, 30, 28, 32, 35]  # Total: 150, Média: 30
for i, valor in enumerate(valores, 1):
    RegistroProducao.objects.create(
        funcionario=pedreiro,
        data=date(2025, 3, i),
        indicador='reboco_externo',
        quantidade=Decimal(str(valor)),
        obra=obra,
        etapa=etapa3
    )

print("Dados de entrada:")
for i, valor in enumerate(valores, 1):
    print(f"  Dia 0{i}/03: {valor}m²")
print("\nCálculo esperado:")
print(f"  Total: {sum(valores)}m²")
print(f"  Dias: {len(valores)} dias")
print(f"  Média: {sum(valores) / len(valores)}m²/dia")

# Testar ranking
ranking = RelatorioProducao.ranking_indicador(
    'reboco_externo',
    date(2025, 3, 1),
    date(2025, 3, 5),
    top=1
)

if ranking:
    item = ranking[0]
    print("\nResultado do sistema:")
    print(f"  Total: {item['total_valor']}m²")
    print(f"  Dias: {item['total_dias']} dias")
    print(f"  Média: {item['media_dia']}m²/dia")
    
    # Validar
    if item['media_dia'] == 30.0:
        print("\n✅ TESTE 3 PASSOU! Cálculo correto.")
    else:
        print(f"\n❌ TESTE 3 FALHOU! Esperado: 30.0, Obtido: {item['media_dia']}")
else:
    print("\n❌ TESTE 3 FALHOU! Nenhum ranking retornado.")

# Limpar dados de teste
print("\n" + "─" * 70)
print("🧹 Limpando dados de teste...")
RegistroProducao.objects.filter(
    funcionario=pedreiro,
    data__range=[date(2025, 3, 1), date(2025, 3, 5)]
).delete()
print("✓ Dados de teste removidos.")

print("\n" + "=" * 70)
print("🏁 VALIDAÇÃO CONCLUÍDA")
print("=" * 70)
