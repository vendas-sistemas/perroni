from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('obras', '0002_add_cliente_fk'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='obra',
            name='cliente',
        ),
        migrations.RenameField(
            model_name='obra',
            old_name='cliente_fk',
            new_name='cliente',
        ),
    ]
