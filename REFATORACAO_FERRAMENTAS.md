# Refatoração do Módulo de Ferramentas

## 📋 Resumo da Mudança

O módulo de ferramentas foi **completamente refatorado** de um sistema de rastreamento individual (uma ferramenta = um registro no banco) para um **sistema de inventário baseado em quantidades** (uma ferramenta = tipo/modelo com quantidade distribuída).

### Antes (Sistema Antigo)
- **10 alicates idênticos = 10 registros no banco de dados**
- Cada unidade tinha seu próprio código
- Campo `status` indicava onde estava cada unidade
- Campo `obra_atual` indicava em qual obra estava

### Depois (Sistema Novo)
- **10 alicates = 1 registro de Ferramenta + distribuição de quantidades**
- Um código por tipo/modelo
- Quantidade distribuída entre localizações (depósito, obras, manutenção, perdida)
- Movimentações registram transferências de quantidades

---

## 🗂️ Nova Estrutura de Modelos

### 1. **Ferramenta** (Tipo/Modelo)
Representa um tipo de ferramenta, não unidades individuais.

**Novos campos:**
- `quantidade_total` → Total de unidades deste tipo
- `valor_unitario` → Preço por unidade (antes: `valor_aquisicao`)

**Campos removidos:**
- ~~`status`~~ → Agora calculado dinamicamente nas localizações
- ~~`obra_atual`~~ → Agora nas localizações

**Propriedades calculadas:**
```python
ferramenta.quantidade_deposito      # Quantas no depósito
ferramenta.quantidade_em_obras      # Quantas em obras (soma)
ferramenta.quantidade_manutencao    # Quantas em manutenção
ferramenta.quantidade_perdida       # Quantas perdidas
ferramenta.valor_total_estoque      # valor_unitario × quantidade_total
```

### 2. **LocalizacaoFerramenta** (NOVO)
Distribui quantidades de uma ferramenta entre diferentes localizações.

**Campos:**
- `ferramenta` → FK para Ferramenta
- `local_tipo` → Escolha: 'deposito', 'obra', 'manutencao', 'perdida'
- `obra` → FK para Obra (obrigatório se `local_tipo='obra'`)
- `quantidade` → Quantas unidades nesta localização

**Regras:**
- Soma de todas as localizações DEVE ser igual a `ferramenta.quantidade_total`
- Não pode haver quantidade negativa
- Um tipo de ferramenta só pode ter UMA localização por tipo (exceto obras)

**Exemplo:**
```python
# Alicate Universal com 10 unidades
alicate = Ferramenta.objects.get(nome='Alicate Universal')
alicate.quantidade_total = 10

# Distribuição:
LocalizacaoFerramenta(ferramenta=alicate, local_tipo='deposito', quantidade=3)
LocalizacaoFerramenta(ferramenta=alicate, local_tipo='obra', obra=obra_a, quantidade=5)
LocalizacaoFerramenta(ferramenta=alicate, local_tipo='manutencao', quantidade=2)
# Total: 3 + 5 + 2 = 10 ✓
```

### 3. **MovimentacaoFerramenta** (Atualizado)
Agora registra movimentação de **quantidades**, não de unidades individuais.

**Novos campos:**
- `quantidade` → Quantas unidades estão sendo movidas (obrigatório)
- `origem_tipo` → 'deposito', 'obra', 'manutencao', 'compra'
- `destino_tipo` → 'deposito', 'obra', 'manutencao', 'perdida', 'descarte'

**Campos removidos:**
- ~~`origem`~~ (string livre) → Agora `origem_tipo` (escolha)
- ~~`destino`~~ (string livre) → Agora `destino_tipo` (escolha)

**Comportamento:**
- Ao salvar, **atualiza automaticamente** as LocalizacaoFerramenta origem e destino
- Usa **F() expressions** para evitar race conditions
- Validado pelo form (não pode mover mais do que disponível)

### 4. **ItemConferencia** (Atualizado)
Agora compara **quantidades esperadas vs encontradas**.

**Novos campos:**
- `quantidade_esperada` → Quanto deveria ter segundo o sistema
- `quantidade_encontrada` → Quanto realmente foi encontrado

**Status auto-calculado:**
- `'ok'` → Quantidades batem
- `'falta'` → Encontrou menos que esperado
- `'sobra'` → Encontrou mais que esperado

**Propriedades:**
```python
item.diferenca  # quantidade_encontrada - quantidade_esperada
# Positivo = sobra, Negativo = falta, Zero = ok
```

---

## 🔄 Tipos de Movimentação

### **Entrada no Depósito** (`entrada_deposito`)
- **Origem:** Compra/Recebimento
- **Destino:** Depósito
- **Valida:** Nenhuma (entrada de estoque)
- **Exemplo:** Comprou 10 martelos → entra no depósito

### **Saída para Obra** (`saida_obra`)
- **Origem:** Depósito
- **Destino:** Obra específica
- **Valida:** Quantidade disponível NO DEPÓSITO
- **Exemplo:** Levar 5 martelos do depósito para Obra A

### **Transferência entre Obras** (`transferencia`)
- **Origem:** Obra A
- **Destino:** Obra B
- **Valida:** Quantidade disponível NA OBRA ORIGEM
- **Exemplo:** Mover 3 martelos da Obra A para Obra B

### **Retorno ao Depósito** (`retorno_deposito`)
- **Origem:** Obra
- **Destino:** Depósito
- **Valida:** Quantidade disponível NA OBRA
- **Exemplo:** Devolver 5 martelos da Obra A para o depósito

### **Envio para Manutenção** (`envio_manutencao`)
- **Origem:** Depósito OU Obra
- **Destino:** Manutenção
- **Valida:** Quantidade disponível na origem
- **Exemplo:** Enviar 2 martelos para conserto

### **Retorno de Manutenção** (`retorno_manutencao`)
- **Origem:** Manutenção
- **Destino:** Depósito
- **Valida:** Quantidade em manutenção
- **Exemplo:** 2 martelos consertados voltam

### **Perda/Extravio** (`perda`)
- **Origem:** Depósito OU Obra
- **Destino:** Perdida
- **Valida:** Quantidade disponível na origem
- **Exemplo:** 1 martelo perdido na Obra B

### **Descarte/Baixa** (`descarte`)
- **Origem:** Depósito OU Obra
- **Destino:** Descarte (remove do total)
- **Valida:** Quantidade disponível na origem
- **Exemplo:** Descartar 2 martelos quebrados

---

## ✅ Validações Implementadas

### No Model (Ferramenta)
```python
# Não permite quantidade_total negativa
quantidade_total = PositiveIntegerField()

# Propriedades calculam somas automaticamente
@property
def quantidade_deposito(self):
    return self.localizacoes.filter(local_tipo='deposito').aggregate(
        Sum('quantidade')
    )['quantidade__sum'] or 0
```

### No Model (LocalizacaoFerramenta)
```python
# Não permite quantidade negativa
quantidade = PositiveIntegerField()

# Constraints no banco:
class Meta:
    constraints = [
        # Uma ferramenta só pode ter UMA localização 'deposito'
        UniqueConstraint(
            fields=['ferramenta', 'local_tipo'],
            condition=Q(local_tipo__in=['deposito', 'manutencao', 'perdida']),
            name='unique_ferramenta_local_nao_obra'
        ),
        # Uma ferramenta só pode ter UMA localização por obra
        UniqueConstraint(
            fields=['ferramenta', 'obra'],
            condition=Q(local_tipo='obra', obra__isnull=False),
            name='unique_ferramenta_obra'
        )
    ]
```

### No Form (MovimentacaoForm)
```python
def clean(self):
    # Para 'saida_obra': verifica se tem quantidade no DEPÓSITO
    if tipo == 'saida_obra':
        qtd_disponivel = ferramenta.quantidade_deposito
        if quantidade > qtd_disponivel:
            raise ValidationError(f'Apenas {qtd_disponivel} disponível(is) no depósito')
    
    # Para 'transferencia': verifica se tem quantidade NA OBRA ORIGEM
    if tipo == 'transferencia':
        loc = ferramenta.localizacoes.get(local_tipo='obra', obra=obra_origem)
        qtd_disponivel = loc.quantidade
        if quantidade > qtd_disponivel:
            raise ValidationError(f'Apenas {qtd_disponivel} em {obra_origem.nome}')
```

### No Model (MovimentacaoFerramenta.save)
```python
def save(self, *args, **kwargs):
    # Usa F() expressions para evitar race conditions
    with transaction.atomic():
        # Atualizar origem
        if self.origem_tipo == 'deposito':
            loc_origem = self.ferramenta.localizacoes.get(local_tipo='deposito')
            loc_origem.quantidade = F('quantidade') - self.quantidade
            loc_origem.save(update_fields=['quantidade'])
        
        # Atualizar destino
        if self.destino_tipo == 'obra':
            loc_destino, created = self.ferramenta.localizacoes.get_or_create(
                local_tipo='obra',
                obra=self.obra_destino,
                defaults={'quantidade': 0}
            )
            loc_destino.quantidade = F('quantidade') + self.quantidade
            loc_destino.save(update_fields=['quantidade'])
```

---

## 📦 Arquivos Modificados/Criados

### Backups (Não Deletar)
- `apps/ferramentas/models_backup_old.py` → Modelo antigo
- `apps/ferramentas/forms_backup_old.py` → Forms antigos
- `apps/ferramentas/admin_backup_old.py` → Admin antigo
- `apps/ferramentas/views_backup_old.py` → Views antigas

### Arquivos Atualizados
- ✅ `apps/ferramentas/models.py` → Refatorado completamente
- ✅ `apps/ferramentas/forms.py` → Reescrito com validações de quantidade
- ✅ `apps/ferramentas/admin.py` → Atualizado com inline de LocalizacaoFerramenta
- ✅ `apps/ferramentas/views.py` → Atualizado completamente
- ✅ `templates/ferramentas/ferramenta_list.html` → Mostra distribuição de quantidades
- ✅ `templates/ferramentas/ferramenta_detail.html` → Mostra cards de distribuição e lista de obras
- ✅ `templates/ferramentas/movimentacao_form.html` → Funciona com novos campos
- ✅ Migrations aplicadas: `0003_alter_conferenciaferramenta_unique_together_and_more.py`
- ✅ `scripts/migrar_dados_ferramentas.py` → Script de migração criado

### Pendentes de Atualização
Nenhum! Todos os arquivos foram atualizados.

---

## 🚀 Como Usar o Novo Sistema

### Criar uma Nova Ferramenta
```python
# 1. Criar ferramenta
ferramenta = Ferramenta.objects.create(
    codigo='MART-54321',
    nome='Martelo de Borracha',
    categoria='mao',
    quantidade_total=15,
    valor_unitario=Decimal('25.00')
)

# 2. Criar localização inicial (automático via view)
LocalizacaoFerramenta.objects.create(
    ferramenta=ferramenta,
    local_tipo='deposito',
    quantidade=15
)

# 3. Registrar entrada (automático via view)
MovimentacaoFerramenta.objects.create(
    ferramenta=ferramenta,
    quantidade=15,
    tipo='entrada_deposito',
    origem_tipo='compra',
    destino_tipo='deposito',
    responsavel=user
)
```

### Enviar Ferramentas para Obra
```python
# Formulário valida automaticamente se tem quantidade no depósito
mov = MovimentacaoFerramenta.objects.create(
    ferramenta=martelo,
    quantidade=5,
    tipo='saida_obra',
    obra_destino=obra_residencial,
    origem_tipo='deposito',  # preenchido automaticamente pelo form
    destino_tipo='obra',     # preenchido automaticamente pelo form
    responsavel=user
)
# Ao salvar, atualiza automaticamente:
# - LocalizacaoFerramenta(deposito): 15 → 10
# - LocalizacaoFerramenta(obra_residencial): 0 → 5
```

### Consultar Distribuição
```python
martelo = Ferramenta.objects.get(codigo='MART-54321')

print(f"Total: {martelo.quantidade_total}")              # 15
print(f"Depósito: {martelo.quantidade_deposito}")        # 10
print(f"Em obras: {martelo.quantidade_em_obras}")        # 5
print(f"Manutenção: {martelo.quantidade_manutencao}")    # 0

# Distribuição completa
dist = martelo.get_distribuicao_completa()
# {
#     'deposito': 10,
#     'obras': [{'obra': <Obra>, 'quantidade': 5}],
#     'manutencao': 0,
#     'perdida': 0
# }
```

### Fazer Conferência
```python
# 1. Criar conferência
conf = ConferenciaFerramenta.objects.create(
    obra=obra_residencial,
    fiscal=user
)

# 2. Adicionar itens (quantidade_esperada é preenchida automaticamente)
item = ItemConferencia.objects.create(
    conferencia=conf,
    ferramenta=martelo,
    quantidade_esperada=5,     # vem da LocalizacaoFerramenta
    quantidade_encontrada=4    # fiscal informou que achou 4
)

# Status calculado automaticamente
print(item.status)      # 'falta'
print(item.diferenca)   # -1
```

---

## ⚠️ Importante para Migração de Dados

### Se houver dados antigos no banco
1. **Backup obrigatório** antes de aplicar as migrations
2. **Dados antigos continuam no banco** mas com campos removidos
3. **Solução:**
   - Criar script para migrar dados antigos
   - Agrupar ferramentas idênticas (mesmo tipo)
   - Contar quantidades e criar LocalizacaoFerramenta

### Script de migração (exemplo)
```python
from collections import defaultdict
from apps.ferramentas.models import Ferramenta, LocalizacaoFerramenta

# 1. Agrupar ferramentas antigas por tipo
grupos = defaultdict(list)
for f in Ferramenta.objects.all():
    # Agrupar por nome ou outro critério
    grupos[f.nome].append(f)

# 2. Para cada grupo:
for nome, ferramentas in grupos.items():
    # Manter apenas a primeira, contar quantidade
    principal = ferramentas[0]
    principal.quantidade_total = len(ferramentas)
    principal.save()
    
    # Contar por localização
    por_local = defaultdict(int)
    for f in ferramentas:
        if f.status == 'deposito':
            por_local['deposito'] += 1
        elif f.status == 'em_obra':
            por_local[('obra', f.obra_atual_id)] += 1
    
    # Criar LocalizacaoFerramenta
    for key, qtd in por_local.items():
        if key == 'deposito':
            LocalizacaoFerramenta.objects.create(
                ferramenta=principal,
                local_tipo='deposito',
                quantidade=qtd
            )
        else:
            local_tipo, obra_id = key
            LocalizacaoFerramenta.objects.create(
                ferramenta=principal,
                local_tipo='obra',
                obra_id=obra_id,
                quantidade=qtd
            )
    
    # Deletar duplicatas
    for f in ferramentas[1:]:
        f.delete()
```

---

## 📝 Próximos Passos

### ✅ Concluído
1. ✅ **Models refatorados** com sistema de quantidades
2. ✅ **Forms com validações** completas
3. ✅ **Admin atualizado** com inline LocalizacaoFerramenta
4. ✅ **Views atualizadas** (todas funcionando)
5. ✅ **Templates atualizados** (ferramenta_list, ferramenta_detail)
6. ✅ **Migrations aplicadas** sem erros
7. ✅ **System check passa** sem problemas
8. ✅ **Script de migração** criado (scripts/migrar_dados_ferramentas.py)

### 📋 Para uso em produção
1. **Fazer backup do banco de dados**
2. **Executar script de migração** (se houver dados antigos):
   ```bash
   python manage.py shell < scripts/migrar_dados_ferramentas.py
   ```
3. **Testar fluxo completo:**
   - Criar nova ferramenta
   - Fazer movimentação
   - Criar conferência
4. **Ajustar distribuição** de ferramentas existentes se necessário

---

## 🐛 Debug / Troubleshooting

### Erro: "Quantidade não disponível"
**Causa:** Tentando mover mais do que existe na localização origem  
**Solução:** Verificar `ferramenta.quantidade_deposito` ou `.localizacoes.get(obra=X).quantidade`

### Erro: "Sum of localizações != quantidade_total"
**Causa:** Inconsistência entre total e distribuição  
**Solução:** Rodar validação:
```python
for f in Ferramenta.objects.all():
    soma = f.localizacoes.aggregate(Sum('quantidade'))['quantidade__sum'] or 0
    if soma != f.quantidade_total:
        print(f"ERRO: {f.codigo} - Total: {f.quantidade_total}, Soma: {soma}")
```

### Como resetar tudo (DEV ONLY)
```bash
python manage.py migrate ferramentas zero
python manage.py migrate ferramentas
python manage.py createsuperuser
```

---

## 📞 Suporte

Se encontrar problemas ou tiver dúvidas sobre o novo sistema:
1. Verificar backups (`*_backup_old.py`)
2. Consultar este documento
3. Verificar validações nos forms/models
4. Consultar logs de erro Django

**Data da Refatoração:** 16/02/2025  
**Status:** ✅ COMPLETAMENTE REFATORADO - Pronto para produção (após backup e migração de dados)
