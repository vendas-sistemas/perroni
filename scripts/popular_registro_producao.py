"""
Script para popular RegistroProducao com base nos apontamentos existentes.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.funcionarios.models import ApontamentoDiarioLote, RegistroProducao, ApontamentoFuncionario

def popular_registros():
    """Cria RegistroProducao para todos os apontamentos em lote existentes"""
    
    # Limpar registros existentes (para reprocessamento)
    RegistroProducao.objects.all().delete()
    print("Registros existentes limpos.")
    
    # Buscar todos os lotes
    lotes = ApontamentoDiarioLote.objects.all().order_by('data')
    print(f"\nEncontrados {lotes.count()} apontamentos em lote.")
    
    total_criados = 0
    
    for lote in lotes:
        print(f"\nProcessando: {lote}")
        
        # Buscar funcionários do lote
        funcionarios_lote = lote.funcionarios.all()
        pedreiros = [f for f in funcionarios_lote if f.funcionario.funcao == 'pedreiro']
        
        if not pedreiros:
            print(f"  ⚠️ Sem pedreiros neste lote, pulando...")
            continue
        
        # Buscar campos da etapa
        campos_dict = lote.get_campos_etapa_dict()
        
        if not campos_dict:
            print(f"  ⚠️ Sem campos de produção neste lote, pulando...")
            continue
        
        print(f"  Campos encontrados: {campos_dict}")
        
        # Criar registros para cada pedreiro
        for func_lote in funcionarios_lote:
            if func_lote.funcionario.funcao == 'pedreiro':
                lote._criar_registro_producao(
                    funcionario=func_lote.funcionario,
                    obra=lote.obra,
                    etapa=lote.etapa,
                    data=lote.data,
                    detalhes_producao=campos_dict
                )
                print(f"  ✓ Criados registros para {func_lote.funcionario.nome_completo}")
    
    # Contar total
    total_criados = RegistroProducao.objects.count()
    print(f"\n{'='*60}")
    print(f"✅ CONCLUÍDO!")
    print(f"Total de RegistroProducao criados: {total_criados}")
    print(f"{'='*60}\n")
    
    # Mostrar resumo por indicador
    from django.db.models import Count, Sum
    resumo = RegistroProducao.objects.values('indicador').annotate(
        total=Count('id'),
        soma=Sum('quantidade')
    ).order_by('indicador')
    
    print("\nResumo por indicador:")
    for item in resumo:
        indicador_nome = dict(RegistroProducao.INDICADOR_CHOICES).get(item['indicador'], item['indicador'])
        print(f"  {indicador_nome}: {item['total']} registros, total={item['soma']}")


if __name__ == '__main__':
    popular_registros()
