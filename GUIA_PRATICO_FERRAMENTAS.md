# 📖 Guia Prático - Sistema de Quantidades

## Cenários Reais de Uso

### Cenário 1: Compra de Novas Ferramentas

**Situação:** Comprou 20 martelos novos para a empresa.

**Passo a Passo:**

1. Acesse: **Ferramentas → Nova Ferramenta**
2. Preencha:
   - Nome: `Martelo de Unha 25mm`
   - Categoria: `Manual`
   - Quantidade Total: `20`
   - Valor Unitário: `R$ 35,00`
   - Data Aquisição: `16/02/2025`
3. Clique em **Salvar**

**Resultado:**
- ✅ Ferramenta criada com código automático (ex: `MART-12345`)
- ✅ Valor total estoque: R$ 700,00 (20 × 35)
- ✅ LocalizacaoFerramenta criada automaticamente:
  - Depósito: 20 unidades
- ✅ Movimentação de entrada registrada automaticamente

---

### Cenário 2: Enviar Ferramentas para Obra

**Situação:** Obra Residencial precisa de 8 martelos.

**Passo a Passo:**

1. Acesse: **Ferramentas → Movimentar**
2. Preencha:
   - Ferramenta: `Martelo de Unha 25mm`
   - Quantidade: `8`
   - Tipo: `Saída para Obra`
   - Obra Destino: `Obra Residencial`
   - Observações: `Envio para início da obra`
3. Clique em **Salvar**

**Validação Automática:**
- ✅ Verifica se tem 8 unidades no depósito
- ❌ Se não tiver, mostra: "Apenas X disponível(is) no depósito"

**Resultado (se OK):**
- ✅ Depósito: 20 → 12 unidades
- ✅ Obra Residencial: 0 → 8 unidades
- ✅ Movimentação registrada com:
  - Origem: Depósito
  - Destino: Obra Residencial
  - Quantidade: 8

---

### Cenário 3: Transferir entre Obras

**Situação:** Obra Residencial terminou etapa, sobram 3 martelos. Obra Comercial precisa deles.

**Passo a Passo:**

1. Acesse: **Ferramentas → Movimentar**
2. Preencha:
   - Ferramenta: `Martelo de Unha 25mm`
   - Quantidade: `3`
   - Tipo: `Transferência entre Obras`
   - Obra Origem: `Obra Residencial`
   - Obra Destino: `Obra Comercial`
3. Clique em **Salvar**

**Validação Automática:**
- ✅ Verifica se tem 3 unidades em Obra Residencial
- ❌ Se não tiver, mostra: "Apenas X em Obra Residencial"

**Resultado (se OK):**
- ✅ Obra Residencial: 8 → 5 unidades
- ✅ Obra Comercial: 0 → 3 unidades
- ✅ Depósito: 12 (inalterado)

---

### Cenário 4: Ferramentas voltam para Depósito

**Situação:** Obra Residencial finalizou, devolver 5 martelos ao depósito.

**Passo a Passo:**

1. Acesse: **Ferramentas → Movimentar**
2. Preencha:
   - Ferramenta: `Martelo de Unha 25mm`
   - Quantidade: `5`
   - Tipo: `Retorno ao Depósito`
   - Obra Origem: `Obra Residencial`
3. Clique em **Salvar**

**Resultado:**
- ✅ Obra Residencial: 5 → 0 unidades
- ✅ Depósito: 12 → 17 unidades

**Distribuição Final:**
```
Martelo de Unha 25mm (20 un. total)
├─ Depósito: 17 un.
├─ Obra Comercial: 3 un.
└─ Obra Residencial: 0 un.
```

---

### Cenário 5: Enviar para Manutenção

**Situação:** 2 martelos quebraram na Obra Comercial, enviar para conserto.

**Passo a Passo:**

1. Acesse: **Ferramentas → Movimentar**
2. Preencha:
   - Ferramenta: `Martelo de Unha 25mm`
   - Quantidade: `2`
   - Tipo: `Envio para Manutenção`
   - Obra Origem: `Obra Comercial`
   - Observações: `Cabo quebrado - conserto`
3. Clique em **Salvar**

**Resultado:**
- ✅ Obra Comercial: 3 → 1 unidade
- ✅ Manutenção: 0 → 2 unidades

---

### Cenário 6: Retorno de Manutenção

**Situação:** 2 martelos consertados voltam para o depósito.

**Passo a Passo:**

1. Acesse: **Ferramentas → Movimentar**
2. Preencha:
   - Ferramenta: `Martelo de Unha 25mm`
   - Quantidade: `2`
   - Tipo: `Retorno de Manutenção`
   - (não precisa obra origem/destino)
3. Clique em **Salvar**

**Resultado:**
- ✅ Manutenção: 2 → 0 unidades
- ✅ Depósito: 17 → 19 unidades

---

### Cenário 7: Perda/Extravio

**Situação:** 1 martelo foi perdido na Obra Comercial.

**Passo a Passo:**

1. Acesse: **Ferramentas → Movimentar**
2. Preencha:
   - Ferramenta: `Martelo de Unha 25mm`
   - Quantidade: `1`
   - Tipo: `Perda/Extravio`
   - Obra Origem: `Obra Comercial`
   - Observações: `Martelo perdido durante obra`
3. Clique em **Salvar**

**Resultado:**
- ✅ Obra Comercial: 1 → 0 unidades
- ✅ Perdida: 0 → 1 unidades
- ⚠️ Quantidade total: 20 (inalterado - ainda consta no sistema)

**Nota:** Perdas ficam registradas mas não são contadas como disponíveis.

---

### Cenário 8: Fazer Conferência na Obra

**Situação:** Precisa conferir ferramentas na Obra Residencial (sistema diz que deveria ter 8 martelos).

**Passo a Passo:**

1. Acesse: **Ferramentas → Conferências → Nova Conferência**
2. Preencha:
   - Obra: `Obra Residencial`
3. Clique em **Salvar** (cria conferência)
4. Clique em **Adicionar Item**
5. Preencha:
   - Ferramenta: `Martelo de Unha 25mm`
   - Quantidade Esperada: __(preenchido automaticamente: 5)__
   - Quantidade Encontrada: `4` _(só achou 4 fisicamente)_
6. Clique em **Salvar Item**

**Resultado:**
- ✅ Item criado com:
  - Status: ⚠️ **FALTA** (diferença: -1)
  - Esperado: 5
  - Encontrado: 4
- ✅ Conferência registrada para futura análise

**Possíveis Status:**
- ✅ **OK:** Encontrado = Esperado
- ⚠️ **FALTA:** Encontrado < Esperado (alguém levou ou perdeu)
- 📦 **SOBRA:** Encontrado > Esperado (alguém trouxe da outra obra)

---

### Cenário 9: Verificar Situação Atual

**Situação:** Quero saber onde estão todos os martelos.

**Passo a Passo:**

1. Acesse: **Ferramentas → Ferramentas**
2. Busque: `Martelo de Unha`
3. Clique em **Ver Detalhes** (ícone olho)

**Resultado Visual:**

```
╔══════════════════════════════════════════════════════════╗
║  Martelo de Unha 25mm (MART-12345)                      ║
╠══════════════════════════════════════════════════════════╣
║  Quantidade Total: 20 unidades                           ║
║  Valor Unitário: R$ 35,00                                ║
║  Valor Total Estoque: R$ 700,00                          ║
╠══════════════════════════════════════════════════════════╣
║  DISTRIBUIÇÃO:                                           ║
║  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    ║
║  │ 🟢 19   │  │ 🔵  0   │  │ 🟡  0   │  │ 🔴  1   │    ║
║  │Depósito │  │ Obras   │  │Manutenç.│  │Perdida  │    ║
║  └─────────┘  └─────────┘  └─────────┘  └─────────┘    ║
║                                                          ║
║  Em Obras: Nenhuma                                       ║
╚══════════════════════════════════════════════════════════╝

HISTÓRICO DE MOVIMENTAÇÕES:
┌────────────────┬───────────────────┬──────┬──────────────────┐
│ Data           │ Tipo              │ Qtd  │ Origem → Destino │
├────────────────┼───────────────────┼──────┼──────────────────┤
│ 16/02 14:30    │ Retorno Manuten.  │  2   │ Manutenção → Dep.│
│ 16/02 12:00    │ Perda/Extravio    │  1   │ Obra Com. → Perd │
│ 16/02 11:00    │ Envio Manutenção  │  2   │ Obra Com. → Manut│
│ 16/02 10:00    │ Retorno Depósito  │  5   │ Obra Res. → Dep. │
│ 16/02 09:00    │ Transferência     │  3   │ Obra Res. → Com. │
│ 16/02 08:00    │ Saída Obra        │  8   │ Depósito → Res.  │
│ 16/02 07:00    │ Entrada Depósito  │ 20   │ Compra → Depósito│
└────────────────┴───────────────────┴──────┴──────────────────┘
```

---

### Cenário 10: Relatórios e Consultas

**Situação:** Preciso saber quantas ferramentas tenho de cada tipo.

**Pela Interface:**

1. Acesse: **Ferramentas → Ferramentas**
2. Veja cards no topo:
   - Total: 47 tipos diferentes
   - Depósito: 234 unidades
   - Em Obras: 189 unidades
   - Manutenção: 12 unidades

**Via Shell Django:**

```python
from apps.ferramentas.models import Ferramenta, LocalizacaoFerramenta
from django.db.models import Sum

# Total de unidades no estoque
total = Ferramenta.objects.aggregate(Sum('quantidade_total'))
print(f"Total de unidades: {total['quantidade_total__sum']}")

# Por categoria
for categoria, nome in Ferramenta.CATEGORIA_CHOICES:
    qtd = Ferramenta.objects.filter(categoria=categoria).aggregate(
        Sum('quantidade_total')
    )['quantidade_total__sum'] or 0
    print(f"{nome}: {qtd} unidades")

# Ferramentas em falta (quantidade baixa)
criticas = Ferramenta.objects.filter(quantidade_total__lt=5, ativo=True)
for f in criticas:
    print(f"⚠️ {f.nome}: apenas {f.quantidade_total} unidades")

# Distribuição por obra
from apps.obras.models import Obra
for obra in Obra.objects.filter(ativo=True):
    qtd = LocalizacaoFerramenta.objects.filter(
        local_tipo='obra',
        obra=obra
    ).aggregate(Sum('quantidade'))['quantidade__sum'] or 0
    print(f"{obra.nome}: {qtd} ferramentas")
```

---

## 🎓 Dicas e Boas Práticas

### ✅ Faça:
- Sempre confira se a quantidade no form está correta antes de salvar
- Use o campo "Observações" para registrar motivos de movimentações
- Faça conferências periódicas nas obras
- Mantenha código de ferramenta único e descritivo
- Use categoria correta para facilitar buscas

### ❌ Evite:
- Criar ferramentas duplicadas (verifique se já existe)
- Movimentar sem conferir disponibilidade
- Deixar conferências sem análise (falta/sobra)
- Ignorar alertas de quantidade insuficiente
- Deletar ferramentas que têm movimentações históricas

### 💡 Truques:
- **Preselecionar ferramenta:** URL com `?f=<id>` ao criar movimentação
- **Copiar código:** Clique no badge do código para copiar
- **Filtro rápido:** Use busca global (campo no topo) para nome OU código
- **Ordenação:** Clique nos cabeçalhos da tabela para ordenar
- **Mobile:** Interface se adapta automaticamente para celular

---

## 📊 Exemplos de Consultas SQL (se precisar)

### Ferramentas mais usadas (mais movimentações)
```sql
SELECT 
    f.codigo,
    f.nome,
    COUNT(m.id) as total_movimentacoes
FROM ferramentas_ferramenta f
LEFT JOIN ferramentas_movimentacaoferramenta m ON m.ferramenta_id = f.id
GROUP BY f.id
ORDER BY total_movimentacoes DESC
LIMIT 10;
```

### Obras com mais ferramentas
```sql
SELECT 
    o.nome,
    SUM(l.quantidade) as total_ferramentas
FROM obras_obra o
LEFT JOIN ferramentas_localizacaoferramenta l ON l.obra_id = o.id AND l.local_tipo = 'obra'
WHERE o.ativo = True
GROUP BY o.id
ORDER BY total_ferramentas DESC;
```

### Valor total do estoque
```sql
SELECT 
    SUM(quantidade_total * valor_unitario) as valor_total_estoque
FROM ferramentas_ferramenta
WHERE ativo = True;
```

### Perdas nos últimos 30 dias
```sql
SELECT 
    f.codigo,
    f.nome,
    SUM(m.quantidade) as quantidade_perdida
FROM ferramentas_movimentacaoferramenta m
JOIN ferramentas_ferramenta f ON m.ferramenta_id = f.id
WHERE m.tipo = 'perda'
  AND m.data_movimentacao >= DATE('now', '-30 days')
GROUP BY f.id
ORDER BY quantidade_perdida DESC;
```

---

**Última Atualização:** 16/02/2025  
**Versão:** 2.0  
**Status:** ✅ Sistema em produção
