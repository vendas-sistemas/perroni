from django import forms
from .models import Ferramenta
from .models import MovimentacaoFerramenta, ConferenciaFerramenta, ItemConferencia
from django.utils import timezone
from django.forms import ModelForm
import datetime


class FerramentaForm(forms.ModelForm):
    class Meta:
        model = Ferramenta
        fields = [
            'codigo', 'nome', 'descricao', 'categoria',
            'data_aquisicao', 'valor_aquisicao', 'foto', 'ativo'
        ]
        widgets = {
            'data_aquisicao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'valor_aquisicao': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow leaving `codigo` empty at creation; the view will auto-generate one if omitted.
        if 'codigo' in self.fields:
            self.fields['codigo'].required = False
            self.fields['codigo'].widget.attrs.setdefault('placeholder', 'Opcional — será gerado automaticamente se vazio')
        for name, field in self.fields.items():
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                existing = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = (existing + ' form-select').strip()
            elif isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs['class'] = 'form-control'
            else:
                existing = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = (existing + ' form-control').strip()
    
    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        # If updating existing ferramenta and codigo left blank, keep original codigo
        if not codigo and self.instance and self.instance.pk:
            return getattr(self.instance, 'codigo', '')
        # return as-is (may be empty on create; view will generate)
        return codigo


class MovimentacaoForm(ModelForm):
    class Meta:
        model = MovimentacaoFerramenta
        fields = ['ferramenta', 'tipo', 'obra_origem', 'obra_destino', 'observacoes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ferramenta'].queryset = Ferramenta.objects.filter(ativo=True).order_by('nome')
        for name, field in self.fields.items():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing + ' form-control').strip()

    def clean(self):
        cleaned = super().clean()
        ferramenta = cleaned.get('ferramenta')
        tipo = cleaned.get('tipo')
        obra_origem = cleaned.get('obra_origem')
        obra_destino = cleaned.get('obra_destino')

        if not ferramenta or not tipo:
            return cleaned

        obra_atual = ferramenta.obra_atual
        origem_padrao = obra_atual.nome if obra_atual else 'Depósito'
        origem_auto = origem_padrao
        destino_auto = ''

        if tipo == 'saida_obra':
            if not obra_destino:
                self.add_error('obra_destino', 'Informe a obra de destino para saída para obra.')
            cleaned['obra_origem'] = obra_atual
            origem_auto = origem_padrao
            destino_auto = obra_destino.nome if obra_destino else ''

        elif tipo == 'transferencia':
            if not obra_origem:
                obra_origem = obra_atual
                cleaned['obra_origem'] = obra_origem
            if not obra_origem:
                self.add_error('obra_origem', 'Informe a obra de origem da transferência.')
            if not obra_destino:
                self.add_error('obra_destino', 'Informe a obra de destino da transferência.')
            if obra_origem and obra_destino and obra_origem == obra_destino:
                self.add_error('obra_destino', 'A obra de destino deve ser diferente da origem.')
            origem_auto = obra_origem.nome if obra_origem else ''
            destino_auto = obra_destino.nome if obra_destino else ''

        elif tipo in ['retorno_deposito', 'entrada_deposito']:
            cleaned['obra_origem'] = obra_atual
            cleaned['obra_destino'] = None
            origem_auto = origem_padrao
            destino_auto = 'Depósito'

        elif tipo == 'manutencao':
            cleaned['obra_origem'] = obra_atual
            cleaned['obra_destino'] = None
            origem_auto = origem_padrao
            destino_auto = 'Manutenção'

        elif tipo == 'perda':
            cleaned['obra_origem'] = obra_atual
            cleaned['obra_destino'] = None
            origem_auto = origem_padrao
            destino_auto = 'Perda/Extravio'

        elif tipo == 'descarte':
            cleaned['obra_origem'] = obra_atual
            cleaned['obra_destino'] = None
            origem_auto = origem_padrao
            destino_auto = 'Descarte'

        self._origem_auto = origem_auto
        self._destino_auto = destino_auto

        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.origem = getattr(self, '_origem_auto', instance.origem)
        instance.destino = getattr(self, '_destino_auto', instance.destino)
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ConferenciaForm(ModelForm):
    class Meta:
        model = ConferenciaFerramenta
        # Do not expose `data_conferencia` to users; it will be set automatically
        fields = ['obra']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')


class ItemConferenciaForm(ModelForm):
    obra_destino = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label='Obra destino (se transferida)'
    )

    class Meta:
        model = ItemConferencia
        # Do not include the parent FK `conferencia` in the form used by the
        # inline formset — the formset/parent instance will set this automatically.
        fields = ['ferramenta', 'status', 'observacoes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault('class', 'form-control')

        from apps.obras.models import Obra
        self.fields['obra_destino'].queryset = Obra.objects.filter(ativo=True).order_by('nome')
        self.fields['obra_destino'].widget.attrs.setdefault('class', 'form-control')

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get('status')
        obra_destino = cleaned.get('obra_destino')

        if status == 'transferida' and not obra_destino:
            self.add_error('obra_destino', 'Informe a obra destino para transferência.')

        if status != 'transferida' and obra_destino:
            cleaned['obra_destino'] = None

        return cleaned
