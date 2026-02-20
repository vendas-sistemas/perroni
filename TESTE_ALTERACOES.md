# 🧪 TESTE DAS ALTERAÇÕES - Apontamento de Obras

## ✅ Alterações Implementadas:

### 1. **Exibição do Progresso Atual**
   - Campos numéricos agora mostram o progresso em alert azul
   - Input fica vazio para digitar apenas o valor do dia
   
### 2. **Campo "Possui Placa" Automático**
   - Marca automaticamente baseado no último apontamento da obra
   - Atualiza ao trocar de obra

### 3. **Help Text Atualizado**
   - "Quanto foi executado HOJE (será somado ao total)"

---

## 🚀 COMO TESTAR:

### Passo 1: Limpar Cache do Navegador
**IMPORTANTE:** Pressione `Ctrl + Shift + Delete` e limpe:
- ✅ Cache/Imagens em cache
- ✅ Tempo: Última hora ou tudo

Ou simplesmente: **Ctrl + F5** (recarregar forçado)

---

### Passo 2: Reiniciar o Servidor Django

```powershell
# Pare qualquer servidor rodando (Ctrl+C no terminal)
# Depois inicie novamente:
python manage.py runserver
```

---

### Passo 3: Testar Progresso Atual

1. Acesse: http://127.0.0.1:8000/funcionarios/apontamento-lote/criar/

2. Selecione uma **Obra que já tem progresso**:
   - Ex: Obra com 30% alicerce, 150 blocos

3. Selecione a **Etapa 1 - Fundação**

4. Verifique se aparece:
   ```
   Levantar Alicerce (%)
   ℹ️ Progresso atual: 30.00 %
   [_____] ← Campo vazio
   Quanto foi executado HOJE (será somado ao total)
   ```

5. Digite: **20** (apenas o que foi feito HOJE)

6. Salve

7. Verifique no banco se o total é: **50%** (30 + 20) ✅

---

### Passo 4: Testar "Possui Placa"

**Teste A: Primeira vez na obra**

1. Selecione uma obra nova (sem apontamentos)
2. ❌ "Possui Placa" deve vir **DESMARCADO**
3. ✅ MARQUE o checkbox "Possui Placa"
4. Salve o apontamento

**Teste B: Segunda vez na mesma obra**

1. Crie NOVO apontamento na MESMA obra
2. ✅ "Possui Placa" deve vir **MARCADO automaticamente**
3. Salve (pode manter marcado ou desmarcar)

**Teste C: Trocar de obra no mesmo formulário**

1. Selecione Obra A (com placa marcada nos apontamentos)
2. ✅ Checkbox deve marcar automaticamente
3. Troque para Obra B (sem placa marcada)
4. ❌ Checkbox deve desmarcar automaticamente
5. Volte para Obra A
6. ✅ Checkbox deve marcar novamente

---

### Passo 5: Testar Console do Navegador

1. Pressione **F12** (DevTools)
2. Vá na aba **Console**
3. Selecione uma obra
4. Deve aparecer no console:
   ```
   Possui Placa carregado: true
   ```
   ou
   ```
   Possui Placa carregado: false
   ```

Se não aparecer, pode ter problema com a API!

---

## 🔍 DEBUGGING:

### Se "Possui Placa" não funcionar:

**Teste manual da API:**

1. Abra o navegador em:
   ```
   http://127.0.0.1:8000/funcionarios/api/obra-possui-placa/?obra_id=1
   ```
   (mude o ID da obra)

2. Deve retornar:
   ```json
   {"possui_placa": true}
   ```
   ou
   ```json
   {"possui_placa": false}
   ```

---

### Se valores não aparecerem:

**Teste manual da API de campos:**

1. Abra:
   ```
   http://127.0.0.1:8000/funcionarios/api/campos-etapa/?etapa_id=1
   ```
   (mude o ID da etapa)

2. Procure no JSON:
   ```json
   {
     "nome": "levantar_alicerce_percentual",
     "valor_atual": "",
     "valor_atual_display": "30.00"
   }
   ```

3. `valor_atual_display` deve ter o valor, `valor_atual` deve estar vazio

---

## 📝 LOGS ÚTEIS:

Se houver problemas, verifique o console do navegador:

```javascript
// Deve aparecer ao selecionar etapa:
Carregando campos da etapa: 1
Dados recebidos: {etapa_id: "1", campos: [...]}

// Deve aparecer ao selecionar obra:
Possui Placa carregado: true
```

---

## ✅ CHECKLIST FINAL:

- [ ] Cache do navegador limpo
- [ ] Servidor Django reiniciado
- [ ] Progresso atual aparece em alert azul
- [ ] Campo de input vem vazio
- [ ] Valor digitado é somado corretamente ao total
- [ ] "Possui Placa" marca automaticamente na segunda vez
- [ ] "Possui Placa" atualiza ao trocar de obra
- [ ] Console não mostra erros JavaScript

---

**Se tudo funcionar:** ✅ Sistema pronto para uso!

**Se algo não funcionar:** 
1. Verifique console do navegador (F12)
2. Verifique terminal do Django (erros Python)
3. Teste as APIs manualmente (URLs acima)
