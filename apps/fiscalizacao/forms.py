from django import forms
from django.forms.widgets import ClearableFileInput
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit, Row, Column
from django.utils import timezone
import datetime

from .models import RegistroFiscalizacao, FotoFiscalizacao


# Custom widget to allow multiple file selection with ClearableFileInput
class MultipleClearableFileInput(ClearableFileInput):
    allow_multiple_selected = True

    def value_from_datadict(self, data, files, name):
        if name in files:
            return files.getlist(name)
        return super().value_from_datadict(data, files, name)


class RegistroFiscalizacaoForm(forms.ModelForm):
    fotos = forms.FileField(
        widget=MultipleClearableFileInput(attrs={
            'multiple': True,
            'accept': 'image/*',
            'capture': 'environment'
        }),
        required=False,
        help_text='(Opcional) Envie até 10 fotos. Use a câmera do celular para fotos diretas.'
    )

    class Meta:
        model = RegistroFiscalizacao
        fields = [
            'obra', 'fiscal', 'data_fiscalizacao', 'clima', 'lixo',
            'placa_instalada', 'houve_ociosidade', 'observacao_ociosidade',
            'houve_retrabalho', 'motivo_retrabalho', 'observacoes'
        ]
        widgets = {
            'data_fiscalizacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observacao_ociosidade': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'motivo_retrabalho': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'obra': forms.Select(attrs={'class': 'form-select'}),
            'fiscal': forms.Select(attrs={'class': 'form-select'}),
            'clima': forms.Select(attrs={'class': 'form-select'}),
            'lixo': forms.Select(attrs={'class': 'form-select'}),
            'placa_instalada': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'houve_ociosidade': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'houve_retrabalho': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.template_pack = 'bootstrap5'
        self.helper.layout = Layout(
            Row(Column(Field('obra'), css_class='col-12 col-md-6'), Column(Field('fiscal'), css_class='col-12 col-md-6')),
            Row(Column(Field('data_fiscalizacao'), css_class='col-12 col-md-4'), Column(Field('clima'), css_class='col-6 col-md-4'), Column(Field('lixo'), css_class='col-6 col-md-4')),
            Row(Column(Field('placa_instalada'), css_class='col-6'), Column(Field('houve_ociosidade'), css_class='col-6')),
            Field('observacao_ociosidade'),
            Field('houve_retrabalho'),
            Field('motivo_retrabalho'),
            Field('observacoes'),
            Field('fotos'),
            Submit('submit', 'Salvar Fiscalização', css_class='btn btn-primary')
        )

    def clean_fotos(self):
        # Attempt to get uploaded files from the form's files attribute
        files = []
        try:
            files = self.files.getlist('fotos')
        except Exception:
            # Fallback: no files available
            files = []

        # Optional: limit max files
        if len(files) > 10:
            raise forms.ValidationError('Envie no máximo 10 fotos.')

        # Basic validation on file types/sizes (optional)
        for f in files:
            if hasattr(f, 'content_type') and not f.content_type.startswith('image/'):
                raise forms.ValidationError('Apenas arquivos de imagem são permitidos.')
            if hasattr(f, 'size') and f.size > 10 * 1024 * 1024:  # 10MB
                raise forms.ValidationError('Cada imagem deve ter no máximo 10MB.')

        return files

    def clean(self):
        cleaned = super().clean()
        # Ensure data consistency: if houve_ociosidade true, observacao required
        if cleaned.get('houve_ociosidade') and not cleaned.get('observacao_ociosidade'):
            self.add_error('observacao_ociosidade', 'Descreva a ociosidade quando aplicável.')
        if cleaned.get('houve_retrabalho') and not cleaned.get('motivo_retrabalho'):
            self.add_error('motivo_retrabalho', 'Descreva o motivo do retrabalho quando aplicável.')
        return cleaned

    def save(self, commit=True, files=None):
        """Save the RegistroFiscalizacao and associated FotoFiscalizacao files.

        - `files` optional list of uploaded files; if None, will use self.files.
        """
        # Ensure data_fiscalizacao includes current time when user provided only a date
        df = self.cleaned_data.get('data_fiscalizacao')
        if df is not None:
            # If a date was provided without time, combine with current time
            if isinstance(df, datetime.date) and not isinstance(df, datetime.datetime):
                now = timezone.localtime()
                combined = datetime.datetime.combine(df, now.timetz())
                # set timezone-aware datetime if settings use timezone
                if timezone.is_naive(combined):
                    combined = timezone.make_aware(combined, timezone.get_current_timezone())
                self.instance.data_fiscalizacao = combined

        instance = super().save(commit=commit)

        # Determine files to save
        if files is None:
            try:
                files = self.files.getlist('fotos')
            except Exception:
                files = []

        # Persist photos
        for idx, f in enumerate(files[:10]):
            FotoFiscalizacao.objects.create(
                fiscalizacao=instance,
                foto=f,
                ordem=idx + 1
            )

        # Ensure data_fiscalizacao matches the created timestamp so multiple
        # fiscalizações can exist for the same obra on the same day but at
        # different times. `created_at` is set by auto_now_add on save, so
        # after saving we copy it into `data_fiscalizacao` for exact match.
        if commit:
            try:
                instance.data_fiscalizacao = instance.created_at
                instance.save(update_fields=['data_fiscalizacao'])
            except Exception:
                # If for any reason copying fails, ignore and keep existing value
                pass

        return instance
