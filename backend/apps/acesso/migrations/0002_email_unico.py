"""Um e-mail, uma conta (spec 003, REQ-3.6): índice único em `lower(email)` na tabela de usuários do Django."""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("acesso", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunSQL(
            sql="CREATE UNIQUE INDEX acesso_email_unico ON auth_user (lower(email)) WHERE email <> '';",
            reverse_sql="DROP INDEX acesso_email_unico;",
        ),
    ]
