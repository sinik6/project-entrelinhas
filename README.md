# Entrelinhas

Diário compartilhado para duas pessoas. Spec em [docs/especificacao-origem.md](docs/especificacao-origem.md),
roadmap em [docs/roadmap.md](docs/roadmap.md), regras de trabalho em [CLAUDE.md](CLAUDE.md).

## Desenvolvimento

```bash
docker compose up --build        # API em http://localhost:8010/api/v1/health
```

Testes (dentro de `backend/`, com um Postgres acessível):

```bash
uv sync --frozen
uv run pytest --create-db
```

## Produção

https://jpsys.duckdns.org/entrelinhas — push na `main` roda o CI e, aprovado, o workflow
`Deploy Entrelinhas` publica na VPS (`infra/deploy.sh`). Variáveis e segredos do ambiente
`production` do GitHub: `DEPLOY_HOST`, `DEPLOY_USER` (vars); `DEPLOY_SSH_KEY`,
`DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD` (secrets).
