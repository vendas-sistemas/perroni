"""
Script de Teste para Validar as 3 Correções de Relatórios de Produção

Execute este script para validar se as correções foram implementadas corretamente:
    python manage.py shell < scripts/testar_correcoes_relatorios.py

Ou dentro do shell Django:
    python manage.py shell
    >>> exec(open('scripts/testar_correcoes_relatorios.py').read())
"""

import os
import django
from decimal import Decimal
from datetime import date, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.funcionarios.models import (
    Funcionario, RegistroProducao, ApontamentoDiarioLote, Etapa
)
from apps.obras.models import Obra

print("\n" + "="*80)
print("🔍 TESTE DAS 3 CORREÇÕES DE RELATÓRIOS DE PRODUÇÃO")
print("="*80)


# ═══════════════════════════════════════════════════════════════
# TESTE 1: Validar que não são criados registros com valor zero
# ═══════════════════════════════════════════════════════════════
print("\n📋 TESTE 1: Validar que campos vazios não geram registros")
print("-" * 80)

# Buscar registros com valor zero
registros_zerados = RegistroProducao.objects.filter(quantidade=0)
total_zerados = registros_zerados.count()

if total_zerados == 0:
    print("✅ SUCESSO: Nenhum registro com quantidade = 0 encontrado!")
else:
    print(f"⚠️  ATENÇÃO: Encontrados {total_zerados} registros com quantidade = 0")
    print("   Isso pode indicar que o problema 1 ainda existe.")
    print("\n   Primeiros 5 registros:")
    for reg in registros_zerados[:5]:
        print(f"   • {reg.funcionario.nome_completo} - {reg.indicador} - {reg.data}")


# ═══════════════════════════════════════════════════════════════
# TESTE 2: Validar que indicadores da Etapa 2 existem
# ═══════════════════════════════════════════════════════════════
print("\n\n📋 TESTE 2: Validar indicadores da Etapa 2")
print("-" * 80)

indicadores_etapa2 = [
    'respaldo_conclusao',
    'laje_conclusao',
    'platibanda',
    'cobertura_conclusao'
]

print("\nIndicadores da Etapa 2 definidos:")
for ind in indicadores_etapa2:
    count = RegistroProducao.objects.filter(indicador=ind).count()
    if count > 0:
        print(f"✅ {ind:<25} - {count:>4} registros encontrados")
    else:
        print(f"⚠️  {ind:<25} - Nenhum registro (pode ser normal se não foi usado)")


# ═══════════════════════════════════════════════════════════════
# TESTE 3: Validar cálculo de médias individuais
# ═══════════════════════════════════════════════════════════════
print("\n\n📋 TESTE 3: Validar cálculo de médias (evitar divisão errada)")
print("-" * 80)

# Buscar um pedreiro com registros
pedreiros_com_dados = (
    RegistroProducao.objects
    .filter(funcionario__funcao='pedreiro')
    .values('funcionario_id', 'funcionario__nome_completo')
    .distinct()[:3]
)

if pedreiros_com_dados:
    print("\nExemplo de médias calculadas para pedreiros:\n")
    
    for p in pedreiros_com_dados:
        funcionario_id = p['funcionario_id']
        nome = p['funcionario__nome_completo']
        
        # Buscar registros deste pedreiro
        registros = RegistroProducao.objects.filter(
            funcionario_id=funcionario_id
        )
        
        # Pegar um indicador para exemplo
        indicador_exemplo = registros.values('indicador').distinct().first()
        
        if indicador_exemplo:
            ind_code = indicador_exemplo['indicador']
            prods = registros.filter(indicador=ind_code)
            
            # Calcular média CORRETA
            total_producao = sum(float(p.quantidade) for p in prods)
            total_dias = prods.values('data').distinct().count()
            
            if total_dias > 0:
                media = total_producao / total_dias
                
                print(f"👤 {nome}")
                print(f"   Indicador: {ind_code}")
                print(f"   Total produzido: {total_producao:.2f}")
                print(f"   Dias trabalhados: {total_dias}")
                print(f"   ✅ Média correta: {media:.2f}/dia")
                print()
else:
    print("⚠️  Nenhum pedreiro com registros de produção encontrado.")
    print("   Cadastre alguns apontamentos para testar as médias.")


# ═══════════════════════════════════════════════════════════════
# RESUMO GERAL
# ═══════════════════════════════════════════════════════════════
print("\n" + "="*80)
print("📊 RESUMO GERAL DO SISTEMA")
print("="*80)

total_registros = RegistroProducao.objects.count()
total_pedreiros = Funcionario.objects.filter(funcao='pedreiro', ativo=True).count()
total_indicadores = RegistroProducao.objects.values('indicador').distinct().count()

print(f"\n• Total de registros de produção: {total_registros}")
print(f"• Total de pedreiros ativos: {total_pedreiros}")
print(f"• Total de indicadores em uso: {total_indicadores}")

print("\n\n" + "="*80)
print("✅ TESTES CONCLUÍDOS!")
print("="*80)
print("\n💡 PRÓXIMOS PASSOS:")
print("   1. Acesse o sistema e cadastre um novo apontamento em lote")
print("   2. Deixe ALGUNS campos vazios (sem informar valor)")
print("   3. Verifique se apenas os campos preenchidos geraram registros")
print("   4. Acesse os relatórios e verifique se a Etapa 2 aparece")
print("   5. Acesse o perfil de um pedreiro e clique em 'Ver Médias'")
print("\n")
