import os
import sys
import django

# Setup Django
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from datetime import date, timedelta
from apps.relatorios.services.analytics_indicadores import gerar_relatorio_completo_indicadores

print("=" * 80)
print("TESTANDO GERAÇÃO DE RANKING")
print("=" * 80)

# Tentar gerar relatório
try:
    # Sem filtros para pegar todos os dados
    print(f"\nGerando relatório SEM FILTROS...")
    
    relatorio = gerar_relatorio_completo_indicadores()
    
    print("\n✅ Relatório gerado com sucesso!")
    
    # Verificar o que foi retornado
    print(f"\nTipo: {type(relatorio)}")
    
    if isinstance(relatorio, dict):
        print(f"\nChaves do relatório:")
        for chave in relatorio.keys():
            print(f"  - {chave}")
        
        # Ver rankings_indicadores
        if 'rankings_indicadores' in relatorio:
            print(f"\n{'=' * 80}")
            print("RANKINGS POR INDICADOR:")
            print(f"{'=' * 80}")
            
            rankings = relatorio['rankings_indicadores']
            print(f"\nTotal de indicadores com dados: {len(rankings)}")
            
            for indicador, dados in rankings.items():
                print(f"\n  📊 {indicador}:")
                if isinstance(dados, dict):
                    print(f"      Nome: {dados.get('nome', 'N/A')}")
                    print(f"      Unidade: {dados.get('unidade', 'N/A')}")
                    print(f"      Total no ranking: {len(dados.get('ranking', []))}")
                    
                    # Mostrar top 3
                    ranking = dados.get('ranking', [])
                    if ranking:
                        print(f"      Top 3:")
                        for i, item in enumerate(ranking[:3], 1):
                            nome = item.get('nome', 'N/A')
                            media = item.get('media_dia', 0)
                            dias = item.get('total_dias', 0)
                            print(f"        {i}. {nome}: {media}/dia ({dias} dias)")
        else:
            print("\n⚠️ Chave 'rankings_indicadores' não encontrada")
        
        # Ver ranking_por_etapas
        if 'ranking_por_etapas' in relatorio:
            print(f"\n{'=' * 80}")
            print("RANKING POR ETAPAS:")
            print(f"{'=' * 80}")
            
            etapas = relatorio['ranking_por_etapas']
            print(f"\nTotal de etapas: {len(etapas)}")
            
            for etapa in etapas:
                print(f"\n  🏗️ {etapa.get('nome', 'N/A')}")
                indicadores = etapa.get('indicadores', [])
                print(f"     Indicadores: {len(indicadores)}")
                for ind in indicadores[:2]:  # Mostrar apenas 2 primeiros
                    print(f"       - {ind.get('nome', 'N/A')}: {len(ind.get('melhores', []))} melhores, {len(ind.get('piores', []))} piores")
    
    else:
        print(f"\n⚠️ Tipo inesperado de relatório: {type(relatorio)}")
        print(relatorio)

except Exception as e:
    print(f"\n❌ ERRO ao gerar relatório:")
    print(f"  Tipo: {type(e).__name__}")
    print(f"  Mensagem: {str(e)}")
    
    import traceback
    print("\nTraceback completo:")
    traceback.print_exc()

print("\n" + "=" * 80)
