# Generated manual migration to add cliente_fk and populate from existing cliente text
from django.db import migrations, models
import django.db.models.deletion


def populate_cliente_fk(apps, schema_editor):
    Obra = apps.get_model('obras', 'Obra')
    Cliente = apps.get_model('clientes', 'Cliente')
    import re
    for obra in Obra.objects.all():
        nome_text = (obra.cliente or '') if hasattr(obra, 'cliente') else ''
        cliente_obj = None
        if nome_text:
            # try exact name match
            cliente_obj = Cliente.objects.filter(nome__iexact=nome_text).first()
            if not cliente_obj:
                cliente_obj = Cliente.objects.filter(nome__icontains=nome_text).first()
        if not cliente_obj:
            # try extract digits from the text and match CPF
            digits = re.sub(r"\D", "", nome_text)
            if digits:
                if len(digits) == 11:
                    formatted = f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
                    cliente_obj = Cliente.objects.filter(models.Q(cpf__icontains=formatted) | models.Q(cpf__icontains=digits)).first()
                else:
                    cliente_obj = Cliente.objects.filter(cpf__icontains=digits).first()
        if cliente_obj:
            # set the new FK field; use _id to avoid fetching relation
            obra.cliente_fk_id = cliente_obj.id
            obra.save()


def depopulate_cliente_fk(apps, schema_editor):
    Obra = apps.get_model('obras', 'Obra')
    for obra in Obra.objects.all():
        obra.cliente_fk_id = None
        obra.save()


class Migration(migrations.Migration):

    dependencies = [
        ('obras', '0001_initial'),
        ('clientes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='obra',
            name='cliente_fk',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, related_name='+', blank=True, null=True, to='clientes.cliente'),
        ),
        migrations.RunPython(populate_cliente_fk, depopulate_cliente_fk),
    ]
