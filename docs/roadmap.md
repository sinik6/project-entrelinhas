# Roadmap e ledger de tarefas

Fonte: `docs/especificacao-origem.md`. Marque `[x]` só com evidência (teste rodado / deploy conferido).

## Fase 1 — Fundação
- [x] T0101 — Projeto Django + DRF com PostgreSQL via Docker Compose (local; falta conferir `docker compose up`).
- [x] T0102 — Testes e health check (`GET /api/v1/health`).
- [ ] T0103 — Infra: repositório no GitHub, ambiente `production`, primeiro deploy na VPS.

## Fase 2 — Autenticação, espaços e convites
- [ ] T0201 — Autenticação Django (sessions / cookies HttpOnly).
- [ ] T0202 — Espaços e convites (máximo 2 membros).

## Fase 3 — Escrita, visibilidade parcial e privada
- [ ] T0301 — Modelo `entries` e migrações.
- [ ] T0302 — Lógica de visibilidade no backend.
- [ ] T0303 — API de leitura com filtragem/truncamento no servidor.
- [ ] T0304 — Frontend: seleção de trecho e modo de visibilidade.

## Fase 4 — Destaques e comentários
- [ ] T0401 — Modelos `entry_highlights` e `entry_comments`.
- [ ] T0402 — Endpoints de destaques e comentários.
- [ ] T0403 — Componente de seleção, highlight e popover.

## Fase 5 — Fotos, PWA e push
- [ ] T0501 — Upload privado de fotos manuscritas.
- [ ] T0502 — PWA e Web Push às 21h30.
