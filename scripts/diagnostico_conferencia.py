"""
Script de diagnóstico para verificar configuração de conferências.
Uso: python manage.py shell < scripts/diagnostico_conferencia.py
"""

from apps.ferramentas.models import Ferramenta, LocalizacaoFerramenta, MovimentacaoFerramenta
from apps.obras.models import Obra

print("=" * 70)
print("DIAGNÓSTICO DO SISTEMA DE CONFERÊNCIA")
print("=" * 70)
print()

# 1. Verificar ferramentas
total_ferramentas = Ferramenta.objects.filter(ativo=True).count()
print(f"✅ Total de ferramentas ativas: {total_ferramentas}")
print()

# 2. Verificar LocalizacaoFerramenta
total_localizacoes = LocalizacaoFerramenta.objects.count()
print(f"✅ Total de localizações registradas: {total_localizacoes}")
print()

# 3. Verificar ferramentas POR OBRA
print("📍 FERRAMENTAS POR OBRA:")
print("-" * 70)

obras = Obra.objects.filter(ativo=True)[:10]
obras_com_ferramentas = []

for obra in obras:
    localizacoes = LocalizacaoFerramenta.objects.filter(
        local_tipo='obra',
        obra=obra,
        quantidade__gt=0
    ).select_related('ferramenta')
    
    qtd_tipos = localizacoes.count()
    qtd_total = sum(loc.quantidade for loc in localizacoes)
    
    print(f"🏗️  {obra.nome}:")
    print(f"   - Tipos de ferramentas: {qtd_tipos}")
    print(f"   - Quantidade total: {qtd_total}")
    
    if qtd_tipos > 0:
        obras_com_ferramentas.append(obra.nome)
        print(f"   - Ferramentas:")
        for loc in localizacoes[:5]:  # Mostrar no máximo 5
            print(f"     • {loc.ferramenta.codigo} - {loc.ferramenta.nome}: {loc.quantidade} un.")
        if localizacoes.count() > 5:
            print(f"     ... e mais {localizacoes.count() - 5} ferramenta(s)")
    print()

# 4. Verificar depósito
loc_deposito = LocalizacaoFerramenta.objects.filter(local_tipo='deposito')
qtd_deposito = sum(loc.quantidade for loc in loc_deposito)
print(f"📦 Ferramentas no DEPÓSITO: {qtd_deposito} unidades")
print()

# 5. Verificar manutenção
loc_manutencao = LocalizacaoFerramenta.objects.filter(local_tipo='manutencao')
qtd_manutencao = sum(loc.quantidade for loc in loc_manutencao)
print(f"🔧 Ferramentas em MANUTENÇÃO: {qtd_manutencao} unidades")
print()

# 6. Verificar perdidas
loc_perdida = LocalizacaoFerramenta.objects.filter(local_tipo='perdida')
qtd_perdida = sum(loc.quantidade for loc in loc_perdida)
print(f"❌ Ferramentas PERDIDAS: {qtd_perdida} unidades")
print()

# 7. Resumo
print("=" * 70)
print("RESUMO E RECOMENDAÇÕES:")
print("=" * 70)

if total_ferramentas == 0:
    print("❌ PROBLEMA: Não há ferramentas cadastradas no sistema!")
    print("   SOLUÇÃO: Cadastre ferramentas primeiro.")
elif total_localizacoes == 0:
    print("❌ PROBLEMA: Ferramentas cadastradas mas sem localizações!")
    print("   SOLUÇÃO: Execute o script de migração:")
    print("   python manage.py shell < scripts/migrar_dados_ferramentas.py")
elif len(obras_com_ferramentas) == 0:
    print("⚠️  AVISO: Todas as ferramentas estão no depósito!")
    print("   SOLUÇÃO: Movimente ferramentas para obras usando:")
    print("   - URL: /ferramentas/movimentar/")
    print("   - Tipo: Saída para Obra")
else:
    print(f"✅ Sistema configurado corretamente!")
    print(f"✅ Obras com ferramentas: {len(obras_com_ferramentas)}")
    print(f"   {', '.join(obras_com_ferramentas[:3])}")
    if len(obras_com_ferramentas) > 3:
        print(f"   ... e mais {len(obras_com_ferramentas) - 3} obra(s)")
    print()
    print("✅ Você pode criar conferências para estas obras.")

print()
print("=" * 70)
