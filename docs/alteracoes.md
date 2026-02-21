# Sistema de Edição e Exclusão de Apontamentos

## Contexto
Sistema Django de fiscalização de obras. Precisamos implementar CRUD completo (edição e exclusão) para apontamentos em lote, com recálculo automático de todos os relatórios e médias.

## Objetivos
- Adicionar botões Editar e Excluir na listagem de apontamentos
- Exclusão deve reverter produção nas etapas (blocos, %, m²)
- Edição deve recalcular tudo automaticamente
- Registrar histórico de todas as alterações
- Atualizar médias e relatórios após qualquer mudança

## Implementação Detalhada

### 1. Model de Histórico

Criar novo model em `apps/obras/models.py` ou `apps/funcionarios/models.py`:

```python
class HistoricoAlteracaoEtapa(models.Model):
    obra = models.ForeignKey('obras.Obra', on_delete=models.CASCADE, related_name='historico_alteracoes')
    etapa = models.ForeignKey('obras.Etapa', on_delete=models.SET_NULL, null=True, blank=True)
    tipo_alteracao = models.CharField(max_length=20, choices=[
        ('criacao', 'Criação'),
        ('edicao', 'Edição'),
        ('exclusao', 'Exclusão'),
    ])
    data_referencia = models.DateField()
    descricao = models.TextField()
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    dados_anteriores = models.JSONField(blank=True, null=True)
    dados_novos = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
```

Criar migration:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. View de Exclusão

Adicionar em `apps/funcionarios/views.py`:

```python
@login_required
@require_http_methods(["POST"])
@transaction.atomic
def apontamento_lote_delete(request, pk):
    """Exclui apontamento e reverte produção"""
    lote = get_object_or_404(ApontamentoDiarioLote, pk=pk)
    
    # Guardar dados para histórico
    obra, etapa, data = lote.obra, lote.etapa, lote.data
    funcionarios_nomes = [f.funcionario.nome_completo for f in lote.funcionarios.all()]
    
    # REVERTER produção nas etapas
    reverter_producao_etapa(lote)
    
    # EXCLUIR registros de produção
    RegistroProducao.objects.filter(obra=obra, data=data, etapa=etapa.numero_etapa if etapa else None).delete()
    
    # EXCLUIR apontamentos individuais
    ApontamentoFuncionario.objects.filter(obra=obra, data=data, etapa=etapa).delete()
    
    # REGISTRAR no histórico
    HistoricoAlteracaoEtapa.objects.create(
        obra=obra, etapa=etapa, tipo_alteracao='exclusao',
        data_referencia=data,
        descricao=f'Apontamento excluído: {lote.producao_total}',
        usuario=request.user,
        dados_anteriores={'producao_total': float(lote.producao_total), 'funcionarios': funcionarios_nomes}
    )
    
    lote.delete()
    messages.success(request, 'Apontamento excluído! Produção revertida.')
    return redirect('funcionarios:apontamento_lote_list')

def reverter_producao_etapa(lote):
    """Reverte valores adicionados nas etapas"""
    if not lote.etapa:
        return
    
    etapa_num = lote.etapa.numero_etapa
    prods = RegistroProducao.objects.filter(obra=lote.obra, data=lote.data, etapa=etapa_num)
    
    # Buscar detalhes da etapa
    if etapa_num == 1:
        detalhes = Etapa1Fundacao.objects.filter(etapa=lote.etapa).first()
    elif etapa_num == 2:
        detalhes = Etapa2Estrutura.objects.filter(etapa=lote.etapa).first()
    elif etapa_num == 3:
        detalhes = Etapa3Instalacoes.objects.filter(etapa=lote.etapa).first()
    else:
        return
    
    if not detalhes:
        return
    
    # Mapear indicador → campo
    CAMPO_MAP = {
        'parede_7fiadas': 'parede_7fiadas_blocos',
        'alicerce_percentual': 'levantar_alicerce_percentual',
        'platibanda': 'platibanda_blocos',
        'reboco_externo': 'reboco_externo_m2',
        'reboco_interno': 'reboco_interno_m2',
    }
    
    # Reverter cada indicador
    for prod in prods.values('indicador').distinct():
        indicador = prod['indicador']
        total_reverter = prods.filter(indicador=indicador).aggregate(Sum('valor'))['valor__sum'] or Decimal('0')
        campo_nome = CAMPO_MAP.get(indicador)
        
        if campo_nome and hasattr(detalhes, campo_nome):
            valor_atual = getattr(detalhes, campo_nome) or Decimal('0')
            novo_valor = max(valor_atual - total_reverter, Decimal('0'))  # Não fica negativo
            setattr(detalhes, campo_nome, novo_valor)
    
    detalhes.save()
```

### 3. View de Edição

```python
@login_required
@transaction.atomic
def apontamento_lote_edit(request, pk):
    """Edita apontamento existente"""
    lote = get_object_or_404(ApontamentoDiarioLote, pk=pk)
    valores_antigos = {'producao_total': lote.producao_total}
    
    if request.method == 'POST':
        form = ApontamentoDiarioLoteForm(request.POST, instance=lote)
        
        if form.is_valid():
            # Reverter produção antiga
            reverter_producao_etapa(lote)
            RegistroProducao.objects.filter(obra=lote.obra, data=lote.data, etapa=lote.etapa.numero_etapa if lote.etapa else None).delete()
            
            # Salvar novo
            lote_atualizado = form.save()
            
            # Atualizar funcionários
            lote.funcionarios.all().delete()
            for i, func_id in enumerate(request.POST.getlist('funcionario')):
                if func_id:
                    FuncionarioLote.objects.create(
                        lote=lote,
                        funcionario_id=func_id,
                        horas_trabalhadas=Decimal(request.POST.getlist('horas_trabalhadas')[i])
                    )
            
            # Gerar nova produção
            lote.gerar_apontamentos_individuais()
            
            # Registrar histórico
            HistoricoAlteracaoEtapa.objects.create(
                obra=lote.obra, etapa=lote.etapa, tipo_alteracao='edicao',
                data_referencia=lote.data,
                descricao=f'Editado: {valores_antigos["producao_total"]} → {lote.producao_total}',
                usuario=request.user,
                dados_anteriores=valores_antigos,
                dados_novos={'producao_total': float(lote.producao_total)}
            )
            
            messages.success(request, 'Apontamento atualizado!')
            return redirect('funcionarios:apontamento_lote_detail', pk=lote.pk)
    else:
        form = ApontamentoDiarioLoteForm(instance=lote)
    
    return render(request, 'funcionarios/apontamento_lote_edit.html', {
        'form': form, 'lote': lote,
        'funcionarios_atuais': lote.funcionarios.all()
    })
```

### 4. View de Detalhes (Atualizada)

```python
@login_required
def apontamento_lote_detail(request, pk):
    lote = get_object_or_404(ApontamentoDiarioLote, pk=pk)
    
    return render(request, 'funcionarios/apontamento_lote_detail.html', {
        'lote': lote,
        'funcionarios_lote': lote.funcionarios.select_related('funcionario').all(),
        'apontamentos': ApontamentoFuncionario.objects.filter(obra=lote.obra, data=lote.data, etapa=lote.etapa),
        'producoes': RegistroProducao.objects.filter(obra=lote.obra, data=lote.data, etapa=lote.etapa.numero_etapa if lote.etapa else None),
        'historico': HistoricoAlteracaoEtapa.objects.filter(obra=lote.obra, etapa=lote.etapa, data_referencia=lote.data).order_by('-created_at')
    })
```

### 5. Templates

**Listagem - Adicionar botões:**

Em `templates/funcionarios/apontamento_lote_list.html`, na coluna Ações:

```html
<td>
    <a href="{% url 'funcionarios:apontamento_lote_detail' lote.id %}" class="btn btn-sm btn-info">
        <i class="bi bi-eye"></i>
    </a>
    <a href="{% url 'funcionarios:apontamento_lote_edit' lote.id %}" class="btn btn-sm btn-warning">
        <i class="bi bi-pencil"></i>
    </a>
    <button type="button" class="btn btn-sm btn-danger" data-bs-toggle="modal" data-bs-target="#modal-excluir-{{ lote.id }}">
        <i class="bi bi-trash"></i>
    </button>
</td>

<!-- Modal de confirmação -->
<div class="modal fade" id="modal-excluir-{{ lote.id }}">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header bg-danger text-white">
                <h5>⚠️ Confirmar Exclusão</h5>
            </div>
            <div class="modal-body">
                <p><strong>Tem certeza?</strong></p>
                <div class="alert alert-warning">
                    ⚠️ Produção será REVERTIDA e relatórios RECALCULADOS!
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                <form method="post" action="{% url 'funcionarios:apontamento_lote_delete' lote.id %}">
                    {% csrf_token %}
                    <button type="submit" class="btn btn-danger">Sim, Excluir</button>
                </form>
            </div>
        </div>
    </div>
</div>
```

**Detalhes - Histórico:**

Criar `templates/funcionarios/apontamento_lote_detail.html` com seção de histórico:

```html
<h5 class="mt-4">📜 Histórico de Alterações</h5>
{% if historico %}
    {% for h in historico %}
    <div class="card mb-2">
        <div class="card-body">
            <span class="badge bg-{{ h.tipo_alteracao == 'exclusao' and 'danger' or 'warning' }}">
                {{ h.get_tipo_alteracao_display }}
            </span>
            {{ h.descricao }} - {{ h.usuario.username }} - {{ h.created_at|date:"d/m/Y H:i" }}
        </div>
    </div>
    {% endfor %}
{% else %}
    <p class="text-muted">Nenhuma alteração registrada.</p>
{% endif %}
```

### 6. URLs

Adicionar em `apps/funcionarios/urls.py`:

```python
path('apontamento-lote/<int:pk>/editar/', views.apontamento_lote_edit, name='apontamento_lote_edit'),
path('apontamento-lote/<int:pk>/excluir/', views.apontamento_lote_delete, name='apontamento_lote_delete'),
```

### 7. Histórico na Página da Etapa

Em `apps/obras/views.py`, atualizar view da etapa:

```python
def etapa_detail(request, pk):
    # ... código existente ...
    historico = HistoricoAlteracaoEtapa.objects.filter(etapa_id=pk).order_by('-created_at')
    context['historico_alteracoes'] = historico
```

No template da etapa, adicionar:

```html
<div class="card mt-4">
    <div class="card-header">📜 Histórico de Alterações</div>
    <div class="card-body">
        <table class="table table-sm">
            <thead>
                <tr>
                    <th>Data/Hora</th>
                    <th>Tipo</th>
                    <th>Descrição</th>
                    <th>Usuário</th>
                </tr>
            </thead>
            <tbody>
                {% for h in historico_alteracoes %}
                <tr>
                    <td>{{ h.created_at|date:"d/m/Y H:i" }}</td>
                    <td><span class="badge bg-{{ h.tipo_alteracao == 'exclusao' and 'danger' or 'warning' }}">{{ h.get_tipo_alteracao_display }}</span></td>
                    <td>{{ h.descricao }}</td>
                    <td>{{ h.usuario.username }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
```

## Plano de Testes

Execute via navegador:

### Teste 1: Exclusão
1. Ir para `/funcionarios/apontamento-lote/`
2. Clicar em 🗑️ de um apontamento
3. Confirmar exclusão
4. ✅ Verificar: apontamento sumiu
5. ✅ Ir para obra/etapa: valores foram revertidos
6. ✅ Ir para `/relatorios/`: médias recalculadas
7. ✅ Ver histórico na etapa: registro de exclusão presente

### Teste 2: Edição
1. Clicar em ✏️ de um apontamento
2. Alterar valor (ex: 100 → 150 blocos)
3. Salvar
4. ✅ Verificar: novo valor na lista
5. ✅ Ir para obra/etapa: valor atualizado
6. ✅ Ir para `/relatorios/`: médias recalculadas
7. ✅ Ver histórico: registro de edição

### Teste 3: Detalhes
1. Clicar em 👁️
2. ✅ Ver funcionários
3. ✅ Ver registros de produção
4. ✅ Ver histórico
5. ✅ Botões Editar e Excluir presentes

### Teste 4: Recálculo de Médias
1. Anotar média de um pedreiro em `/funcionarios/ID/medias/`
2. Excluir um apontamento dele
3. ✅ Voltar para `/medias/`: média deve ter mudado
4. ✅ Ir para `/relatorios/`: ranking atualizado

## Checklist de Implementação

- [ ] Criar model HistoricoAlteracaoEtapa
- [ ] Criar migration e migrar
- [ ] Adicionar botões na listagem
- [ ] Criar modal de confirmação
- [ ] Implementar view de exclusão
- [ ] Implementar função reverter_producao_etapa
- [ ] Implementar view de edição
- [ ] Criar template de edição
- [ ] Atualizar view de detalhes
- [ ] Criar template de detalhes com histórico
- [ ] Adicionar histórico na página da etapa
- [ ] Adicionar URLs
- [ ] TESTAR exclusão
- [ ] TESTAR edição
- [ ] VERIFICAR relatórios recalcularam
- [ ] VERIFICAR médias atualizaram

## Notas Importantes

- Todas as operações usam `@transaction.atomic` para garantir integridade
- Exclusão SEMPRE reverte valores nas etapas antes de deletar
- Edição reverte valores antigos ANTES de aplicar novos
- Histórico é registrado em TODAS as alterações
- Recálculo é AUTOMÁTICO (Django signals ou chamadas diretas)
- Não permite valores negativos após reversão (usa `max(valor, 0)`)
