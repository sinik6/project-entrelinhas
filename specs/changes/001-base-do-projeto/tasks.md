---
id: 001-base-do-projeto
status: em-revisao
---

# Tarefas — Base do projeto

Legenda: `[P]` paralelizável · teste antes da implementação · cada tarefa com `Req:` e `Verifica:` · tamanho XS/S/M.
Estratégia de fatiamento: risco primeiro (configuração segura e pipeline), depois publicação.
Tracker externo: nenhum.

## Onda 1 — Fundação
- [x] T-1.1 Projeto Django com settings por ambiente e health check (S)
  - Req: REQ-1.1, REQ-1.2
  - Arquivos: `backend/config/`, `backend/apps/common/`
  - Verifica: `uv run pytest apps/common`
- [x] T-1.2 [P] Produção recusa subir sem chave secreta (XS)
  - Req: REQ-2.1, CTL-3
  - Arquivos: `backend/config/settings/prod.py`, `backend/tests/test_configuracao.py`
  - Verifica: `uv run pytest tests/test_configuracao.py`
- [x] T-1.3 [P] Permissão padrão negada e lista de rotas públicas (XS)
  - Req: NFR-SEC-1, PROP-1, CTL-5
  - Arquivos: `backend/config/settings/base.py`, `backend/tests/test_rotas_publicas.py`
  - Verifica: `uv run pytest tests/test_rotas_publicas.py`
- [x] T-1.4 Ambiente local com `compose.yml` (XS)
  - Req: REQ-4.1
  - Arquivos: `compose.yml`
  - Verifica: `docker compose config`
- [ ] T-1.5 Conferir `docker compose up --build` de ponta a ponta (XS)
  - Req: REQ-4.1
  - Verifica: `curl http://localhost:8010/api/v1/health` devolve `ok`

## Onda 2 — Pipeline
- [x] T-2.1 CI: lint, checagens, testes, build e compose de produção (S)
  - Req: REQ-3.1
  - Arquivos: `.github/workflows/ci.yml`
  - Verifica: leitura do arquivo; execução real na T-3.3
- [x] T-2.2 [P] Compose de produção com nomes únicos e rótulos do Traefik (S)
  - Req: CTL-4, REQ-3.3, REQ-3.4
  - Arquivos: `docker-compose.deploy.yml`
  - Verifica: `docker compose -f docker-compose.deploy.yml config`
- [x] T-2.3 [P] `infra/deploy.sh` com conferência de rede, backup, migrações e verificação pública (M)
  - Req: REQ-3.5, REQ-3.6, ABU-3, CTL-6
  - Arquivos: `infra/deploy.sh`
  - Verifica: `bash -n infra/deploy.sh`
- [x] T-2.4 Workflow de deploy após o CI, com segredos obrigatórios (S)
  - Req: REQ-3.2, ABU-1, ABU-2, CTL-1, CTL-2, NFR-SEC-2
  - Arquivos: `.github/workflows/deploy.yml`
  - Verifica: leitura do arquivo; execução real na T-3.3
- [x] T-2.5 Testes de contrato do pipeline (S)
  - Req: ABU-1, ABU-2, ABU-3, CTL-1, CTL-2, CTL-6, REQ-3.5, REQ-3.6
  - Arquivos: `backend/tests/test_pipeline.py`
  - Verifica: `uv run pytest tests/test_pipeline.py`

### Checkpoint: depois da onda 2
- suíte verde · lint limpo · imagem constrói · revisão humana dos arquivos de deploy

## Onda 3 — Publicação
- [x] T-3.1 Código enviado ao GitHub (`sinik6/project-entrelinhas`, `main`) (XS)
  - Req: REQ-3.1
  - Verifica: `git log origin/main`
- [ ] T-3.2 Ambiente `production` (variáveis e segredos) e chave SSH nova na VPS, feitos por quem é admin (S)
  - Req: CTL-7, ABU-2
  - Verifica: Deploy não aborta por segredo ausente; `authorized_keys` com a linha do projeto
- [ ] T-3.3 Primeiro deploy executado e conferido por domínio e IP (S)
  - Req: REQ-3.1, REQ-3.2, REQ-3.3, REQ-3.4
  - Verifica: `curl -I https://jpsys.duckdns.org/entrelinhas/admin/login/` → 200; `curl -I http://217.216.82.25/entrelinhas/admin/login/` → redirecionamento para https

## Onda 4 — Fechamento
- [ ] T-4.1 Atualizar `traceability.md` e rodar o `sdd_lint` (XS)
  - Req: todos
  - Verifica: `python ~/.claude/skills/spec-driven-dev/scripts/sdd_lint.py . --code backend` sem erro
- [ ] T-4.2 Verificação independente, `validation.md` (G5) e arquivamento em `specs/system/base.md` (S)
  - Req: todos
  - Verifica: validation.md sem placeholders e com veredito

## Revisão do usuário
- [ ] Confirmar as suposições pendentes de `requirements.md` e a lista de decisões em aberto do `capability-map.md`.
- [ ] Aprovar o mapa de capacidades (portão do P3).
