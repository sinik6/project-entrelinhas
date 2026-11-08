---
id: 011-recuperacao-de-senha
status: em-revisao
---

# Tarefas — Recuperação de senha por e-mail

Legenda: `[P]` paralelizável · teste antes da implementação · cada tarefa com `Req:` e `Verifica:` · tamanho XS/S/M/L.
Estratégia de fatiamento: risco primeiro (resposta uniforme, token, Host), depois infra e e-mail, depois o front.
Os testes levam `[011]` na docstring ou no nome. Depende da 003 no ar. **Dependência do usuário:** o provedor de e-mail (T-3.1).

## Onda 1 — Backend: testes primeiro (devem falhar)
- [x] T-1.1 Testes do pedido: e-mail com conta, sem conta, maiúsculas e espaços, vazio, mal formado, limite de 3 por hora, resposta idêntica, Host falso, SMTP lento, falha sem vazar, PROP-14 (L)
  - Req: REQ-20.1, REQ-20.2, REQ-20.3, REQ-20.4, REQ-20.5, REQ-20.6, ABU-24, ABU-25, ABU-27, PROP-14, CTL-91, CTL-94, CTL-97
  - Arquivos: `backend/apps/acesso/tests/test_recuperacao_pedido.py`
  - Verifica: `uv run pytest apps/acesso/tests/test_recuperacao_pedido.py` → vermelho
- [x] T-1.2 [P] Testes da redefinição: token válido, vencido (relógio injetado), reutilizado, depois de trocar a senha por outro caminho, `uid` trocado, resposta única, senha fraca mantém o token, sessões encerradas, sem login automático, aviso por e-mail (L)
  - Req: REQ-21.1, REQ-21.2, REQ-21.3, REQ-21.4, REQ-21.5, ABU-26, NFR-REC-2, CTL-93, CTL-95
  - Arquivos: `backend/apps/acesso/tests/test_recuperacao_redefinir.py`
  - Verifica: vermelho
- [x] T-1.3 [P] Atualizar `test_rotas_publicas`: as duas rotas novas entram na lista de públicas e só elas (S)
  - Req: CTL-91
  - Arquivos: `backend/tests/test_rotas_publicas.py`
  - Verifica: vermelho
- [x] T-1.4 [P] Testes de infra: roteadores do Traefik com o balde, variáveis de e-mail exigidas no compose e no `deploy.sh` antes de parar a API, segredo fora de log (M)
  - Req: CTL-92, CTL-93, NFR-REC-1, NFR-REC-4, ABU-25
  - Arquivos: `backend/tests/test_infra_recuperacao.py`
  - Verifica: vermelho

## Onda 2 — Backend: implementação
- [x] T-2.1 ADR-0013 aceito; settings de e-mail e `APP_URL_BASE`, `PASSWORD_RESET_TIMEOUT`; modelo `PedidoRecuperacao` e migração reversível (S)
  - Req: REQ-20.6, REQ-21.2, NFR-REC-1, CTL-96
  - Arquivos: `specs/changes/011-recuperacao-de-senha/adr/ADR-0013-*.md`, `backend/config/settings/`, `backend/apps/acesso/{models}.py`, `backend/apps/acesso/migrations/`
  - Verifica: `makemigrations --check`; `migrate zero`
- [x] T-2.2 Pedido: serviço de recuperação (limite por hora, link com `APP_URL_BASE`, envio em segundo plano, log sem dado sensível) e view pública `POST /auth/recuperacao` (M)
  - Req: REQ-20.1 a REQ-20.6, ABU-24, ABU-25, ABU-27, PROP-14
  - Arquivos: `backend/apps/acesso/{services,views,urls}.py`, `backend/apps/acesso/templates/` (texto dos e-mails)
  - Verifica: `test_recuperacao_pedido.py` verde
  - Depende: T-1.1, T-2.1
- [x] T-2.3 Redefinição: view pública `POST /auth/redefinir` (token, política de senha, encerrar sessões, e-mail de aviso) (M)
  - Req: REQ-21.1 a REQ-21.5, ABU-26
  - Arquivos: `backend/apps/acesso/{services,views,urls}.py`
  - Verifica: `test_recuperacao_redefinir.py` verde; testes da 003 continuam verdes
  - Depende: T-1.2, T-2.1
- [x] T-2.4 Lista de rotas públicas e OpenAPI da 011 com teste de contrato (S)
  - Req: CTL-91, NFR-REC-2
  - Arquivos: `backend/tests/test_rotas_publicas.py`, `specs/changes/011-recuperacao-de-senha/contracts/openapi.yaml`, `backend/tests/test_contrato.py`
  - Verifica: o teste de rotas públicas e o de contrato verdes; a linha `x-estado: planejado` sai do contrato
  - Depende: T-1.3, T-2.2, T-2.3

## Onda 3 — Infra e o que é do usuário
- [ ] T-3.1 (do usuário) Escolher o provedor de e-mail, criar a conta de envio e as credenciais, e criar no GitHub, ambiente `production`, as variáveis `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `DEFAULT_FROM_EMAIL`, `APP_URL_BASE` e o segredo `EMAIL_HOST_PASSWORD`; a senha nunca vai ao chat (XS)
  - Req: NFR-REC-1, CTL-96
  - Verifica: o deploy passa na conferência das variáveis
- [x] T-3.2 Infra: roteadores `entrelinhas-recuperar-*` com o balde de 5 por minuto, variáveis no compose e no `.env.production`, conferência no `deploy.sh`, `limpar_pedidos` no deploy (M)
  - Req: CTL-92, CTL-93, NFR-REC-1, NFR-REC-4, ABU-25
  - Arquivos: `docker-compose.deploy.yml`, `compose.yml`, `infra/deploy.sh`, `.github/workflows/deploy.yml`
  - Verifica: `test_infra_recuperacao.py` verde; `docker compose config`
  - Depende: T-1.4

## Onda 4 — Front
- [x] T-4.1 Testes de widget: botão em Entrar, pedido com confirmação fixa, tela de senha nova, link inválido, erro de senha, token fora da barra de endereço, sem armazenamento, acessibilidade (L)
  - Req: REQ-22.1, REQ-22.2, REQ-22.3, REQ-22.4, REQ-22.5, REQ-22.6, NFR-REC-3
  - Arquivos: `frontend/test/recuperacao_test.dart`, `frontend/test/suporte/api_falsa.dart`
  - Verifica: vermelho
- [x] T-4.2 Front: cliente, telas `#/recuperar` e `#/redefinir/<uid>/<token>`, rotas anônimas, mensagem na tela de entrar (L)
  - Req: REQ-22.1, REQ-22.2, REQ-22.3, REQ-22.4, REQ-22.5, REQ-22.6, NFR-REC-3
  - Arquivos: `frontend/lib/features/acesso/`, `frontend/lib/shared/api/`, `frontend/lib/app/rotas.dart`
  - Verifica: `recuperacao_test.dart` e os testes da 003 verdes; `flutter analyze` limpo
  - Depende: T-4.1, T-2.3

## Onda 5 — Publicação e fechamento
- [ ] T-5.1 Teste no navegador, em contêiner, com SMTP de teste (captura de e-mail local): pedir, abrir o link, redefinir, entrar; link vencido; 360 e 1280 px, claro e escuro (M)
  - Req: REQ-20.1, REQ-21.1, REQ-22.3, NFR-REC-3
  - Verifica: roteiro verde; evidência no `validation.md`
  - Depende: T-4.2, T-2.3
- [ ] T-5.2 Deploy (o dono manda "Commit e push") e conferência no ar com e-mail real: link recebido, senha trocada, aviso recebido, 6º pedido em 1 min → 429 (M)
  - Req: REQ-20.1, REQ-21.1, REQ-21.4, ABU-25
  - Verifica: evidência no `validation.md` (inclui spam e entrega nos dois e-mails)
  - Depende: T-3.1, T-3.2, T-5.1
- [ ] T-5.3 Rastreabilidade, `sdd_lint`, auditoria independente por subagente (foco: enumeração, Host, token, tempo), `validation.md`, arquivamento em `acesso-espaco.md` (M)
  - Req: PROP-14, ABU-24, ABU-26
  - Verifica: lint sem erro; auditoria sem achado grave aberto
