# Tecnologia — Entrelinhas

## Stack (versões travadas no lockfile)
| Camada | Tecnologia | Versão | Doc oficial da versão |
|---|---|---|---|
| Backend | Django / DRF | 5.2 / 3.17 | https://docs.djangoproject.com/en/5.2/ · https://www.django-rest-framework.org/ |
| Linguagem | Python (uv) | 3.13 | https://docs.astral.sh/uv/ |
| Servidor | gunicorn + WhiteNoise | 23 / 6.12 | — |
| Web | Next.js + TypeScript (PWA) | a definir na mudança do front | — |
| Banco | PostgreSQL | 17 | https://www.postgresql.org/docs/17/ |
| Infra | Docker Compose, GitHub Actions, Traefik central da VPS | | repositório `traefikproxy` |

## Usage specs (libs novas, raras ou que mudaram muito)
| Lib | Versão | Armadilhas conhecidas / API correta |
|---|---|---|
| Django `ATOMIC_REQUESTS` | 5.2 | cada request é uma transação; erro no meio desfaz tudo |
| WhiteNoise `CompressedManifestStaticFilesStorage` | 6.12 | exige `collectstatic` no build da imagem (o Dockerfile faz) |

## Comandos (dentro de `backend/`)
| Ação | Comando |
|---|---|
| Dependências | `uv sync --frozen` |
| Subir tudo (dev) | `docker compose up --build` na raiz; API em http://localhost:8010 |
| Testes | `uv run pytest --create-db` (PostgreSQL acessível) |
| Lint / formato | `uv run ruff check . && uv run ruff format --check .` |
| Checagens do Django | `uv run python manage.py check && uv run python manage.py makemigrations --check --dry-run` |
| Checagem de produção | `DJANGO_SETTINGS_MODULE=config.settings.prod DJANGO_SECRET_KEY=<chave longa> DJANGO_ALLOWED_HOSTS=api.exemplo.com uv run python manage.py check --deploy --fail-level WARNING` |
| Verificar specs | `python ~/.claude/skills/spec-driven-dev/scripts/sdd_lint.py . --code backend` |

## Restrições técnicas
- Sem dependência nova sem ADR; nunca pip global; venv fora do repositório no desenvolvimento.
- API versionada em `/api/v1`; só o BFF do front a chama, pela rede interna.
- Ambiente local (Windows): `UV_PYTHON_INSTALL_DIR=C:/Users/jpfis/.uvpython`; as portas 5432 e 8000
  costumam estar ocupadas por outros projetos (o `compose.yml` não publica o banco e sobe a API em 8010);
  nos testes use um PostgreSQL descartável em porta própria (ex.: 55433), com `POSTGRES_HOST=127.0.0.1`.
- Produção em `https://jpsys.duckdns.org/entrelinhas`; variáveis obrigatórias: `DJANGO_SECRET_KEY` e `POSTGRES_PASSWORD`.
