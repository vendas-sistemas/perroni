# Migration: remover unique_together para permitir múltiplos apontamentos
# do mesmo funcionário na mesma obra no mesmo dia (ex: manhã + tarde)

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('funcionarios', '0009_fix_unique_together_apontamento'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='apontamentofuncionario',
            unique_together=set(),  # Remove completamente a constraint
        ),
    ]
