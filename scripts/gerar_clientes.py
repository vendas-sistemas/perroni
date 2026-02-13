#!/usr/bin/env python
"""
Script para gerar clientes com nomes e sobrenomes aleatórios.
Uso: python gerar_clientes.py
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.clientes.models import Cliente


# Nomes e sobrenomes em português
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
    'Pinto', 'Coelho', 'Simões', 'Freitas', 'Castro', 'Medeiros', 'Vieira', 'Tavares',
    'Fonseca', 'Leite', 'Soares', 'Dias', 'Campos', 'Amorim', 'Mendes', 'Brito',
]


def gerar_cpf_valido():
    """Gera um CPF válido formatado como XXX.XXX.XXX-XX."""
    # Gera 9 dígitos aleatórios
    numeros = [random.randint(0, 9) for _ in range(9)]
    
    # Calcula o primeiro dígito verificador
    soma = sum(a * b for a, b in zip(numeros, range(10, 1, -1)))
    digito1 = 11 - (soma % 11)
    digito1 = 0 if digito1 > 9 else digito1
    numeros.append(digito1)
    
    # Calcula o segundo dígito verificador
    soma = sum(a * b for a, b in zip(numeros, range(11, 1, -1)))
    digito2 = 11 - (soma % 11)
    digito2 = 0 if digito2 > 9 else digito2
    numeros.append(digito2)
    
    # Formata como XXX.XXX.XXX-XX
    cpf_str = ''.join(map(str, numeros))
    return f"{cpf_str[0:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:11]}"


def gerar_nome_cliente():
    """Gera um nome com até 4 sobrenomes aleatórios."""
    nome = random.choice(NOMES)
    num_sobrenomes = random.randint(2, 4)
    sobrenomes = [random.choice(SOBRENOMES) for _ in range(num_sobrenomes)]
    return f"{nome} {' '.join(sobrenomes)}"


def gerar_email_aleatorio(nome):
    """Gera um email simples baseado no nome."""
    base = nome.lower().replace(' ', '.').replace('ã', 'a').replace('á', 'a')
    dominios = ['gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com']
    return f"{base}@{random.choice(dominios)}"


def gerar_telefone():
    """Gera um telefone no formato (XX) 9XXXX-XXXX."""
    area = random.randint(10, 99)
    numero = random.randint(900000000, 999999999)
    return f"({area}) 9{numero:08d}"


def gerar_clientes(quantidade):
    """Cria N clientes com dados aleatórios e valida CPF único."""
    criados = 0
    erros = 0
    cpfs_existentes = set(Cliente.objects.values_list('cpf', flat=True))
    
    print(f"\n{'='*60}")
    print(f"🎲 Gerando {quantidade} clientes...")
    print(f"{'='*60}\n")
    
    for i in range(quantidade):
        try:
            # Gera dados únicos até encontrar CPF não registrado
            tentativas = 0
            while tentativas < 10:
                cpf = gerar_cpf_valido()
                if cpf not in cpfs_existentes:
                    break
                tentativas += 1
            
            if cpf in cpfs_existentes:
                print(f"  ❌ [{i+1}/{quantidade}] CPF único não gerado após 10 tentativas. Pulando...")
                erros += 1
                continue
            
            nome = gerar_nome_cliente()
            email = gerar_email_aleatorio(nome)
            telefone = gerar_telefone()
            data_nasc = (datetime.now() - timedelta(days=random.randint(18*365, 70*365))).date()
            
            cliente = Cliente.objects.create(
                nome=nome,
                cpf=cpf,
                email=email,
                telefone=telefone,
                data_nascimento=data_nasc,
                ativo=True,
            )
            
            cpfs_existentes.add(cpf)
            criados += 1
            print(f"  ✅ [{i+1}/{quantidade}] {cliente.nome} ({cliente.cpf})")
            
        except Exception as e:
            erros += 1
            print(f"  ❌ [{i+1}/{quantidade}] Erro ao criar cliente: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 Resultado: {criados} criados, {erros} erros")
    print(f"{'='*60}\n")


def main():
    try:
        quantidade = input("Quantos clientes deseja criar? ").strip()
        
        if not quantidade.isdigit():
            print("❌ Favor informar um número inteiro válido.")
            sys.exit(1)
        
        quantidade = int(quantidade)
        if quantidade <= 0:
            print("❌ A quantidade deve ser maior que 0.")
            sys.exit(1)
        
        gerar_clientes(quantidade)
        
    except KeyboardInterrupt:
        print("\n\n⏸️  Operação cancelada pelo usuário.")
        sys.exit(0)


if __name__ == '__main__':
    main()
