# Manutenção do backend

## Criar um app de domínio
1. `apps/<dominio>/` com `apps.py`, `models.py`, `services.py`, `serializers.py`, `views.py`, `urls.py`, `tests/`.
2. Registrar em `INSTALLED_APPS` (`config/settings/base.py`) e em `config/api_v1.py`.
3. `uv run python manage.py makemigrations <dominio>` e commitar a migração.
4. Teste de acesso cruzado (outro espaço = 404) e, se devolve texto de registro, teste de visibilidade.

## Dependências
Nova dependência exige ADR (constituição). Adicionar com `uv add <pacote>` dentro de `backend/` e
commitar `pyproject.toml` e `uv.lock`; o Dockerfile instala com `uv sync --frozen`.

## Antes de concluir
Os comandos estão em [`docs/tecnologia.md`](../../docs/tecnologia.md).

## Produção
Deploy pelo workflow `Deploy Entrelinhas`; operação manual na VPS: `cd ~/project-entrelinhas &&
docker compose -f docker-compose.deploy.yml --env-file .env.production ps`. Backups em
`~/backups/project-entrelinhas`.
