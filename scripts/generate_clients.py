from django.core.management.base import BaseCommand
from apps.clientes.models import Cliente
from django.utils import timezone
import random
import datetime


FIRST_NAMES = [
    'Ana', 'Bruna', 'Camila', 'Carolina', 'Daniela', 'Eduardo', 'Felipe', 'Fernanda',
    'Gabriel', 'Gustavo', 'Henrique', 'Isabela', 'João', 'Jonas', 'Juliana', 'Larissa',
    'Lucas', 'Mariana', 'Marcos', 'Marcio', 'Mateus', 'Paula', 'Pedro', 'Rafael', 'Renata',
    'Ricardo', 'Rodrigo', 'Sofia', 'Tatiana', 'Thiago'
]

LAST_NAMES = [
    'Silva', 'Santos', 'Oliveira', 'Souza', 'Costa', 'Pereira', 'Rodrigues', 'Almeida',
    'Nascimento', 'Lima', 'Araújo', 'Fernandes', 'Cardoso', 'Rocha', 'Gomes', 'Martins',
    'Barbosa', 'Ribeiro', 'Carvalho', 'Mendes'
]


def random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)} {random.randint(1, 99)}"


def random_cpf_formatted():
    # generate 11 random digits and format as 000.000.000-00
    nums = [str(random.randint(0, 9)) for _ in range(11)]
    s = ''.join(nums)
    return f"{s[0:3]}.{s[3:6]}.{s[6:9]}-{s[9:11]}"


def random_phone():
    # Brazilian mobile style
    ddd = random.choice(['11', '21', '31', '41', '51', '61', '71', '81', '91'])
    prefix = random.choice(['9', '8']) + str(random.randint(6, 9))
    rest = ''.join(str(random.randint(0, 9)) for _ in range(7))
    return f"({ddd}) {prefix}{rest}"


def random_email(name, idx):
    local = ''.join(ch for ch in name.lower() if ch.isalnum())
    return f"{local}.{idx}@example.com"


def random_address():
    types = ['Rua', 'Avenida', 'Travessa', 'Praça']
    return f"{random.choice(types)} {random.choice(LAST_NAMES)} {random.randint(1,999)}, Bairro {random.choice(LAST_NAMES)}"


def random_birthdate():
    start = datetime.date(1955, 1, 1)
    end = datetime.date(2002, 12, 31)
    days = (end - start).days
    return start + datetime.timedelta(days=random.randint(0, days))


class Command(BaseCommand):
    help = 'Generate sample Cliente records (realistic-looking names)'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=100, help='How many clients to create')
        parser.add_argument('--skip-existing', action='store_true', help='Do not overwrite existing CPFs if collision')

    def handle(self, *args, **options):
        count = options['count']
        created = 0
        attempts = 0
        self.stdout.write(f"Gerando até {count} clientes...")

        while created < count and attempts < count * 5:
            attempts += 1
            name = random_name()
            cpf = random_cpf_formatted()
            if Cliente.objects.filter(cpf=cpf).exists():
                if options['skip_existing']:
                    continue
                # try again
                continue

            cliente = Cliente(
                nome=name,
                cpf=cpf,
                endereco=random_address(),
                data_nascimento=random_birthdate(),
                telefone=random_phone(),
                email=random_email(name, created + 1),
                ativo=True,
            )
            cliente.save()
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Clientes criados: {created} (tentativas: {attempts})"))
