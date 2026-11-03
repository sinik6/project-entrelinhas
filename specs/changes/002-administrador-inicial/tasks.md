---
id: 002-administrador-inicial
status: em-revisao
---

# Tarefas — Administrador inicial criado pelo deploy

Legenda: `[P]` paralelizável · teste antes da implementação · cada tarefa com `Req:` e `Verifica:` · tamanho XS/S/M.
Estratégia de fatiamento: risco primeiro (testes do comando e da senha), depois pipeline e limite de tentativas.
Tracker externo: nenhum.

## Onda 1 — Testes primeiro (devem falhar)
- [x] T-1.1 Testes de integração do comando `administrador_inicial` (M)
  - Req: REQ-1.1, REQ-1.2, REQ-1.3, REQ-2.1, REQ-2.2, REQ-2.3, ABU-1, ABU-2, ABU-3, NFR-SEC-1, NFR-SEC-2, PROP-1, PROP-2, CTL-1, CTL-3, CTL-5
  - Arquivos: `backend/apps/common/tests/test_administrador_inicial.py`
  - Verifica: `uv run pytest apps/common/tests/test_administrador_inicial.py` → vermelho (comando inexistente). Visto: 24 falhas nos testes novos, 11 antigos passando
- [x] T-1.2 [P] Testes de contrato do pipeline e do compose (S)
  - Req: REQ-2.4, CTL-4, ABU-4, CTL-6
  - Arquivos: `backend/tests/test_pipeline.py`
  - Verifica: `uv run pytest tests/test_pipeline.py` → vermelho nos casos novos

## Onda 2 — Implementação
- [x] T-2.1 Política de senhas do sistema, mínimo de 12 (XS)
  - Req: REQ-2.2, CTL-2
  - Arquivos: `backend/config/settings/base.py`
  - Verifica: `uv run python manage.py check` limpo; casos de senha fraca de T-1.1 passam a falhar só por falta do comando
  - Depende: T-1.1
- [x] T-2.2 Service e comando `administrador_inicial` (M)
  - Req: REQ-1.1, REQ-1.2, REQ-1.3, REQ-2.1, REQ-2.2, REQ-2.3, ABU-1, ABU-2, ABU-3, NFR-SEC-1, NFR-SEC-2, PROP-1, PROP-2, CTL-1, CTL-3, CTL-5
  - Arquivos: `backend/apps/common/services.py`, `backend/apps/common/management/commands/administrador_inicial.py`
  - Verifica: `uv run pytest apps/common/tests/test_administrador_inicial.py` → verde
  - Depende: T-1.1, T-2.1
- [x] T-2.3 [P] Chamada no `deploy.sh` e segredo obrigatório no workflow (S)
  - Req: REQ-2.4, CTL-4, NFR-SEC-1
  - Arquivos: `infra/deploy.sh`, `.github/workflows/deploy.yml`
  - Verifica: `bash -n infra/deploy.sh`; casos de REQ-2.4 e CTL-4 de T-1.2 passam
  - Depende: T-1.2
- [x] T-2.4 [P] Limite de 5 tentativas por minuto no login do Admin, em rótulos do compose (S)
  - Req: ABU-4, CTL-6
  - Arquivos: `docker-compose.deploy.yml`
  - Verifica: `docker compose -f docker-compose.deploy.yml config` válido; caso de ABU-4 de T-1.2 passa
  - Depende: T-1.2

### Checkpoint: depois da onda 2
- suíte verde · lint limpo · compose de produção válido · revisão humana do `deploy.sh` e dos rótulos

## Onda 3 — Publicação
- [x] T-3.1 Criar no ambiente `production` as variables `ADMIN_USUARIO` e `ADMIN_EMAIL` e o secret `SENHA_ADMIN_INICIAL` (XS, feito pelo usuário)
  - Req: REQ-1.1, REQ-2.3
  - Verifica: o deploy não aborta por valor ausente
- [ ] T-3.2 Commit, push, deploy e conferência no ar (S)
  - Req: REQ-1.3, REQ-2.4, ABU-4
  - Verifica: o usuário entra no Admin; 6 `POST` seguidos em `/entrelinhas/admin/login/` terminam em 429; segundo deploy não altera a conta
  - Estado: publicado; 429 visto no ar (2026-11-03); **faltam** o login do dono e ver um segundo deploy

## Onda 4 — Fechamento
- [x] T-4.1 Atualizar `traceability.md` e rodar o `sdd_lint` (XS)
  - Req: todos
  - Verifica: `python ~/.claude/skills/spec-driven-dev/scripts/sdd_lint.py . --code backend` sem erro
- [ ] T-4.2 Verificação independente, `validation.md` (G5) e arquivamento em `specs/system/base.md` junto da 001 (S)
  - Req: todos
  - Verifica: validation.md sem placeholders e com veredito

## Revisão do usuário
- [ ] Criar `ADMIN_USUARIO`, `ADMIN_EMAIL` e `SENHA_ADMIN_INICIAL` no ambiente `production` antes do push da T-3.2 (sem isso o deploy aborta, e é o comportamento previsto).
- [ ] Conferir no navegador que o login do Admin funciona com a conta criada.
