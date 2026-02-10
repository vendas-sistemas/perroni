from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from decimal import Decimal
import random
import datetime

from apps.funcionarios.models import Funcionario
from apps.ferramentas.models import Ferramenta
from apps.obras.models import Obra, Etapa

# Data pools
FIRST_NAMES = ['João', 'Maria', 'Pedro', 'Ana', 'Carlos', 'Paula', 'Rafael', 'Carolina', 'Lucas', 'Mariana']
LAST_NAMES = ['Silva', 'Santos', 'Oliveira', 'Souza', 'Pereira', 'Costa', 'Rodrigues', 'Almeida']
TOOL_NAMES = ['Alicate', 'Betoneira', 'Furadeira', 'Serra Circular', 'Marreta', 'Trena', 'Nível', 'Esquadro']
OBRA_PREFIXES = ['Residencial', 'Comercial', 'Condomínio', 'Edifício']
CLIENTES = ['Construtora Alfa', 'Construtora Beta', 'Grupo Nova', 'Empreendimentos Delta']


def random_date(start_days_ago=3650, end_days_ago=30):
    today = datetime.date.today()
    start = today - datetime.timedelta(days=start_days_ago)
    end = today - datetime.timedelta(days=end_days_ago)
    delta = (end - start).days
    return start + datetime.timedelta(days=random.randint(0, max(0, delta)))


def unique_cpf(existing):
    while True:
        n = random.randint(10**10, 10**11 - 1)
        s = f"{n:011d}"
        if s not in existing:
            existing.add(s)
            return s


class Command(BaseCommand):
    help = 'Gera dados de teste: funcionarios, ferramentas e obras.'

    def add_arguments(self, parser):
        parser.add_argument('--funcionarios', type=int, default=100)
        parser.add_argument('--ferramentas', type=int, default=100)
        parser.add_argument('--obras', type=int, default=100)
        parser.add_argument('--clean', action='store_true', help='Remover registros gerados anteriormente que batem com os padrões de teste antes de criar')

    def handle(self, *args, **options):
        n_func = options['funcionarios']
        n_ferr = options['ferramentas']
        n_obras = options['obras']
        do_clean = options['clean']

        if do_clean:
            self.stdout.write('Limpando registros gerados anteriormente...')
            Obra.objects.filter(nome__icontains='Obra Teste').delete()
            Ferramenta.objects.filter(descricao__icontains='Gerado automaticamente').delete()
            Funcionario.objects.filter(nome_completo__icontains='Funcionario Teste').delete()

        self.stdout.write(f'Criando até {n_obras} obras, {n_ferr} ferramentas, {n_func} funcionarios...')

        with transaction.atomic():
            # Obras
            existing_obras = Obra.objects.count()
            to_create_obras = max(0, n_obras - existing_obras)
            created_obras = []
            for i in range(1, to_create_obras + 1):
                idx = existing_obras + i
                nome = f"{random.choice(OBRA_PREFIXES)} {idx:03d}"
                cliente = random.choice(CLIENTES)
                endereco = f"Rua {idx}, Bairro Centro"
                data_inicio = random_date(3650, 365)
                data_previsao = data_inicio + datetime.timedelta(days=random.randint(90, 720))
                status = random.choice([k for k, _ in Obra._meta.get_field('status').choices])
                percentual = Decimal(str(round(random.uniform(0, 100), 2)))
                o = Obra.objects.create(
                    nome=nome,
                    endereco=endereco,
                    cliente=cliente,
                    data_inicio=data_inicio,
                    data_previsao_termino=data_previsao,
                    status=status,
                    percentual_concluido=percentual,
                    ativo=True
                )
                # Criar 5 etapas básicas para a obra recém-criada
                for num, _label in Etapa.ETAPA_CHOICES:
                    Etapa.objects.create(
                        obra=o,
                        numero_etapa=num,
                        percentual_valor=Etapa.PERCENTUAIS_ETAPA.get(num)
                    )
                created_obras.append(o)

            # Ferramentas
            existing_f = Ferramenta.objects.count()
            to_create_f = max(0, n_ferr - existing_f)
            obras_list = list(Obra.objects.all())
            categorias = [k for k, _ in Ferramenta._meta.get_field('categoria').choices]
            status_choices = [k for k, _ in Ferramenta._meta.get_field('status').choices]
            for i in range(1, to_create_f + 1):
                idx = existing_f + i
                nome_base = random.choice(TOOL_NAMES)
                nome = f"{nome_base} {idx:03d}"
                codigo = f"TF{idx:04d}"
                categoria = random.choice(categorias)
                status = random.choice(status_choices)
                obra_atual = random.choice(obras_list) if obras_list and random.random() < 0.4 else None
                Ferramenta.objects.create(
                    codigo=codigo,
                    nome=nome,
                    descricao='Gerado automaticamente',
                    categoria=categoria,
                    status=status,
                    obra_atual=obra_atual,
                    data_aquisicao=random_date(3650, 0),
                    valor_aquisicao=Decimal(str(round(random.uniform(20, 2000), 2))),
                    ativo=True
                )

            # Funcionarios
            existing_func = Funcionario.objects.count()
            to_create_func = max(0, n_func - existing_func)
            existing_cpfs = set(Funcionario.objects.values_list('cpf', flat=True))
            funcoes = [k for k, _ in Funcionario._meta.get_field('funcao').choices]
            for i in range(1, to_create_func + 1):
                idx = existing_func + i
                first = random.choice(FIRST_NAMES)
                last = random.choice(LAST_NAMES)
                nome = f"{first} {last} {idx}"
                cpf = unique_cpf(existing_cpfs)
                data_nasc = random_date(20000, 7000)
                telefone = f"(11) 9{random.randint(10000000,99999999)}"
                email = f"{first.lower()}.{last.lower()}{idx}@example.local"
                endereco = f"Rua {idx}"
                cidade = 'São Paulo'
                estado = 'SP'
                cep = f"{random.randint(10000000,99999999):08d}"
                funcao = random.choice(funcoes)
                valor_diaria = Decimal(str(round(random.uniform(80, 350), 2)))
                data_admissao = random_date(3000, 30)
                Funcionario.objects.create(
                    nome_completo=nome,
                    cpf=cpf,
                    rg=f"RG{idx:06d}",
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

        self.stdout.write(self.style.SUCCESS('Dados de teste gerados com sucesso.'))