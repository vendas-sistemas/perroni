"""
Script para migrar dados antigos do sistema individual para o sistema de quantidades.

IMPORTANTE: Execute este script SOMENTE SE você tiver dados antigos no banco de dados.
Este script irá:
1. Agrupar ferramentas idênticas por nome/tipo
2. Contar quantidades por localização
3. Criar registros de LocalizacaoFerramenta
4. Remover registros duplicados

ATENÇÃO: Faça backup do banco de dados antes de executar!

Uso:
    python manage.py shell < scripts/migrar_dados_ferramentas.py
"""

from django.db import transaction
from django.db.models import Q, Count
from collections import defaultdict
from apps.ferramentas.models import Ferramenta, LocalizacaoFerramenta
from decimal import Decimal

print("=" * 60)
print("SCRIPT DE MIGRAÇÃO DE DADOS - FERRAMENTAS")
print("=" * 60)
print()

# Verificar se existem dados para migrar
total_ferramentas = Ferramenta.objects.count()
print(f"Total de ferramentas no banco: {total_ferramentas}")

if total_ferramentas == 0:
    print("✅ Nenhuma ferramenta encontrada. Nada a migrar.")
    exit(0)

# Verificar se já tem LocalizacaoFerramenta (já migrado)
total_localizacoes = LocalizacaoFerramenta.objects.count()
if total_localizacoes > 0:
    print(f"⚠️  Já existem {total_localizacoes} registros de LocalizacaoFerramenta.")
    resposta = input("Deseja continuar mesmo assim? (s/n): ")
    if resposta.lower() != 's':
        print("❌ Migração cancelada.")
        exit(0)

print()
print("INICIANDO MIGRAÇÃO...")
print()

# Agrupar ferramentas por nome (você pode ajustar o critério)
grupos = defaultdict(list)
for ferramenta in Ferramenta.objects.all():
    # Chave: nome + categoria (para agrupar ferramentas idênticas)
    chave = (ferramenta.nome, ferramenta.categoria)
    grupos[chave].append(ferramenta)

print(f"📦 Encontrados {len(grupos)} grupos de ferramentas distintas")
print()

ferramentas_migradas = 0
ferramentas_removidas = 0
localizacoes_criadas = 0

with transaction.atomic():
    for (nome, categoria), ferramentas in grupos.items():
        if len(ferramentas) == 1:
            # Só tem uma ferramenta deste tipo
            f = ferramentas[0]
            print(f"  • {f.codigo} - {f.nome} (única unidade)")
            
            # Garantir quantidade_total
            if f.quantidade_total == 0:
                f.quantidade_total = 1
                f.save(update_fields=['quantidade_total'])
            
            # Criar localização se não existir
            # NOTA: Como não temos mais status/obra_atual no modelo novo,
            # vamos colocar tudo no depósito por padrão
            if not f.localizacoes.exists():
                LocalizacaoFerramenta.objects.create(
                    ferramenta=f,
                    local_tipo='deposito',
                    quantidade=f.quantidade_total
                )
                localizacoes_criadas += 1
            
            ferramentas_migradas += 1
        else:
            # Múltiplas ferramentas do mesmo tipo - consolidar
            print(f"  🔄 {nome} ({categoria}) - {len(ferramentas)} unidades encontradas")
            
            # Usar a primeira como principal
            principal = ferramentas[0]
            principal.quantidade_total = len(ferramentas)
            
            # Somar valores se existirem
            valores = [f.valor_unitario for f in ferramentas if f.valor_unitario]
            if valores:
                principal.valor_unitario = sum(valores) / len(valores)
            
            principal.save(update_fields=['quantidade_total', 'valor_unitario'])
            
            # Contar por localização (SIMULAÇÃO - sem status/obra_atual)
            # Como os campos antigos foram removidos, vamos colocar tudo no depósito
            LocalizacaoFerramenta.objects.get_or_create(
                ferramenta=principal,
                local_tipo='deposito',
                defaults={'quantidade': len(ferramentas)}
            )
            localizacoes_criadas += 1
            
            # Remover duplicatas (manter apenas a principal)
            for f_dup in ferramentas[1:]:
                print(f"    ❌ Removendo duplicata: {f_dup.codigo}")
                # Transferir movimentações para a principal (opcional)
                f_dup.movimentacoes.all().update(ferramenta=principal)
                f_dup.delete()
                ferramentas_removidas += 1
            
            ferramentas_migradas += 1

print()
print("=" * 60)
print("✅ MIGRAÇÃO CONCLUÍDA!")
print("=" * 60)
print(f"📊 Ferramentas migradas: {ferramentas_migradas}")
print(f"❌ Ferramentas removidas (duplicatas): {ferramentas_removidas}")
print(f"📍 Localizações criadas: {localizacoes_criadas}")
print()
print("⚠️  IMPORTANTE:")
print("   1. Todos os itens foram colocados no DEPÓSITO por padrão")
print("   2. Ajuste manualmente a distribuição se necessário")
print("   3. Use movimentações para redistribuir entre obras")
print()

# Validação final
print("VALIDANDO CONSISTÊNCIA...")
inconsistencias = 0
for f in Ferramenta.objects.all():
    soma_locs = sum(loc.quantidade for loc in f.localizacoes.all())
    if soma_locs != f.quantidade_total:
        print(f"⚠️  INCONSISTÊNCIA: {f.codigo} - Total: {f.quantidade_total}, Soma localizações: {soma_locs}")
        inconsistencias += 1

if inconsistencias == 0:
    print("✅ Todas as ferramentas estão consistentes!")
else:
    print(f"⚠️  {inconsistencias} inconsistências encontradas. Execute correções manuais.")

print()
print("=" * 60)
