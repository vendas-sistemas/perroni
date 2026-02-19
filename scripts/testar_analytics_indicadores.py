"""
Script para testar o novo sistema de analytics_indicadores.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.relatorios.services.analytics_indicadores import (
    ranking_geral_por_etapas,
    gerar_relatorio_completo_indicadores,
)

def testar_sistema():
    """Testa o novo sistema de relatórios"""
    
    print("="*60)
    print("TESTANDO NOVO SISTEMA DE RELATÓRIOS POR INDICADOR")
    print("="*60)
    print()
    
    # Teste 1: Ranking geral por etapas
    print("1. Testando ranking_geral_por_etapas()...")
    resultado = ranking_geral_por_etapas()
    print(f"   ✓ Etapas encontradas: {len(resultado)}")
    
    for etapa in resultado:
        print(f"\n   {etapa['nome']}")
        print(f"   └─ {len(etapa['indicadores'])} indicadores com dados:")
        
        for indicador in etapa['indicadores']:
            qtd_melhores = len(indicador['melhores'])
            qtd_piores = len(indicador['piores'])
            print(f"      • {indicador['nome']} ({indicador['unidade']})")
            print(f"        → {qtd_melhores} melhores, {qtd_piores} piores")
            
            if qtd_melhores > 0:
                melhor = indicador['melhores'][0]
                print(f"        🥇 {melhor['nome']}: {melhor['media_producao']} {indicador['unidade']}/dia")
    
    print("\n" + "="*60)
    print("2. Testando gerar_relatorio_completo_indicadores()...")
    relatorio = gerar_relatorio_completo_indicadores()
    
    print(f"   ✓ Ranking por etapas: {len(relatorio['ranking_por_etapas'])} etapas")
    print(f"   ✓ Média dias/etapa: {len(relatorio['media_dias_etapa'])} etapas")
    print(f"   ✓ Média individual: {len(relatorio['media_individual'])} pedreiros")
    
    if relatorio['media_individual']:
        print("\n   Top 3 pedreiros (média geral):")
        for i, pedreiro in enumerate(relatorio['media_individual'][:3], 1):
            print(f"      {i}. {pedreiro['nome']}: {pedreiro['media_producao']} unidades/dia ({pedreiro['total_dias']} dias)")
    
    print("\n" + "="*60)
    print("✅ TESTES CONCLUÍDOS COM SUCESSO!")
    print("="*60)


if __name__ == '__main__':
    testar_sistema()
