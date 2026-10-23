# Tecnologia

| Camada | Escolha |
|---|---|
| API | Django 5.2, Django REST Framework 3.17, Python 3.13 |
| Dependências | uv (`backend/pyproject.toml` + `uv.lock`); nunca pip global |
| Servidor | gunicorn, WhiteNoise para estáticos do Admin |
| Banco | PostgreSQL 17 |
| Lint | ruff (`check` e `format`) |
| Testes | pytest + pytest-django, sempre em PostgreSQL real |
| Frontend | Next.js + TypeScript (T0304 em diante) |
| Infra | Docker Compose; Traefik central da VPS; GitHub Actions |

## Comandos (dentro de `backend/`)

Antes de concluir qualquer tarefa:

```bash
uv sync --frozen
uv run ruff check . && uv run ruff format --check .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run pytest --create-db
```

`check --deploy` roda com `DJANGO_SETTINGS_MODULE=config.settings.prod`, `DJANGO_SECRET_KEY` longa e
`DJANGO_ALLOWED_HOSTS` definidos (o CI faz isso).

## Ambiente local (Windows)
- `UV_PYTHON_INSTALL_DIR=C:/Users/jpfis/.uvpython`; venv fora do repo (`UV_PROJECT_ENVIRONMENT`).
- Portas 5432 e 8000 costumam estar ocupadas por outros projetos: o `compose.yml` não publica o
  banco e sobe a API em `8010`.
- Para os testes, suba um Postgres descartável (`postgres:17-alpine`) em porta própria
  (ex.: 55433) e use `POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=55433`; apague o container depois.
- Desenvolvimento completo: `docker compose up --build` na raiz.

## Variáveis de ambiente
Ver `.env.example`. Produção: `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD` (obrigatórias),
`DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `DJANGO_PREFIXO_URL` (definidas no compose).
