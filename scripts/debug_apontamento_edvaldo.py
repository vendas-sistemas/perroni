import os
import sys
import django

# Setup Django
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.funcionarios.models import RegistroProducao, ApontamentoFuncionario, ApontamentoDiarioLote, FuncionarioLote
from datetime import date

print("=" * 80)
print("INVESTIGANDO APONTAMENTO QUE GEROU 400 BLOCOS PARA EDVALDO")
print("=" * 80)

# Buscar o registro problemático
registro = RegistroProducao.objects.get(id=54)

print(f"\nRegistro problemático:")
print(f"  ID: {registro.id}")
print(f"  Data: {registro.data}")
print(f"  Funcionário: {registro.funcionario.nome_completo}")
print(f"  Indicador: {registro.get_indicador_display()}")
print(f"  Quantidade: {registro.quantidade}")
print(f"  Obra: {registro.obra.nome}")
print(f"  Etapa: {registro.etapa}")

# Buscar o apontamento individual relacionado
print("\n" + "=" * 80)
print("APONTAMENTO INDIVIDUAL:")
print("=" * 80)

apontamento_individual = ApontamentoFuncionario.objects.filter(
    funcionario=registro.funcionario,
    data=registro.data,
    obra=registro.obra
).first()

if apontamento_individual:
    print(f"\n  ID: {apontamento_individual.id}")
    print(f"  Funcionário: {apontamento_individual.funcionario.nome_completo}")
    print(f"  Data: {apontamento_individual.data}")
    print(f"  Obra: {apontamento_individual.obra.nome}")
    print(f"  Etapa: {apontamento_individual.etapa}")
    print(f"  Metragem Executada: {apontamento_individual.metragem_executada}")
    print(f"  Horas Trabalhadas: {apontamento_individual.horas_trabalhadas}")
else:
    print("\n  ⚠️ Nenhum apontamento individual encontrado")

# Buscar o lote que gerou esse apontamento
print("\n" + "=" * 80)
print("APONTAMENTO EM LOTE:")
print("=" * 80)

lote = ApontamentoDiarioLote.objects.filter(
    data=registro.data,
    obra=registro.obra,
    etapa=registro.etapa
).first()

if lote:
    print(f"\n  ID: {lote.id}")
    print(f"  Data: {lote.data}")
    print(f"  Obra: {lote.obra.nome}")
    print(f"  Etapa: {lote.etapa}")
    print(f"  Produção Total: {lote.producao_total}")
    
    # Buscar detalhes da etapa
    print(f"\n  Detalhes da Etapa:")
    campos_dict = lote.get_campos_etapa_dict()
    for campo, valor in campos_dict.items():
        print(f"    {campo}: {valor}")
    
    # Buscar funcionários do lote
    print("\n  Funcionários no Lote:")
    funcionarios_lote = FuncionarioLote.objects.filter(lote=lote)
    
    pedreiros_count = 0
    for func_lote in funcionarios_lote:
        funcao = func_lote.funcionario.funcao
        is_pedreiro = " (PEDREIRO)" if funcao == 'pedreiro' else ""
        print(f"    - {func_lote.funcionario.nome_completo}{is_pedreiro} | Horas: {func_lote.horas_trabalhadas}")
        if funcao == 'pedreiro':
            pedreiros_count += 1
    
    print(f"\n  Total de funcionários no lote: {funcionarios_lote.count()}")
    print(f"  Total de PEDREIROS no lote: {pedreiros_count}")
    
    # Calcular o que deveria ser
    if pedreiros_count > 0 and campos_dict.get('parede_7fiadas_blocos'):
        total_blocos = float(campos_dict['parede_7fiadas_blocos'])
        esperado_por_pedreiro = total_blocos / pedreiros_count
        print(f"\n  Cálculo esperado:")
        print(f"    Total de blocos cadastrados: {total_blocos}")
        print(f"    Pedreiros: {pedreiros_count}")
        print(f"    Esperado por pedreiro: {total_blocos} ÷ {pedreiros_count} = {esperado_por_pedreiro:.2f}")
        print(f"    Valor REAL no registro: {registro.quantidade}")
        
        if float(registro.quantidade) != esperado_por_pedreiro:
            print(f"\n  ⚠️ ERRO: Valor esperado ({esperado_por_pedreiro:.2f}) ≠ Valor gravado ({registro.quantidade})")
            diferenca_multiplicador = float(registro.quantidade) / esperado_por_pedreiro
            print(f"  Multiplicador incorreto: {diferenca_multiplicador:.2f}x")
        else:
            print(f"\n  ✅ Valor correto!")
else:
    print("\n  ⚠️ Nenhum lote encontrado")

print("\n" + "=" * 80)
