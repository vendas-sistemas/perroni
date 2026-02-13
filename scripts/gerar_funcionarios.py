#!/usr/bin/env python
"""
Script para gerar funcionários com dados completos.
Uso: python gerar_funcionarios.py
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.funcionarios.models import Funcionario


# Nomes e sobrenomes
NOMES = [
    'João', 'Maria', 'Carlos', 'Ana', 'Pedro', 'Paula', 'Paulo', 'Fernanda',
    'Felipe', 'Juliana', 'Ricardo', 'Camila', 'Francisco', 'Tatiana', 'Diego',
    'Mariana', 'Eduardo', 'Alessandra', 'Roberto', 'Daniela', 'André', 'Beatriz',
    'Marcos', 'Viviane', 'Gabriel', 'Priscila', 'Lucas', 'Simone', 'Rafael', 'Gabriela',
]

SOBRENOMES = [
    'Silva', 'Santos', 'Oliveira', 'Souza', 'Costa', 'Ferreira', 'Rodrigues', 'Martins',
    'Gomes', 'Alves', 'Carvalho', 'Ribeiro', 'Teixeira', 'Nunes', 'Mendes', 'Pereira',
    'Barbosa', 'Monteiro', 'Machado', 'Rocha', 'Correia', 'Lopes', 'Mota', 'Duarte',
]

BAIRROS = [
    'Centro', 'Liberdade', 'Vila Mariana', 'Pinheiros', 'Jardins', 'Tatuapé',
    'Morumbi', 'Vila Madalena', 'Consolação', 'Santa Cecília', 'Alto da Lapa',
]

RUAS = ['Rua', 'Avenida', 'Alameda', 'Travessa']

CIDADES = [
    'São Paulo', 'Guarulhos', 'São Bernardo do Campo', 'Santo André',
    'Osasco', 'Mauá', 'Diadema', 'Barueri', 'Jundiaí',
]


def gerar_cpf_valido():
    """Gera um CPF válido formatado como XXX.XXX.XXX-XX."""
    numeros = [random.randint(0, 9) for _ in range(9)]
    
    soma = sum(a * b for a, b in zip(numeros, range(10, 1, -1)))
    digito1 = 11 - (soma % 11)
    digito1 = 0 if digito1 > 9 else digito1
    numeros.append(digito1)
    
    soma = sum(a * b for a, b in zip(numeros, range(11, 1, -1)))
    digito2 = 11 - (soma % 11)
    digito2 = 0 if digito2 > 9 else digito2
    numeros.append(digito2)
    
    cpf_str = ''.join(map(str, numeros))
    return f"{cpf_str[0:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:11]}"


def gerar_rg_valido():
    """Gera um RG formatado."""
    numeros = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    return f"{numeros[0:2]}.{numeros[2:5]}.{numeros[5:8]}-{random.randint(0, 9)}"


def gerar_nome_funcionario():
    """Gera um nome completo."""
    nome = random.choice(NOMES)
    num_sobrenomes = random.randint(2, 3)
    sobrenomes = [random.choice(SOBRENOMES) for _ in range(num_sobrenomes)]
    return f"{nome} {' '.join(sobrenomes)}"


def gerar_telefone():
    """Gera um telefone no formato (XX) 9XXXX-XXXX."""
    area = random.randint(10, 99)
    numero = random.randint(900000000, 999999999)
    return f"({area}) 9{numero:08d}"


def gerar_endereco():
    """Gera um endereço aleatório."""
    rua = random.choice(RUAS)
    bairro = random.choice(BAIRROS)
    numero = random.randint(1, 9999)
    return f"{rua} {bairro}, {numero}"


def gerar_email_aleatorio(nome):
    """Gera um email simples baseado no nome."""
    base = nome.lower().replace(' ', '.').replace('ã', 'a').replace('á', 'a')
    dominios = ['gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com']
    return f"{base}@{random.choice(dominios)}"


def gerar_funcionarios(quantidade):
    """Cria N funcionários com dados aleatórios."""
    criados = 0
    erros = 0
    cpfs_existentes = set(Funcionario.objects.values_list('cpf', flat=True))
    
    print(f"\n{'='*60}")
    print(f"👷 Gerando {quantidade} funcionários...")
    print(f"{'='*60}\n")
    
    for i in range(quantidade):
        try:
            # Gera CPF único até 10 tentativas
            tentativas = 0
            while tentativas < 10:
                cpf = gerar_cpf_valido()
                if cpf not in cpfs_existentes:
                    break
                tentativas += 1
            
            if cpf in cpfs_existentes:
                print(f"  ❌ [{i+1}/{quantidade}] CPF único não gerado. Pulando...")
                erros += 1
                continue
            
            nome = gerar_nome_funcionario()
            rg = gerar_rg_valido()
            data_nasc = (datetime.now() - timedelta(days=random.randint(18*365, 65*365))).date()
            telefone = gerar_telefone()
            email = gerar_email_aleatorio(nome)
            endereco = gerar_endereco()
            cidade = random.choice(CIDADES)
            estado = 'SP'
            cep_1 = random.randint(1000, 9999)
            cep_2 = random.randint(100, 999)
            cep = f"{cep_1:04d}-{cep_2:03d}"
            
            # Função aleatória
            funcao = random.choice(['pedreiro', 'servente'])
            
            # Valor da diária padrão por função
            if funcao == 'pedreiro':
                valor_diaria = Decimal('200.00')
            else:  # servente
                valor_diaria = Decimal('150.00')
            
            # Data de admissão nos últimos 2 anos
            data_admissao = (datetime.now() - timedelta(days=random.randint(1, 730))).date()
            
            funcionario = Funcionario.objects.create(
                nome_completo=nome,
                cpf=cpf,
                rg=rg,
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
                ativo=True,
            )
            
            cpfs_existentes.add(cpf)
            criados += 1
            print(f"  ✅ [{i+1}/{quantidade}] {funcionario.nome_completo} ({funcionario.get_funcao_display()}) - R$ {funcionario.valor_diaria}")
            
        except Exception as e:
            erros += 1
            print(f"  ❌ [{i+1}/{quantidade}] Erro ao criar funcionário: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 Resultado: {criados} criados, {erros} erros")
    print(f"{'='*60}\n")


def main():
    try:
        quantidade = input("Quantos funcionários deseja criar? ").strip()
        
        if not quantidade.isdigit():
            print("❌ Favor informar um número inteiro válido.")
            sys.exit(1)
        
        quantidade = int(quantidade)
        if quantidade <= 0:
            print("❌ A quantidade deve ser maior que 0.")
            sys.exit(1)
        
        gerar_funcionarios(quantidade)
        
    except KeyboardInterrupt:
        print("\n\n⏸️  Operação cancelada pelo usuário.")
        sys.exit(0)


if __name__ == '__main__':
    main()
