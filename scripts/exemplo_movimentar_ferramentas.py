"""
Script para movimentar ferramentas do depósito para obras (EXEMPLO).
Uso: python manage.py shell < scripts/exemplo_movimentar_ferramentas.py

IMPORTANTE: Ajuste os nomes das obras e ferramentas conforme seu sistema!
"""

from apps.ferramentas.models import Ferramenta, MovimentacaoFerramenta, LocalizacaoFerramenta
from apps.obras.models import Obra
from django.contrib.auth.models import User

print("=" * 70)
print("MOVIMENTANDO FERRAMENTAS PARA OBRAS - EXEMPLO")
print("=" * 70)
print()

# Pegar primeiro usuário (será o responsável pelas movimentações)
user = User.objects.first()
if not user:
    print("❌ ERRO: Não há usuários no sistema!")
    exit()

print(f"👤 Responsável: {user.username}")
print()

# Pegar primeiras 3 obras ativas
obras = Obra.objects.filter(ativo=True)[:3]
if obras.count() == 0:
    print("❌ ERRO: Não há obras ativas no sistema!")
    exit()

print(f"🏗️  Obras disponíveis: {obras.count()}")
for obra in obras:
    print(f"   - {obra.nome}")
print()

# Pegar ferramentas do depósito
ferramentas_deposito = LocalizacaoFerramenta.objects.filter(
    local_tipo='deposito',
    quantidade__gte=5  # Apenas ferramentas com 5+ unidades
).select_related('ferramenta')[:10]  # Pegar no máximo 10 tipos

if ferramentas_deposito.count() == 0:
    print("❌ ERRO: Não há ferramentas no depósito com 5+ unidades!")
    exit()

print(f"📦 Ferramentas disponíveis no depósito: {ferramentas_deposito.count()}")
print()

# Distribuir ferramentas entre as obras
movimentacoes_criadas = 0

for i, loc in enumerate(ferramentas_deposito):
    ferramenta = loc.ferramenta
    obra = obras[i % obras.count()]  # Distribuir em round-robin
    
    # Movimentar 3 unidades para a obra
    qtd_movimentar = min(3, loc.quantidade)  # No máximo 3, ou o que tiver
    
    try:
        mov = MovimentacaoFerramenta.objects.create(
            ferramenta=ferramenta,
            quantidade=qtd_movimentar,
            tipo='saida_obra',
            obra_destino=obra,
            origem_tipo='deposito',
            destino_tipo='obra',
            responsavel=user,
            observacoes=f'Movimentação de exemplo - Script automático'
        )
        
        print(f"✅ {ferramenta.codigo} - {ferramenta.nome}")
        print(f"   Movidas {qtd_movimentar} unidade(s) para: {obra.nome}")
        movimentacoes_criadas += 1
        
    except Exception as e:
        print(f"❌ Erro ao movimentar {ferramenta.codigo}: {e}")

print()
print("=" * 70)
print(f"RESUMO:")
print(f"✅ {movimentacoes_criadas} movimentação(ões) criada(s)")
print()
print("🎯 PRÓXIMOS PASSOS:")
print("1. Acesse: http://127.0.0.1:8000/ferramentas/conferencia/criar/")
print("2. Selecione uma das obras acima")
print("3. O sistema listará automaticamente as ferramentas!")
print("=" * 70)
