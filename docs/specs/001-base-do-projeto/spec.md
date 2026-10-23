# 001 — Base do projeto (T0101, T0102, T0103)

## Comportamento
- Projeto Django 5.2 + DRF com PostgreSQL, subindo por `docker compose up` (API em `localhost:8010`).
- `GET /api/v1/health` responde sem login e confirma que o banco aceita consulta.
- Pipeline: push na `main` roda o CI (lint, checagens do Django, testes em PostgreSQL, build da imagem,
  validação do compose de produção) e, aprovado, o workflow `Deploy Entrelinhas` publica na VPS.
- Produção: `https://jpsys.duckdns.org/entrelinhas` (e pelo IP), sob o Traefik central (ADR-003). Nesta
  fase só o Django Admin e os estáticos dele ficam públicos; o front chega na T0304.

## Suposições
- O repositório fica em `github.com/sinik6/project-entrelinhas` (dono `sinik6`, `jpjamal` colaborador).
- O ambiente `production` do GitHub é criado por quem é admin do repositório, com `DEPLOY_HOST`,
  `DEPLOY_USER`, `DEPLOY_SSH_KEY`, `DJANGO_SECRET_KEY` e `POSTGRES_PASSWORD`.
- Fotos (SILO), Web Push e front não entram nesta spec.

## Aceitação
- **001-C1** — `GET /api/v1/health` responde 200 com `{"status": "ok"}` sem autenticação.
- **001-C2** — o health executa uma consulta no banco; banco fora do ar não devolve 200.
- **001-C3** — `ruff check`, `ruff format --check`, `manage.py check`, `makemigrations --check` e
  `check --deploy` (settings de produção) saem limpos, e o CI roda o mesmo.
- **001-C4** — a imagem Docker da API constrói, tem healthcheck, e o `docker-compose.deploy.yml` é válido.
- **001-C5** — produção recusa subir sem `DJANGO_SECRET_KEY`.
- **001-C6** — após o push na `main`, o deploy publica e `https://jpsys.duckdns.org/entrelinhas/admin/login/`
  responde 200 pelo domínio e pelo IP, e `http` redireciona para `https`.

## Não objetivos
Autenticação, modelos de domínio, front, fotos, push, backup fora da VPS.
