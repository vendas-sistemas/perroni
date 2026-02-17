"""
Script para verificar e corrigir inconsistências no estoque de ferramentas.
Uso: python manage.py shell < scripts/corrigir_estoque.py
"""

from apps.ferramentas.models import Ferramenta, LocalizacaoFerramenta
from django.db.models import Sum

def verificar_e_corrigir_estoque(ferramenta_id=None):
    """Verifica e corrige estoque de uma ferramenta ou todas"""
    
    if ferramenta_id:
        ferramentas = Ferramenta.objects.filter(pk=ferramenta_id)
    else:
        ferramentas = Ferramenta.objects.filter(ativo=True)
    
    print("="*70)
    print("VERIFICAÇÃO E CORREÇÃO DE ESTOQUE")
    print("="*70)
    
    inconsistentes = []
    
    for f in ferramentas:
        soma_loc = f.localizacoes.aggregate(total=Sum('quantidade'))['total'] or 0
        
        print(f"\n{f.codigo} - {f.nome}")
        print(f"  Quantidade Total Registrada: {f.quantidade_total}")
        print(f"  Soma das Localizações: {soma_loc}")
        
        if soma_loc != f.quantidade_total:
            print(f"  ⚠️  INCONSISTENTE - Diferença: {soma_loc - f.quantidade_total}")
            inconsistentes.append(f)
            
            # Mostrar detalhes das localizações
            print(f"  Localizações:")
            for loc in f.localizacoes.all():
                if loc.local_tipo == 'obra' and loc.obra:
                    print(f"    - {loc.get_local_tipo_display()} ({loc.obra.nome}): {loc.quantidade} un.")
                else:
                    print(f"    - {loc.get_local_tipo_display()}: {loc.quantidade} un.")
            
            # CORRIGIR: Atualizar quantidade_total para bater com soma
            print(f"  ✓ Corrigindo quantidade_total para {soma_loc}...")
            f.quantidade_total = soma_loc
            f.save(update_fields=['quantidade_total'])
            
        else:
            print(f"  ✓ Consistente")
    
    print("\n" + "="*70)
    print(f"RESUMO: {len(inconsistentes)} ferramenta(s) corrigida(s)")
    print("="*70)
    
    if inconsistentes:
        print("\nFerramentas corrigidas:")
        for f in inconsistentes:
            print(f"  - {f.codigo} - {f.nome}")

# Executar para ferramenta específica (ID 1015)
print("\n🔍 Verificando ferramenta ID 1015...")
verificar_e_corrigir_estoque(1015)

print("\n\n📋 Detalhes da ferramenta 1015 após correção:")
f = Ferramenta.objects.get(pk=1015)
print(f"Código: {f.codigo}")
print(f"Nome: {f.nome}")
print(f"Quantidade Total: {f.quantidade_total}")
print(f"\nDistribuição:")
print(f"  Depósito: {f.quantidade_deposito}")
print(f"  Em Obras: {f.quantidade_em_obras}")
print(f"  Manutenção: {f.quantidade_manutencao}")
print(f"  Perdida: {f.quantidade_perdida}")
print(f"\n✅ Correção concluída!")
