# 📊 Documentação Técnica - Models

## Visão Geral dos Apps e Models

O sistema é dividido em 5 apps principais, cada um com responsabilidades específicas.

---

## 🏗️ APP: OBRAS

### Model: Obra
**Propósito**: Armazena informações principais de cada obra

**Campos principais**:
- `nome` (CharField): Nome da obra
- `endereco` (TextField): Endereço completo
- `cliente` (CharField): Nome do cliente
- `data_inicio` (DateField): Quando a obra começou
- `status` (CharField): planejamento, em_andamento, pausada, concluida, cancelada
- `percentual_concluido` (DecimalField): Auto-calculado pelas etapas

**Métodos importantes**:
- `calcular_percentual()`: Calcula percentual baseado nas etapas concluídas

**Relacionamentos**:
- OneToMany com Etapa
- OneToMany com RegistroFiscalizacao
- OneToMany com ApontamentoFuncionario
- OneToMany com Ferramenta (obra_atual)

---

### Model: Etapa
**Propósito**: Representa uma das 5 etapas principais da obra

**Campos principais**:
- `obra` (ForeignKey): Obra a que pertence
- `numero_etapa` (IntegerField): 1 a 5
- `percentual_valor` (DecimalField): Valor da etapa (29.9, 45, 70, 84, 95)
- `data_inicio` / `data_termino` (DateField)
- `concluida` (BooleanField)

**Regras**:
- Percentual preenchido automaticamente baseado no número
- Unique together: obra + numero_etapa (não pode duplicar)

**Relacionamentos**:
- ManyToOne com Obra
- OneToOne com Etapa1Fundacao, Etapa2Estrutura, etc.

---

### Models: Etapa1Fundacao, Etapa2Estrutura, Etapa3Instalacoes, Etapa4Acabamentos, Etapa5Finalizacao

**Propósito**: Detalhamento específico de cada etapa

#### Etapa 1 - Fundação (29.9%)
- `limpeza_terreno` (Boolean)
- `instalacao_energia_agua` (Boolean)
- `marcacao_escavacao_dias` (Integer)
- `locacao_ferragem_dias` (Integer)
- `alicerce_percentual` (Decimal 0-100)
- `aterro_contrapiso_dias` (Integer)
- `parede_7fiadas_blocos` (Integer)
- `fiadas_respaldo_dias` (Integer)

#### Etapa 2 - Estrutura (45%)
- `montagem_laje_dias` (Integer)
- `platibanda_blocos` (Integer)
- `cobertura_dias` (Integer)

#### Etapa 3 - Instalações (70%)
- `reboco_externo_m2` (Decimal)
- `reboco_interno_m2` (Decimal)
- `instalacao_portais` (Boolean)
- `agua_fria` (Boolean)
- `esgoto` (Boolean)
- `fluvial` (Boolean)

#### Etapa 4 - Acabamentos (84%)
- `portas_janelas` (Boolean)
- `pintura_externa_1demao_dias` (Integer)
- `pintura_interna_1demao_dias` (Integer)
- `assentamento_piso_dias` (Integer)

#### Etapa 5 - Finalização (95%)
- `pintura_externa_2demao_dias` (Integer)
- `pintura_interna_2demao_dias` (Integer)
- `loucas_metais` (Boolean)
- `eletrica` (Boolean)

---

## 📸 APP: FISCALIZACAO

### Model: RegistroFiscalizacao
**Propósito**: Registro diário de fiscalização da obra

**Campos principais**:
- `obra` (ForeignKey): Obra fiscalizada
- `fiscal` (ForeignKey User): Quem fez a fiscalização
- `data_fiscalizacao` (DateField): Data da vistoria
- `clima` (CharField): sol, chuva, nublado
- `lixo` (CharField): nao_ha, pouco, muito
- `placa_instalada` (Boolean)
- `houve_ociosidade` (Boolean)
- `observacao_ociosidade` (TextField)
- `houve_retrabalho` (Boolean)
- `motivo_retrabalho` (TextField)

**Métodos importantes**:
- `validar_fotos()`: Verifica se há mínimo 6 fotos

**Regras**:
- Unique together: obra + data_fiscalizacao (1 fiscalização por obra por dia)

**Relacionamentos**:
- ManyToOne com Obra
- ManyToOne com User (fiscal)
- OneToMany com FotoFiscalizacao

---

### Model: FotoFiscalizacao
**Propósito**: Fotos da fiscalização (mínimo 6)

**Campos**:
- `fiscalizacao` (ForeignKey)
- `foto` (ImageField): Upload para /fiscalizacao/YYYY/MM/DD/
- `descricao` (CharField)
- `ordem` (Integer): Ordem de exibição

---

## 👷 APP: FUNCIONARIOS

### Model: Funcionario
**Propósito**: Cadastro completo de pedreiros e serventes

**Campos principais**:
- `nome_completo` (CharField)
- `cpf` (CharField unique)
- `data_nascimento` (DateField)
- `telefone` (CharField)
- `endereco` (TextField)
- `cidade`, `estado`, `cep`
- `funcao` (CharField): pedreiro ou servente
- `valor_diaria` (DecimalField): R$ da diária
- `foto` (ImageField)
- `ativo` (Boolean)
- `data_admissao` / `data_demissao` (DateField)

**Métodos importantes**:
- `inativar(motivo)`: Inativa funcionário

**Relacionamentos**:
- OneToMany com ApontamentoFuncionario
- OneToMany com FechamentoSemanal

---

### Model: ApontamentoFuncionario
**Propósito**: Registro diário de trabalho

**Campos**:
- `funcionario` (ForeignKey)
- `obra` (ForeignKey)
- `data` (DateField)
- `valor_diaria` (Decimal): Auto-preenchido do funcionário

**Regras**:
- Unique together: funcionario + obra + data (não pode duplicar)
- Valor diária preenchido automaticamente

---

### Model: FechamentoSemanal
**Propósito**: Fechamento de pagamento semanal

**Campos**:
- `funcionario` (ForeignKey)
- `data_inicio` / `data_fim` (DateField)
- `total_dias` (Integer)
- `total_valor` (Decimal)
- `status` (CharField): aberto, fechado, pago
- `data_pagamento` (DateField)

**Métodos importantes**:
- `calcular_totais()`: Soma apontamentos da semana

**Regras**:
- Unique together: funcionario + data_inicio + data_fim

---

## 🔧 APP: FERRAMENTAS

### Model: Ferramenta
**Propósito**: Cadastro de ferramentas

**Campos**:
- `codigo` (CharField unique): Código identificador
- `nome` (CharField)
- `categoria` (CharField): manual, eletrica, medicao, seguranca, outros
- `status` (CharField): deposito, em_obra, manutencao, perdida, descartada
- `obra_atual` (ForeignKey): Onde está agora
- `foto` (ImageField)

**Relacionamentos**:
- OneToMany com MovimentacaoFerramenta

---

### Model: MovimentacaoFerramenta
**Propósito**: Histórico de movimentações

**Campos**:
- `ferramenta` (ForeignKey)
- `tipo` (CharField): entrada_deposito, saida_obra, transferencia, etc.
- `obra_origem` / `obra_destino` (ForeignKey)
- `responsavel` (ForeignKey User)
- `data_movimentacao` (DateTimeField auto)

**Métodos importantes**:
- `atualizar_ferramenta()`: Atualiza status da ferramenta após movimentação

---

### Model: ConferenciaFerramenta
**Propósito**: Conferência diária pelo fiscal

**Campos**:
- `obra` (ForeignKey)
- `fiscal` (ForeignKey User)
- `data_conferencia` (DateField)

**Regras**:
- Unique together: obra + data_conferencia

**Relacionamentos**:
- OneToMany com ItemConferencia

---

### Model: ItemConferencia
**Propósito**: Itens conferidos

**Campos**:
- `conferencia` (ForeignKey)
- `ferramenta` (ForeignKey)
- `status` (CharField): ok, ausente, danificada

**Regras**:
- Unique together: conferencia + ferramenta

---

## 📊 APP: ANALYTICS

**Não possui models próprios**. Usa queries nos outros apps.

### Services disponíveis (AnalyticsService):

#### `ranking_pedreiros_por_etapa(numero_etapa, top=3, bottom=3)`
Retorna melhores e piores pedreiros em uma etapa específica

#### `media_dias_por_etapa()`
Média de dias para cada uma das 5 etapas

#### `rendimento_individual_pedreiro(pedreiro_id)`
Estatísticas detalhadas de um pedreiro

#### `custo_mao_obra_por_obra(obra_id, data_inicio, data_fim)`
Custos de mão de obra por obra

#### `historico_funcionario_semanal(funcionario_id, semanas=4)`
Histórico semanal de trabalho

#### `dashboard_geral()`
Métricas consolidadas do sistema

---

## 🔗 Diagrama de Relacionamentos

```
Obra
├── Etapa (OneToMany)
│   ├── Etapa1Fundacao (OneToOne)
│   ├── Etapa2Estrutura (OneToOne)
│   ├── Etapa3Instalacoes (OneToOne)
│   ├── Etapa4Acabamentos (OneToOne)
│   └── Etapa5Finalizacao (OneToOne)
├── RegistroFiscalizacao (OneToMany)
│   └── FotoFiscalizacao (OneToMany)
├── ApontamentoFuncionario (OneToMany)
├── ConferenciaFerramenta (OneToMany)
│   └── ItemConferencia (OneToMany)
└── Ferramenta (via obra_atual)

Funcionario
├── ApontamentoFuncionario (OneToMany)
└── FechamentoSemanal (OneToMany)

Ferramenta
├── MovimentacaoFerramenta (OneToMany)
└── ItemConferencia (OneToMany)

User (Django)
├── RegistroFiscalizacao (via fiscal)
├── MovimentacaoFerramenta (via responsavel)
└── ConferenciaFerramenta (via fiscal)
```

---

## 💾 Migrations

Para criar as tabelas no banco:

```bash
python manage.py makemigrations obras
python manage.py makemigrations fiscalizacao
python manage.py makemigrations funcionarios
python manage.py makemigrations ferramentas
python manage.py makemigrations analytics

python manage.py migrate
```

---

## 📝 Notas de Implementação

1. **Auto-cálculos**: Vários campos são preenchidos automaticamente (percentuais, valores de diária)
2. **Unique Together**: Várias combinações únicas para evitar duplicatas
3. **Soft Delete**: Funcionários e ferramentas usam campo `ativo` ao invés de delete
4. **Auditoria**: Todos models têm `created_at` e `updated_at`
5. **Choices**: Uso extensivo de choices para garantir consistência
6. **Validators**: MinValueValidator, MaxValueValidator para ranges

---

**Última atualização**: Sistema base criado
