# Entrelinhas — especificação de origem (SDD)

> Texto recebido do dono do produto em 2026-10-19, guardado como veio (fonte, não se edita). Foi
> desdobrado em `specs/steering/`, `specs/capability-map.md` e nas mudanças em `specs/changes/`.
> O modelo de dados e os requisitos RF-05 e RF-11 daqui entram nas specs de `registros` e `destaques`.

**Status:** Draft — aguardando revisão do proprietário do produto
**Objetivo:** aplicativo web instalável (PWA) para duas pessoas compartilharem escrita diária, fotos de textos manuscritos, trechos selecionados e comentários contextuais.

## Decisões aprovadas para o MVP

- Frontend: Next.js + TypeScript, interface responsiva e PWA.
- Backend: Django + Django REST Framework + Python.
- Banco: PostgreSQL.
- Deploy: Docker Compose em VPS com HTTPS.
- Fotos: armazenamento privado compatível com S3 ou volume privado via Django.
- Lembretes: Web Push agendado para 21h30 no fuso configurado pelo usuário.
- Espaço: exatamente dois participantes.
- Visibilidade na entrega: privada total, parcial (seleção de trecho) ou pública/visível ao parceiro.
- Interatividade: comentários e destaques em estilo Kindle sobre o texto visível.

## Constituição

1. **Especificação antes do código.** Toda funcionalidade tem requisitos verificáveis antes de ser implementada.
2. **Privacidade e filtragem estrita no servidor.** Textos privados ou trechos não selecionados NUNCA vão na resposta HTTP do Django. A filtragem é feita obrigatoriamente no backend.
3. **Sem expansão automática de escopo.** Só o que está neste documento é implementado.

## Requisitos funcionais

### RF-05 — Entrega e modos de visibilidade
- AC-05.1: o autor escolhe o modo de visibilidade ao entregar:
  - **Totalmente visível (`full`):** texto completo e anexos visíveis ao parceiro.
  - **Privado (`private`):** o parceiro vê só a indicação de entrega, com o status *"Enviado, mas mantido privado pelo autor"*. O texto não é enviado na API.
  - **Parcial (`partial`):** o autor delimita as linhas ou o trecho que o parceiro pode ler. O backend trunca o texto e envia estritamente o intervalo selecionado.
- AC-05.2: a entrega registra data/hora no servidor.

### RF-11 — Destaques e comentários contextuais (estilo Kindle)
- AC-11.1: o parceiro seleciona uma área do texto que lhe é visível para destacar.
- AC-11.2: a área destacada fica marcada visualmente no editor/leitor.
- AC-11.3: o usuário anexa um comentário ao destaque.
- AC-11.4: com hover ou clique/toque no trecho destacado, a interface mostra o comentário.
- AC-11.5: destaques e comentários têm coordenadas (`start_offset`, `end_offset`) validadas contra o texto visível retornado ao parceiro.

## Arquitetura

- Frontend: Next.js + TypeScript (PWA).
- Backend: Django + DRF.
- Persistência: PostgreSQL.
- Autenticação: sessões seguras com cookie HttpOnly / Django Authentication.
- ORM e validação: Django ORM com serializers próprios para higienização e truncamento de texto no servidor.

## Modelo de dados

### `entries` (registros diários)
- `id` UUID PK
- `space_id` FK spaces
- `author_id` FK users
- `entry_date` DATE
- `body` TEXT (conteúdo integral original)
- `visibility_type` enum (`full`, `private`, `partial`)
- `visible_start_offset` INTEGER nullable
- `visible_end_offset` INTEGER nullable
- `status` enum (`draft`, `submitted`)
- `submitted_at` DateTime nullable

### `entry_highlights` (destaques no texto visível)
- `id` UUID PK
- `entry_id` FK entries
- `author_id` FK users (quem destacou)
- `start_offset` INTEGER
- `end_offset` INTEGER
- `highlighted_text` TEXT
- `created_at` DateTime

### `entry_comments` (comentários nos destaques)
- `id` UUID PK
- `highlight_id` FK entry_highlights
- `author_id` FK users
- `comment_text` TEXT
- `created_at` DateTime, `updated_at` DateTime

## Roadmap

### Fase 1 — Fundação e Django
- [ ] T0101 — Projeto Django + DRF com PostgreSQL via Docker Compose.
- [ ] T0102 — Testes do Django e health check.

### Fase 2 — Autenticação, espaços e convites
- [ ] T0201 — Autenticação nativa Django (sessions / cookies HttpOnly).
- [ ] T0202 — Espaços e convites (máximo 2 membros).

### Fase 3 — Escrita, visibilidade parcial e privada
- [ ] T0301 — Modelo `entries` e migrações.
- [ ] T0302 — Lógica de visibilidade no backend (`full`, `private`, `partial`).
- [ ] T0303 — API de leitura com filtragem/truncamento rígido no servidor.
- [ ] T0304 — Interface para seleção de trecho e modo de visibilidade.

### Fase 4 — Destaques e comentários (estilo Kindle)
- [ ] T0401 — Modelos `entry_highlights` e `entry_comments`.
- [ ] T0402 — Endpoints de criação e listagem de destaques e comentários.
- [ ] T0403 — Componente de seleção de texto, highlight e hover/popover de comentário.

### Fase 5 — Fotos, PWA e lembretes push
- [ ] T0501 — Upload privado de fotos manuscritas via Django.
- [ ] T0502 — PWA e agendamento de Web Push.
