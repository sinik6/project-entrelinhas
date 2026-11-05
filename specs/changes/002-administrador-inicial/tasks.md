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
  - Estado: publicado; 429 visto no ar (2026-11-03); login do dono confirmado (2026-11-03); **falta** ver um segundo deploy manter a conta

## Onda 4 — Fechamento
- [x] T-4.1 Atualizar `traceability.md` e rodar o `sdd_lint` (XS)
  - Req: todos
  - Verifica: `python ~/.claude/skills/spec-driven-dev/scripts/sdd_lint.py . --code backend` sem erro
- [ ] T-4.2 Verificação independente, `validation.md` (G5) e arquivamento em `specs/system/base.md` junto da 001 (S)
  - Req: todos
  - Verifica: validation.md sem placeholders e com veredito

## Onda 5 — Correções da auditoria independente (2026-11-03)
Origem: `auditoria-independente.md`. Decisões de spec tomadas pelo agente por delegação do dono (ver `requirements.md`, esclarecimentos).
- [x] T-5.1 A1: `.env.production` com aspas simples, `valor()` tira as aspas e recusa-se aspa no valor (S)
  - Req: CTL-8, NFR-SEC-1
  - Arquivos: `.github/workflows/deploy.yml`, `infra/deploy.sh`, `backend/tests/test_pipeline.py`
  - Verifica: `pytest tests/test_pipeline.py -k ctl_8`; bloco real do workflow executado com `jq`; `docker compose config` sem aviso
- [x] T-5.2 A2: testes qualificados por mudança (`[001]`/`[002]`) e CTL-2 citado nas docstrings (XS)
  - Req: CTL-2
  - Arquivos: `backend/tests/test_pipeline.py`, `backend/apps/common/tests/test_administrador_inicial.py`
  - Verifica: `sdd_lint.py . --code backend` sem erro
- [x] T-5.3 M1: testes do mínimo de 12, senha comum, senha parecida e senha de 12 aceita (S)
  - Req: REQ-2.2, PROP-2
  - Arquivos: `backend/apps/common/tests/test_administrador_inicial.py`
  - Verifica: `pytest -k req_2_2`
- [x] T-5.4 M2: ABU-4 reescrito com a semântica real do balde, e medido no ar (XS)
  - Req: ABU-4, CTL-6
  - Arquivos: `specs/changes/002-administrador-inicial/requirements.md`
  - Verifica: 7 `POST` no domínio (5 passam, 2 recusados), depois 3 no IP aceitos (balde próprio)
- [x] T-5.5 M3: `administrador_inicial --verificar` antes de parar a API (M)
  - Req: REQ-2.5, CTL-10
  - Arquivos: `backend/apps/common/services.py`, `backend/apps/common/management/commands/administrador_inicial.py`, `infra/deploy.sh`
  - Verifica: `pytest -k "req_2_5"`
- [x] T-5.6 M4 e M5: `VARS_JSON` por `env`, recusa de variable com nome de segredo, última ocorrência vale (S)
  - Req: CTL-9
  - Arquivos: `.github/workflows/deploy.yml`, `infra/deploy.sh`
  - Verifica: `pytest -k ctl_9`; os 4 casos do bloco do workflow executados com `jq`
- [x] T-5.7 B1, B2 e B5: teste da corrida, teste do hasher de produção, validação de nome e e-mail (S)
  - Req: PROP-1, NFR-SEC-2, REQ-2.3
  - Arquivos: `backend/apps/common/services.py`, `backend/tests/test_configuracao.py`, `backend/apps/common/tests/test_administrador_inicial.py`
  - Verifica: `pytest -k "corrida or hasher or invalido"`
- [x] T-5.8 Segunda verificação independente, por agente específico, sobre as correções (S)
  - Req: todos
  - Verifica: relatório `auditoria-independente-2.md` entregue (veredito: apto com ressalvas; 2 ALTA, 7 MÉDIA, 8 BAIXA). Os achados foram tratados na onda 6

## Onda 6 — Correções da 2ª auditoria independente (2026-11-03)
Origem: `auditoria-independente-2.md`.
- [x] T-6.1 ALTA-1: testes que detectam as mutações de infra: `deploy.sh` executado com `docker` falso, bloco do workflow executado com `jq`, `env_file`, `|| true`, argv, prioridade e demais rótulos do login (L)
  - Req: CTL-4, CTL-8, CTL-9, CTL-10, REQ-2.4, REQ-2.5, NFR-SEC-1, ABU-4, CTL-6
  - Arquivos: `backend/tests/test_deploy_script.py`, `backend/tests/test_workflow_env.py`, `backend/tests/test_pipeline.py`
  - Verifica: `pytest tests/` local (bash do Git) e num contêiner Linux com `jq`; as mutações da auditoria rodadas contra os testes novos
- [x] T-6.2 MÉDIA-1: o contêiner de `run` sai com `-l traefik.enable=false`, para não entrar no balanceador (XS)
  - Req: CTL-10
  - Arquivos: `infra/deploy.sh`
  - Verifica: `test_ctl_10_todo_run_do_deploy_desliga_os_rotulos_do_traefik`, `test_req_2_5_todo_run_do_deploy_sai_sem_rotulos_do_traefik`
- [x] T-6.3 MÉDIA-3: testes renomeados para `test_ctl_8_*` e `test_ctl_9_*`; citações dos documentos conferidas (XS)
  - Req: CTL-8, CTL-9
  - Verifica: `pytest -k ctl_8` e `-k ctl_9` selecionam testes
- [x] T-6.4 MÉDIA-4: o workflow recusa `POSTGRES_PASSWORD` com cifrão ou espaço seguido de cerquilha, antes de tocar na VPS (XS)
  - Req: CTL-8
  - Arquivos: `.github/workflows/deploy.yml`
  - Verifica: `test_ctl_8_senha_do_banco_que_mudaria_com_as_aspas_derruba_o_passo`
- [x] T-6.5 MÉDIA-6: ABU-1 provado em todos os caminhos de erro, com `capsys` (S)
  - Req: ABU-1, NFR-SEC-1
  - Arquivos: `backend/apps/common/tests/test_administrador_inicial.py`
  - Verifica: `pytest -k abu_1`
- [x] T-6.6 BAIXAS: normalização NFKC, nome sem distinção de caixa, aviso de superusuário inativo, variables sem quebra de linha, ABU-4 reescrito, hasher real de produção (S)
  - Req: REQ-1.2, ABU-2, REQ-1.4, CTL-9, ABU-4, NFR-SEC-2
  - Arquivos: `backend/apps/common/services.py`, `backend/apps/common/management/commands/administrador_inicial.py`, `.github/workflows/deploy.yml`, `backend/tests/test_configuracao.py`
  - Verifica: `pytest -k "unicode or caixa or inativo or hasher or quebra"`
- [x] T-6.7 MÉDIA-5: `validation.md`, `traceability.md` e `design.md` atualizados com o que foi de fato executado (S)
  - Req: todos
  - Verifica: `sdd_lint.py . --code backend` sem erro
- [x] T-6.8 Ratificação do usuário: riscos aceitos pelo agente (`threat-model.md`), decisões de spec desta onda e revisão de CI, deploy e Traefik (XS, do usuário)
  - Req: todos
  - Verifica: o usuário confirma ou corrige cada linha de "Riscos aceitos"
  - Estado: ratificado em 2026-11-03 ("Aprovo e ratifico")

## Revisão do usuário
- [x] Criar `ADMIN_USUARIO`, `ADMIN_EMAIL` e `SENHA_ADMIN_INICIAL` no ambiente `production` antes do push da T-3.2 (feito em 2026-10-28).
- [x] Conferir no navegador que o login do Admin funciona com a conta criada (feito em 2026-11-03).
- [ ] Confirmar que o `POSTGRES_PASSWORD` do ambiente `production` não tem cifrão nem espaço seguido de cerquilha (o workflow passa a recusar; ver T-6.4).
- [x] Ratificar os riscos aceitos pelo agente (T-6.8), feito em 2026-11-03.
