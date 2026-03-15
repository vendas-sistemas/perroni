from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fornecedores', '0001_initial'),
        ('ferramentas', '0004_alter_ferramenta_ativo'),
    ]

    operations = [
        migrations.AddField(
            model_name='ferramenta',
            name='classificacao',
            field=models.CharField(choices=[('propria', 'Patrimônio Próprio'), ('alugada', 'Alugada')], default='propria', max_length=20, verbose_name='Classificação'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='ferramenta',
            name='fornecedor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ferramentas', to='fornecedores.fornecedor', verbose_name='Fornecedor'),
        ),
        migrations.AlterField(
            model_name='movimentacaoferramenta',
            name='tipo',
            field=models.CharField(choices=[('entrada_deposito', 'Entrada no Depósito (Compra/Recebimento)'), ('saida_obra', 'Saída para Obra'), ('transferencia', 'Transferência entre Obras'), ('retorno_deposito', 'Retorno ao Depósito'), ('envio_manutencao', 'Envio para Manutenção'), ('retorno_manutencao', 'Retorno de Manutenção'), ('perda', 'Perda/Extravio'), ('descarte', 'Descarte/Baixa'), ('devolver_fornecedor', 'Devolver ao Fornecedor')], max_length=25, verbose_name='Tipo de Movimentação'),
        ),
    ]
