#!/usr/bin/env python
import os
import sys
import random
import datetime
from decimal import Decimal

# Setup Django environment
proj_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, proj_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from apps.funcionarios.models import Funcionario
from apps.ferramentas.models import Ferramenta
from apps.obras.models import Obra

# Optional: use Cliente names if available
try:
    from apps.clientes.models import Cliente
    CLIENTES = list(Cliente.objects.all())
except Exception:
    CLIENTES = []


def random_date(start_days_ago=3650, end_days_ago=30):
    today = datetime.date.today()
    start = today - datetime.timedelta(days=start_days_ago)
    end = today - datetime.timedelta(days=end_days_ago)
    delta = (end - start).days
    return start + datetime.timedelta(days=random.randint(0, max(0, delta)))


def ensure_unique_cpf(base, i):
    # produce 11-digit strings
    return f"{int(base):011d}{i}"[-11:]


def create_obras(target=100):
    existing = Obra.objects.count()
    to_create = max(0, target - existing)
    print(f"Obras: existing={existing}, to_create={to_create}")
    obras = list(Obra.objects.all())
    for i in range(to_create):
        idx = existing + i + 1
        cliente_name = None
        if CLIENTES:
            c = random.choice(CLIENTES)
            cliente_name = c.nome
        else:
            cliente_name = f"Cliente Teste {idx % 10}"
        o = Obra.objects.create(
            nome=f"Obra Teste {idx}",
            endereco=f"Endereço teste {idx}",
            cliente=cliente_name,
            data_inicio=random_date(3650, 365),
            data_previsao_termino=random_date(364, 30),
            status=random.choice([k for k, _ in Obra._meta.get_field('status').choices]),
            percentual_concluido=Decimal(str(random.uniform(0, 100)))
        )
        obras.append(o)
    return obras


def create_ferramentas(target=100):
    existing = Ferramenta.objects.count()
    to_create = max(0, target - existing)
    print(f"Ferramentas: existing={existing}, to_create={to_create}")
    ferramentas = list(Ferramenta.objects.all())
    categorias = [k for k, _ in Ferramenta._meta.get_field('categoria').choices]
    status_choices = [k for k, _ in Ferramenta._meta.get_field('status').choices]
    obras = list(Obra.objects.all())
    for i in range(to_create):
        idx = existing + i + 1
        codigo = f"F{idx:03d}"
        nome = f"Ferramenta {idx}"
        categoria = random.choice(categorias)
        status = random.choice(status_choices)
        obra_atual = random.choice(obras) if obras and random.random() < 0.3 else None
        f = Ferramenta.objects.create(
            codigo=codigo,
            nome=nome,
            descricao="Gerado automaticamente para testes",
            categoria=categoria,
            status=status,
            obra_atual=obra_atual,
            data_aquisicao=random_date(3650, 0),
            valor_aquisicao=Decimal(str(round(random.uniform(10, 1000), 2))),
            ativo=True
        )
        ferramentas.append(f)
    return ferramentas


def create_funcionarios(target=100):
    existing = Funcionario.objects.count()
    to_create = max(0, target - existing)
    print(f"Funcionarios: existing={existing}, to_create={to_create}")
    funcionarios = list(Funcionario.objects.all())
    funcoes = [k for k, _ in Funcionario._meta.get_field('funcao').choices]
    for i in range(to_create):
        idx = existing + i + 1
        nome = f"Funcionario Teste {idx}"
        cpf = f"{10000000000 + idx}"[-11:]
        data_nasc = random_date(20000, 8000)
        telefone = f"(11) 9{random.randint(10000000,99999999)}"
        email = f"func{idx}@example.local"
        endereco = f"Endereco teste {idx}"
        cidade = "Cidade Teste"
        estado = "SP"
        cep = f"{random.randint(10000000,99999999):08d}"
        funcao = random.choice(funcoes)
        valor_diaria = Decimal(str(round(random.uniform(80, 300), 2)))
        data_admissao = random_date(2000, 30)
        f = Funcionario.objects.create(
            nome_completo=nome,
            cpf=cpf,
            rg=f"RG{idx}",
            data_nascimento=data_nasc,
            telefone=telefone,
            email=email,
            endereco=endereco,
            cidade=cidade,
            estado=estado,
            cep=cep,
            funcao=funcao,
            valor_diaria=valor_diaria,
            data_admissao=data_admissao,
            ativo=True
        )
        funcionarios.append(f)
    return funcionarios


if __name__ == '__main__':
    print('Gerando dados de teste...')
    obras = create_obras(100)
    ferramentas = create_ferramentas(100)
    funcionarios = create_funcionarios(100)
    print('Concluído')
    print(f'Obras total: {Obra.objects.count()}')
    print(f'Ferramentas total: {Ferramenta.objects.count()}')
    print(f'Funcionarios total: {Funcionario.objects.count()}')
