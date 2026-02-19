"""
Script para verificar se os cálculos de média dos dados reais estão corretos.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.funcionarios.models import RegistroProducao, Funcionario
from apps.relatorios.services.analytics_indicadores import ranking_por_indicador
from datetime import date
import sys
import io

# Configurar stdout para UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 70)
print("VALIDACAO DE CALCULOS - DADOS REAIS DO SISTEMA")
print("=" * 70)

# Pegar todos os pedreiros
pedreiros = Funcionario.objects.filter(funcao='pedreiro')

print(f"\n📊 Pedreiros encontrados: {pedreiros.count()}")

for pedreiro in pedreiros:
    print(f"\n{'─' * 70}")
    print(f"PEDREIRO: {pedreiro.nome_completo}")
    print(f"{'─' * 70}")
    
    # Buscar todos os indicadores deste pedreiro
    indicadores = RegistroProducao.objects.filter(
        funcionario=pedreiro
    ).values_list('indicador', flat=True).distinct()
    
    if not indicadores:
        print("   (Sem dados de produção)")
        continue
    
    for indicador in indicadores:
        # Buscar registros deste indicador
        registros = RegistroProducao.objects.filter(
            funcionario=pedreiro,
            indicador=indicador
        ).order_by('data')
        
        if not registros.exists():
            continue
        
        # Nome do indicador
        indicador_nome = dict(RegistroProducao.INDICADOR_CHOICES).get(
            indicador, 
            indicador
        )
        
        print(f"\n   INDICADOR: {indicador_nome}")
        
        # Calcular manualmente
        total_manual = sum(float(r.quantidade) for r in registros)
        dias_manual = registros.values('data').distinct().count()
        media_manual = total_manual / dias_manual if dias_manual > 0 else 0
        
        # Mostrar detalhes
        print(f"      Registros por dia:")
        for reg in registros:
            print(f"        - {reg.data.strftime('%d/%m/%Y')}: {reg.quantidade} (obra: {reg.obra.nome})")
        
        print(f"\n      Cálculo:")
        print(f"        Total: {total_manual}")
        print(f"        Dias únicos: {dias_manual}")
        print(f"        Média: {total_manual} ÷ {dias_manual} = {media_manual:.2f}")
        
        # Buscar resultado do sistema
        data_inicio = registros.first().data
        data_fim = registros.last().data
        
        ranking = ranking_por_indicador(
            indicador,
            {'funcionario_id': pedreiro.id},
            top=1
        )
        
        if ranking['melhores']:
            media_sistema = ranking['melhores'][0]['media_producao']
            print(f"\n      Sistema retornou: {media_sistema}")
            
            # Validar
            if abs(media_sistema - media_manual) < 0.01:  # Tolerância de 0.01
                print(f"      [OK] CORRETO!")
            else:
                print(f"      [ERRO] Esperado: {media_manual:.2f}, Obtido: {media_sistema}")

print("\n" + "=" * 70)
print("VALIDACAO CONCLUIDA")
print("=" * 70)
