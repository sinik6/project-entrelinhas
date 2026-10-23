# Roadmap e ledger de tarefas

Fonte: [especificacao-origem.md](especificacao-origem.md). Marque `[x]` só com evidência
(teste rodado / deploy conferido) no `validation.md` da spec.

## Fase 1 — Fundação — spec [001](specs/001-base-do-projeto/spec.md)
- [x] T0101 — Projeto Django + DRF com PostgreSQL via Docker Compose (falta conferir `docker compose up` completo).
- [x] T0102 — Testes e health check (`GET /api/v1/health`).
- [ ] T0103 — Infra: repositório no GitHub (feito), ambiente `production`, chave SSH, primeiro deploy na VPS.

## Fase 2 — Autenticação, espaços e convites
- [ ] T0201 — Autenticação Django (sessions / cookies HttpOnly) — ADR-004.
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

## Pendências de decisão (resolver na spec da tarefa indicada)
Detalhes em [`docs/dominio/`](dominio/README.md).

| Pergunta | Onde | Antes de |
|---|---|---|
| Unidade dos offsets (caractere Unicode ou UTF-16) e trecho por linhas ou caracteres | [registros](dominio/registros.md) | T0301 |
| Registro entregue pode ser editado? Visibilidade muda depois? | [registros](dominio/registros.md) | T0301 |
| Offsets do destaque referem o texto integral ou o visível? | [destaques](dominio/destaques-e-comentarios.md) | T0401 |
| Como funciona o convite (link, código, e-mail) e a saída de um membro | [espaço](dominio/espaco.md) | T0202 |
| Fotos: SILO ou volume; visíveis em `partial`? | [fotos](dominio/fotos-e-lembretes.md) | T0501 |
| Fuso por usuário e regra do lembrete das 21h30 | [fotos](dominio/fotos-e-lembretes.md) | T0502 |

## Riscos
- O deploy depende de a rede `traefik_proxy` existir na VPS e do ambiente `production` do GitHub, criado por quem é admin do repo (`sinik6`).
- Mudar a unidade dos offsets depois de haver dados corrompe os trechos e os destaques: decidir antes da T0301.
