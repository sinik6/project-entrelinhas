# Entrelinhas

Diário compartilhado para duas pessoas. Usa Spec-Driven Development: comece por [AGENTS.md](AGENTS.md) e por
[specs/capability-map.md](specs/capability-map.md); o texto original da especificação está em
[specs/origem/especificacao-origem.md](specs/origem/especificacao-origem.md).

## Desenvolvimento

```bash
docker compose up --build        # API em http://localhost:8010/api/v1/health
```

Testes (dentro de `backend/`, com um PostgreSQL acessível; detalhes em [specs/steering/tech.md](specs/steering/tech.md)):

```bash
uv sync --frozen
uv run pytest --create-db
```

## Produção

https://jpsys.duckdns.org/entrelinhas — push na `main` roda o CI e, aprovado, o workflow
`Deploy Entrelinhas` publica na VPS (`infra/deploy.sh`). Ambiente `production` do GitHub:
variáveis `DEPLOY_HOST`, `DEPLOY_USER`; segredos `DEPLOY_SSH_KEY`, `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD`.
