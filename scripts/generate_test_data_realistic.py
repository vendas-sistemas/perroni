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
from apps.obras.models import Obra, Etapa
from apps.clientes.models import Cliente
from django.db import transaction

# Pools for realistic names
FIRST_NAMES = ['João', 'Maria', 'Pedro', 'Ana', 'Carlos', 'Paula', 'Rafael', 'Carolina', 'Lucas', 'Mariana', 'Gustavo', 'Fernanda', 'Bruno', 'Patrícia', 'André', 'Juliana', 'Gabriel', 'Camila', 'Thiago', 'Aline']
LAST_NAMES = ['Silva', 'Santos', 'Oliveira', 'Souza', 'Pereira', 'Costa', 'Rodrigues', 'Almeida', 'Nascimento', 'Lima', 'Araújo', 'Fernandes', 'Gomes', 'Ribeiro', 'Martins']
TOOL_NAMES = ['Alicate', 'Betoneira', 'Furadeira', 'Serra Circular', 'Marreta', 'Trena', 'Nível', 'Esquadro', 'Parafusadeira', 'Lixadeira', 'Martelo', 'Chave de Fenda', 'Chave Inglesa', 'Nível Laser', 'Cortador de Piso', 'Compactador', 'Carreta', 'Carrinho de Mão', 'Escada', 'Talhadeira']
OBRA_PREFIXES = ['Residencial', 'Comercial', 'Condomínio', 'Prédio', 'Edifício', 'Obra']
CLIENTES = ['Construtora Alfa', 'Construtora Beta', 'Grupo Nova', 'Empreendimentos Delta', 'Pereira & Filhos', 'Inova Construções', 'Moura Engenharia']


def random_date(start_days_ago=3650, end_days_ago=30):
    today = datetime.date.today()
    start = today - datetime.timedelta(days=start_days_ago)
    end = today - datetime.timedelta(days=end_days_ago)
    delta = (end - start).days
    return start + datetime.timedelta(days=random.randint(0, max(0, delta)))


def unique_cpf(existing_cpfs):
    while True:
        n = random.randint(10**10, 10**11 - 1)
        s = f"{n:011d}"
        if s not in existing_cpfs:
            existing_cpfs.add(s)
            return s


def clean_previous_generated():
    # Remove previously generated records identified by name patterns / description
    # For safety, only remove entries that match the generator markers used previously
    print('Cleaning previously generated test data (matching "Teste" or auto-generated descriptors)...')
    # Obras with name starting with 'Obra Teste' or 'Residencial ' patterns created earlier: remove 'Obra Teste' only
    Obra.objects.filter(nome__icontains='Obra Teste').delete()
    # Also remove obras created by this script (with numbered patterns)
    for prefix in OBRA_PREFIXES:
        Obra.objects.filter(nome__startswith=prefix).delete()
    # Funcionarios with name containing 'Funcionario Teste'
    Funcionario.objects.filter(nome_completo__icontains='Funcionario Teste').delete()
    # Ferramentas with description marker or code pattern TF####
    Ferramenta.objects.filter(descricao__icontains='Gerado automaticamente').delete()
    Ferramenta.objects.filter(codigo__startswith='TF').delete()
    print('Cleanup done.')


def create_obras(n=100):
    print('Creating obras...')
    created = []
    clientes = list(Cliente.objects.all())
    for i in range(1, n+1):
        nome = f"{random.choice(OBRA_PREFIXES)} {random.choice(['Bela Vista', 'Jardim das Flores', 'Nova Era', 'Quinta Real', 'Vale Verde', 'Centro Comercial'])} {i:03d}"
        # choose a Cliente instance if any exist
        cliente = random.choice(clientes) if clientes else None
        endereco = f"Rua {random.choice(['A', 'B', 'C', 'D', 'E'])}, {random.randint(10,999)} - Bairro {random.choice(['Centro','Jardim','Vila'])}"
        data_inicio = random_date(3650, 365)
        data_previsao_termino = data_inicio + datetime.timedelta(days=random.randint(90, 720))
        status = random.choice([k for k, _ in Obra._meta.get_field('status').choices])
        percentual = round(random.uniform(0, 100), 2)
        o = Obra.objects.create(
            nome=nome,
            endereco=endereco,
            cliente=cliente,
            data_inicio=data_inicio,
            data_previsao_termino=data_previsao_termino,
            status=status,
            percentual_concluido=Decimal(str(percentual)),
            ativo=True
        )
        # Criar 5 etapas para cada obra
        for num, _label in Etapa.ETAPA_CHOICES:
            Etapa.objects.create(
                obra=o,
                numero_etapa=num,
                percentual_valor=Etapa.PERCENTUAIS_ETAPA.get(num)
            )
        created.append(o)
    print(f'Created {len(created)} obras')
    return created


def create_ferramentas(n=100):
    print('Creating ferramentas...')
    created = []
    categorias = [k for k, _ in Ferramenta._meta.get_field('categoria').choices]
    status_choices = [k for k, _ in Ferramenta._meta.get_field('status').choices]
    obras = list(Obra.objects.all())
    # ensure we can produce unique codes
    base = 1000
    for i in range(1, n+1):
        nome_base = random.choice(TOOL_NAMES)
        nome = f"{nome_base} {i:03d}"
        codigo = f"TF{i:04d}"
        categoria = random.choice(categorias)
        status = random.choice(status_choices)
        obra_atual = random.choice(obras) if obras and random.random() < 0.4 else None
        f = Ferramenta.objects.create(
            codigo=codigo,
            nome=nome,
            descricao='Gerado automaticamente (realistic names)',
            categoria=categoria,
            status=status,
            obra_atual=obra_atual,
            data_aquisicao=random_date(3650, 0),
            valor_aquisicao=Decimal(str(round(random.uniform(20, 2000), 2))),
            ativo=True
        )
        created.append(f)
    print(f'Created {len(created)} ferramentas')
    return created


def create_funcionarios(n=100):
    print('Creating funcionarios...')
    created = []
    funcoes = [k for k, _ in Funcionario._meta.get_field('funcao').choices]
    existing_cpfs = set(Funcionario.objects.values_list('cpf', flat=True))
    for i in range(1, n+1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        sobrenome = random.choice(LAST_NAMES)
        nome = f"{first} {last} {sobrenome}"
        cpf = unique_cpf(existing_cpfs)
        data_nasc = random_date(20000, 7000)
        telefone = f"(11) 9{random.randint(10000000,99999999)}"
        email = f"{first.lower()}.{last.lower()}{i}@example.local"
        endereco = f"Rua {random.choice(['A','B','C'])}, {random.randint(1,999)}"
        cidade = "São Paulo"
        estado = "SP"
        cep = f"{random.randint(10000000,99999999):08d}"
        funcao = random.choice(funcoes)
        valor_diaria = Decimal(str(round(random.uniform(80, 350), 2)))
        data_admissao = random_date(3000, 30)
        f = Funcionario.objects.create(
            nome_completo=nome,
            cpf=cpf,
            rg=f"RG{i:06d}",
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
        created.append(f)
    print(f'Created {len(created)} funcionarios')
    return created


def create_clientes():
    """Create Cliente records for names listed in CLIENTES if they don't exist."""
    print('Creating clientes...')
    created = []
    existing_cpfs = set(Cliente.objects.values_list('cpf', flat=True))
    for name in CLIENTES:
        if Cliente.objects.filter(nome__iexact=name).exists():
            continue
        cpf = unique_cpf(existing_cpfs)
        c = Cliente.objects.create(
            nome=name,
            cpf=cpf,
            endereco='Endereço gerado automaticamente',
            ativo=True
        )
        created.append(c)
    print(f'Created {len(created)} clientes')
    return created


if __name__ == '__main__':
    print('Recreating test data with realistic names...')
    with transaction.atomic():
        clean_previous_generated()
        created_clientes = create_clientes()
        created_obras = create_obras(100)
        created_ferramentas = create_ferramentas(100)
        created_funcionarios = create_funcionarios(100)
    print('Done.')
    print(f'Obras total: {Obra.objects.count()}')
    print(f'Ferramentas total: {Ferramenta.objects.count()}')
    print(f'Funcionarios total: {Funcionario.objects.count()}')
