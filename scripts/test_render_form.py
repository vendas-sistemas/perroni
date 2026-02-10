#!/usr/bin/env python
import sys, os

# Add project to path
proj_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, proj_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.template import Template, Context
from apps.clientes.forms import ClienteForm

p = os.path.normpath(os.path.join(proj_root, 'templates', 'clientes', 'cliente_form.html'))
with open(p, encoding='utf-8') as f:
    t = Template(f.read())

html = t.render(Context({'form': ClienteForm(), 'title': 'Teste'}))

if 'form-check' in html and 'name="ativo"' in html:
    print('OK')
else:
    print('FAIL')
    print(html)
