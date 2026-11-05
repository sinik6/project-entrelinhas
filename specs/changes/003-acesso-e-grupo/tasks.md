---
id: 003-acesso-e-grupo
status: em-revisao
---

# Tarefas — Contas, perfil, grupo de escrita, convite e casca do front

Legenda: `[P]` paralelizável · teste antes da implementação · cada tarefa com `Req:` e `Verifica:` · tamanho XS/S/M/L.
Estratégia de fatiamento: risco primeiro (autenticação, convite e concorrência no backend), depois a infra e por fim o front.
Tracker externo: nenhum. Os testes levam `[003]` na docstring; nomes planejados estão em `design.md`, seção 10.

## Onda 1 — Backend: testes primeiro (devem falhar)
- [x] T-1.1 Testes da regra de cor: formato, contraste mínimo de 3 para 1 nos dois fundos e diferença da cor do parceiro (S)
  - Req: REQ-4.3, REQ-4.4, REQ-4.5, PROP-1
  - Arquivos: `backend/apps/acesso/tests/test_cor.py`
  - Verifica: `uv run pytest apps/acesso/tests/test_cor.py` → vermelho. Visto: `ModuleNotFoundError` (o app ainda não existia), antes de qualquer código
- [x] T-1.2 [P] Testes da autenticação: token de proteção, entrar, sair, rotas públicas, CSRF em rota anônima, cookies, respostas iguais (M)
  - Req: REQ-1.1, REQ-1.2, REQ-1.3, REQ-1.4, ABU-2, ABU-4, NFR-SEC-1, PROP-4, CTL-12, CTL-15, CTL-16, CTL-18
  - Arquivos: `backend/apps/acesso/tests/test_autenticacao.py`
  - Verifica: `uv run pytest apps/acesso/tests/test_autenticacao.py` → vermelho
- [x] T-1.3 [P] Testes de perfil e grupo: perfil, nome e cor, troca de senha, criar grupo, perfil incompleto, nome e cor do parceiro, isolamento (M)
  - Req: REQ-2.1, REQ-2.2, REQ-2.4, REQ-4.1, REQ-4.2, REQ-4.6, REQ-4.7, REQ-4.8, REQ-4.9, NFR-SEC-3, CTL-17
  - Arquivos: `backend/apps/acesso/tests/test_perfil_e_grupo.py`
  - Verifica: `uv run pytest apps/acesso/tests/test_perfil_e_grupo.py` → vermelho
- [x] T-1.4 [P] Testes do convite: gerar, invalidar o anterior, expirar, aceitar, respostas iguais, grupo cheio, código em hash e **aceites simultâneos com threads** (M)
  - Req: REQ-2.3, REQ-3.1, REQ-3.2, REQ-3.3, REQ-3.4, REQ-3.5, REQ-3.6, REQ-3.7, ABU-3, NFR-SEC-2, PROP-2, PROP-3, CTL-13, CTL-14
  - Arquivos: `backend/apps/acesso/tests/test_convite.py`
  - Verifica: `uv run pytest apps/acesso/tests/test_convite.py` → vermelho

## Onda 2 — Backend: implementação
- [x] T-2.1 App `acesso`: modelos `Grupo`, `Perfil`, `Convite`, índice único parcial do convite pendente e índice único em `lower(email)` (M)
  - Req: REQ-2.3, REQ-3.2, CTL-14
  - Arquivos: `backend/apps/acesso/models.py`, `backend/apps/acesso/migrations/`
  - Verifica: `makemigrations --check`; `migrate` e `migrate zero` (reversível)
  - Depende: T-1.3, T-1.4
- [x] T-2.2 `domain.py` da cor: contraste WCAG e diferença de cor (CIE76), constantes calibráveis (S)
  - Req: REQ-4.3, REQ-4.4, REQ-4.5, PROP-1
  - Arquivos: `backend/apps/acesso/domain.py`
  - Verifica: `pytest apps/acesso/tests/test_cor.py` → verde
  - Depende: T-1.1
- [x] T-2.3 Autenticação: backend por e-mail, classe que sempre exige CSRF, cookies com nome e caminho próprios, rotas `csrf`, `entrar`, `sair` e a lista de rotas públicas (M)
  - Req: REQ-1.1, REQ-1.2, REQ-1.3, REQ-1.4, ABU-2, ABU-4, NFR-SEC-1, PROP-4, CTL-12, CTL-15, CTL-16, CTL-18
  - Arquivos: `backend/apps/acesso/`, `backend/config/settings/base.py`, `backend/config/api_v1.py`, `backend/tests/test_rotas_publicas.py`
  - Verifica: `pytest apps/acesso/tests/test_autenticacao.py tests/test_rotas_publicas.py` → verde
  - Depende: T-1.2, T-2.1
- [x] T-2.4 Perfil e grupo: services e views de perfil, senha, criar e consultar grupo, com consultas sempre filtradas pelo grupo (M)
  - Req: REQ-2.1, REQ-2.2, REQ-2.4, REQ-4.1, REQ-4.2, REQ-4.6, REQ-4.7, REQ-4.8, REQ-4.9, NFR-SEC-3, CTL-17
  - Arquivos: `backend/apps/acesso/services.py`, `serializers.py`, `views.py`, `urls.py`
  - Verifica: `pytest apps/acesso/tests/test_perfil_e_grupo.py` → verde
  - Depende: T-1.3, T-2.2, T-2.3
- [x] T-2.5 Convite: gerar com `select_for_update`, hash do código, aceitar de forma atômica, respostas iguais (M)
  - Req: REQ-2.3, REQ-3.1, REQ-3.2, REQ-3.3, REQ-3.4, REQ-3.5, REQ-3.6, REQ-3.7, ABU-3, NFR-SEC-2, PROP-2, PROP-3, CTL-13, CTL-14
  - Arquivos: `backend/apps/acesso/services.py`, `views.py`, `urls.py`
  - Verifica: `pytest apps/acesso/tests/test_convite.py` → verde, inclusive o teste com threads
  - Depende: T-1.4, T-2.4

### Checkpoint: depois da onda 2
- suíte verde · lint limpo · `check --deploy` limpo · contrato `openapi.yaml` conferido contra as rotas · revisão humana
- Feito em 2026-11-03: 171 testes passam (12 pulados sem `jq`), ruff e `check --deploy` limpos, migração `acesso` vai e volta, `test_ctl_18_o_contrato_cobre_todas_as_rotas_e_so_elas` verde, 23 de 24 mutações do backend detectadas (a que sobra é equivalente). **Falta a revisão humana.**

## Onda 3 — Infra e front em Flutter
- [x] T-3.1 [P] Testes de contrato da infra: rotas e limite de login no Traefik, nginx com CSP, SDK com SHA-256 (S)
  - Req: ABU-1, CTL-11, CTL-19, CTL-20
  - Arquivos: `backend/tests/test_pipeline.py`, `backend/tests/test_deploy_script.py`
  - Verifica: `pytest tests/` → vermelho nos casos novos
- [x] T-3.2 Infra: `infra/nginx/entrelinhas.conf`, `infra/web.Dockerfile`, `frontend/Dockerfile` (SDK), serviço `entrelinhas-web` e rótulos do Traefik, `deploy.sh` e CI do Flutter (L)
  - Req: ABU-1, CTL-11, CTL-19, CTL-20
  - Arquivos: `infra/`, `frontend/Dockerfile`, `docker-compose.deploy.yml`, `.github/workflows/ci.yml`, `.github/workflows/deploy.yml`
  - Verifica: `docker compose config`; `docker build` do web; `pytest tests/` verde
  - Depende: T-3.1
- [x] T-3.3 Testes de widget do Flutter: entrar, criar conta pelo convite, perfil, grupo, erros em português, perfil incompleto (M)
  - Req: REQ-5.1, REQ-5.2, REQ-5.3, REQ-5.4, REQ-5.5
  - Arquivos: `frontend/test/`
  - Verifica: `flutter test` no contêiner → vermelho
- [x] T-3.4 Front: `shared/api` (cliente com token de proteção), `app` (rotas por fragmento), `features/acesso`, `features/perfil`, `features/grupo`, tema claro e escuro (L)
  - Req: REQ-5.1, REQ-5.2, REQ-5.3, REQ-5.4, REQ-5.5, NFR-A11Y-1, NFR-RESP-1
  - Arquivos: `frontend/lib/`, `frontend/pubspec.yaml`, `frontend/pubspec.lock`
  - Verifica: `flutter analyze` e `flutter test` verdes no contêiner
  - Depende: T-3.3, T-2.5
- [ ] T-3.5 Teste ponta a ponta no navegador, em contêiner, com dois participantes: 360 e 1280 px, claro e escuro, sem rolagem horizontal (M)
  - Estado: feito só em parte (2026-11-05): dono entrou, completou o perfil, criou o grupo e gerou o convite no navegador, em pilha local (360 e 1280 px, escuro e claro, sem rolagem horizontal). Falta o segundo participante aceitando o convite no navegador (coberto por testes de widget e de API, não por navegador) e o escuro/claro em todas as telas.
  - Req: NFR-A11Y-1, NFR-RESP-1, REQ-5.3
  - Arquivos: `frontend/e2e/`
  - Verifica: roteiro e2e verde; relatório de acessibilidade sem violação grave
  - Depende: T-3.4, T-3.2

## Onda 4 — Publicação
- [x] T-4.1 Conferir que `ADMIN_EMAIL` do ambiente `production` é o e-mail com que o dono quer entrar no app (XS, do usuário)
  - Req: REQ-1.1
  - Verifica: o e-mail confere; nenhum segredo novo é necessário
- [ ] T-4.2 (deploy feito; falta o roteiro com as duas pessoas no ar) Commit, push, deploy e conferência no ar: o dono entra, completa o perfil, cria o grupo e gera o convite; a segunda pessoa cria a conta; o login recebe 429 após 5 tentativas (S)
  - Req: REQ-1.1, REQ-2.1, REQ-3.1, REQ-3.4, ABU-1
  - Verifica: roteiro no ar com as duas pessoas; medição do 429 com credenciais falsas
  - Depende: T-3.5, T-4.1

## Onda 5 — Fechamento
- [ ] T-5.1 Atualizar `traceability.md` e rodar o `sdd_lint` (XS)
  - Req: todos
  - Verifica: `sdd_lint.py . --code backend` sem erro
- [ ] T-5.2 Verificação independente por agente específico, `validation.md` (G5) e arquivamento em `specs/system/acesso-espaco.md` (M)
  - Req: todos
  - Verifica: relatório sem achado alto aberto; validation.md sem placeholders e com veredito

## Revisão do usuário
- [ ] Confirmar o e-mail do dono (`ADMIN_EMAIL`) antes do deploy (T-4.1).
- [ ] Testar o fluxo no navegador com a segunda pessoa depois do deploy (T-4.2).
