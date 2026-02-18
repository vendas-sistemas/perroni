# Migration: restaurar unique_together correto em ApontamentoFuncionario
# Permite: mesmo funcionário em dias diferentes ✅
# Permite: funcionários diferentes no mesmo dia ✅
# Permite: mesmo funcionário em obras diferentes no mesmo dia ✅
# Bloqueia: duplicata exata (mesmo func + data + obra) ❌

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('funcionarios', '0008_alter_funcionario_data_admissao_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='apontamentofuncionario',
            unique_together={('funcionario', 'data', 'obra')},
        ),
    ]
