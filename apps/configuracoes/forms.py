from django import forms
from django.contrib.auth.models import Group, User

from apps.configuracoes.models import GroupAreaPermission
from apps.funcionarios.models import UserProfile
from config.access_control import ACTION_KEYS, AREA_KEYS


class GroupManageForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']
        labels = {'name': 'Nome do Grupo'}
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for area in AREA_KEYS:
            for action in ACTION_KEYS:
                key = f'{area}_{action}'
                self.fields[key] = forms.BooleanField(required=False)

        if self.instance and self.instance.pk:
            existing = {
                p.area: p for p in GroupAreaPermission.objects.filter(group=self.instance)
            }
            for area in AREA_KEYS:
                perm = existing.get(area)
                if not perm:
                    continue
                self.initial[f'{area}_view'] = perm.can_view
                self.initial[f'{area}_create'] = perm.can_create
                self.initial[f'{area}_edit'] = perm.can_edit
                self.initial[f'{area}_delete'] = perm.can_delete

    def save_permissions(self):
        group = self.instance
        for area in AREA_KEYS:
            perm, _ = GroupAreaPermission.objects.get_or_create(group=group, area=area)
            perm.can_view = bool(self.cleaned_data.get(f'{area}_view'))
            perm.can_create = bool(self.cleaned_data.get(f'{area}_create'))
            perm.can_edit = bool(self.cleaned_data.get(f'{area}_edit'))
            perm.can_delete = bool(self.cleaned_data.get(f'{area}_delete'))
            perm.save()


class UserManageForm(forms.ModelForm):
    nome = forms.CharField(label='Nome', max_length=150)
    telefone = forms.CharField(label='Telefone', max_length=30, required=False)
    endereco = forms.CharField(
        label='Endereço',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
    )
    cargo = forms.CharField(label='Cargo', max_length=100, required=False)
    password = forms.CharField(
        label='Senha',
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Preencha para definir/alterar a senha.',
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'is_active', 'groups']
        labels = {
            'username': 'Usuário (login)',
            'email': 'E-mail',
            'is_active': 'Ativo',
            'groups': 'Grupos',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'groups': forms.SelectMultiple(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['groups'].queryset = Group.objects.order_by('name')
        self.fields['nome'].widget.attrs.update({'class': 'form-control'})
        self.fields['telefone'].widget.attrs.update({'class': 'form-control'})
        self.fields['cargo'].widget.attrs.update({'class': 'form-control'})
        if self.instance and self.instance.pk:
            self.initial['nome'] = self.instance.get_full_name() or self.instance.first_name
            profile = getattr(self.instance, 'profile', None)
            if profile:
                self.initial['telefone'] = profile.telefone
                self.initial['endereco'] = profile.endereco
                self.initial['cargo'] = profile.cargo

    def clean_password(self):
        password = (self.cleaned_data.get('password') or '').strip()
        if not self.instance.pk and not password:
            raise forms.ValidationError('Informe uma senha para o novo usuário.')
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        nome = (self.cleaned_data.get('nome') or '').strip()
        if nome:
            parts = nome.split(' ', 1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ''

        password = (self.cleaned_data.get('password') or '').strip()
        if password:
            user.set_password(password)

        if commit:
            user.save()
            self.save_m2m()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.telefone = self.cleaned_data.get('telefone') or ''
            profile.endereco = self.cleaned_data.get('endereco') or ''
            profile.cargo = self.cleaned_data.get('cargo') or ''
            profile.save()

        return user
