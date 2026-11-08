from django.db import migrations, models

from apps.acesso.preenchimento import preencher


def preencher_existentes(apps, schema_editor):
    preencher(apps.get_model("acesso", "Perfil"))


class Migration(migrations.Migration):
    dependencies = [("acesso", "0003_perfil_foto")]

    operations = [
        migrations.AddField(
            model_name="perfil",
            name="entrou_em",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.RunPython(preencher_existentes, migrations.RunPython.noop),
    ]
