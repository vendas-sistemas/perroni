from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if not dictionary:
        return None
    return dictionary.get(key)


@register.filter
def brl(value):
    """Formata valor para padrão brasileiro: R$ 1.234,56"""
    try:
        value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return 'R$ 0,00'
    
    value = value.quantize(Decimal('0.01'))
    # Separar parte inteira e decimal
    str_value = str(abs(value))
    if '.' in str_value:
        inteira, decimal = str_value.split('.')
    else:
        inteira = str_value
        decimal = '00'
    
    decimal = decimal.ljust(2, '0')[:2]
    
    # Adicionar pontos como separador de milhar
    inteira_formatada = ''
    for i, digit in enumerate(reversed(inteira)):
        if i > 0 and i % 3 == 0:
            inteira_formatada = '.' + inteira_formatada
        inteira_formatada = digit + inteira_formatada
    
    sinal = '-' if value < 0 else ''
    return f'{sinal}R$ {inteira_formatada},{decimal}'
