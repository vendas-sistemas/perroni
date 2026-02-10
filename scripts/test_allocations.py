#!/usr/bin/env python
import os, sys
from decimal import Decimal
import datetime

proj_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, proj_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from apps.obras.models import Obra, Etapa, Etapa3Instalacoes
from apps.funcionarios.models import Funcionario, ApontamentoFuncionario

# Cleanup any previous test obra
Obra.objects.filter(nome__icontains='Obra Alocacao Test').delete()

# Create obra
obra = Obra.objects.create(
    nome='Obra Alocacao Test',
    endereco='Endereco teste',
    data_inicio=datetime.date.today() - datetime.timedelta(days=7),
    data_previsao_termino=datetime.date.today() + datetime.timedelta(days=30),
    status='em_andamento',
)

# Create etapa 3 for this obra
etapa = Etapa.objects.create(obra=obra, numero_etapa=3, percentual_valor=Etapa.PERCENTUAIS_ETAPA.get(3))
# set etapa period to include our apontamentos
etapa.data_inicio = datetime.date.today() - datetime.timedelta(days=7)
etapa.data_termino = datetime.date.today() + datetime.timedelta(days=1)
etapa.save()

# Create Etapa3Instalacoes detail
detalhe = Etapa3Instalacoes.objects.create(etapa=etapa, reboco_externo_m2=Decimal('20.00'), reboco_interno_m2=Decimal('0.00'))

# Create two funcionarios
f1, created1 = Funcionario.objects.get_or_create(
    cpf='00000000001',
    defaults={
        'nome_completo': 'Pedreiro Teste 1',
        'data_nascimento': datetime.date(1990,1,1),
        'telefone': '(11)900000001',
        'endereco': 'Rua A',
        'cidade': 'Cidade',
        'estado': 'SP',
        'cep': '00000000',
        'funcao': 'pedreiro',
        'valor_diaria': Decimal('100.00'),
        'data_admissao': datetime.date.today()-datetime.timedelta(days=365)
    }
)
f2, created2 = Funcionario.objects.get_or_create(
    cpf='00000000002',
    defaults={
        'nome_completo': 'Pedreiro Teste 2',
        'data_nascimento': datetime.date(1991,1,1),
        'telefone': '(11)900000002',
        'endereco': 'Rua B',
        'cidade': 'Cidade',
        'estado': 'SP',
        'cep': '00000000',
        'funcao': 'pedreiro',
        'valor_diaria': Decimal('100.00'),
        'data_admissao': datetime.date.today()-datetime.timedelta(days=300)
    }
)

# Create apontamentos for both within etapa period
data_aponto = datetime.date.today() - datetime.timedelta(days=3)
ApontamentoFuncionario.objects.create(funcionario=f1, obra=obra, data=data_aponto, valor_diaria=f1.valor_diaria)
ApontamentoFuncionario.objects.create(funcionario=f2, obra=obra, data=data_aponto, valor_diaria=f2.valor_diaria)

# Call allocation
alloc = detalhe.allocation_per_worker('reboco_externo_m2')

import json
print('=== Allocation result ===')
print(json.dumps(alloc, indent=2, ensure_ascii=False, default=str))

print('\nDetalhe breakdown names:')
for b in alloc.get('breakdown', []):
    print(b)

print('\nTeste concluído.')
