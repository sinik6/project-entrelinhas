---
id: 002-administrador-inicial
status: rascunho
veredito: parcial
---

# Validação — Administrador inicial criado pelo deploy

Evidência do que foi **realmente executado**. A mudança está no ar, mas continua aberta: falta ver um deploy repetido
deixar a conta como está, e a verificação independente não foi feita.

## Ambiente
Testes: máquina local (Windows), PostgreSQL 17 descartável em porta 55433 · commit `5fe8e66`.
Produção: `https://jpsys.duckdns.org/entrelinhas` na VPS, conferida por `curl` em 2026-10-29 e 2026-11-03.

## Critério → evidência
| ID | Como foi provado | Resultado |
|---|---|---|
| REQ-1.1 | `test_req_1_1_cria_superusuario_quando_nao_existe`; no ar, o deploy com a senha corrigida terminou verde (informado pelo usuário) e o Admin voltou a responder 200 | ✔ (a conta em si não foi vista; ver REQ-1.3) |
| REQ-1.2 | `test_req_1_2_usuario_existente_nao_muda`, `test_prop_1_…` (2 e 5 execuções) | ✔ em teste; **não visto no ar** (precisa de um segundo deploy com a conta já criada) |
| REQ-1.3 | `test_req_1_3_conta_criada_entra_no_admin` (login pelo cliente de teste, 302 e depois 200 no painel) | ✔ em teste e no ar (o dono entrou no Admin com a conta criada, informado em 2026-11-03) |
| REQ-2.1 | `test_req_2_1_sem_senha_recusa_e_nao_cria` (sem senha e senha vazia) | ✔ |
| REQ-2.2 | `test_req_2_2_senha_fraca_recusa_e_nao_cria` (curta, só números, parecida com o usuário); **no ar**: o 1º deploy parou com `Senha recusada pela política de senhas: … pelo menos 12 caracteres` | ✔ em teste e no ar |
| REQ-2.3 | `test_req_2_3_sem_usuario_ou_email_recusa` (4 casos) | ✔ |
| REQ-2.4 | `test_req_2_4_administrador_entre_migrate_e_subida`; **no ar**: com a recusa, o deploy falhou e o Admin respondeu 404 até o deploy seguinte (API parada) | ✔ em teste e no ar |
| NFR-SEC-1 | `test_nfr_sec_1_senha_nao_aparece_na_saida`, `test_ctl_4_…`; o log do deploy colado pelo usuário não traz a senha, só a mensagem de recusa | ✔ |
| NFR-SEC-2 | `test_nfr_sec_2_senha_gravada_so_como_hash` | ✔ |
| ABU-1 | `test_abu_1_senha_nao_vai_para_saida_nem_para_log` (sucesso e erro) | ✔ |
| ABU-2 | `test_abu_2_usuario_comum_existente_nao_e_promovido` | ✔ |
| ABU-3 | `test_abu_3_senha_vazia_ou_so_espacos_recusa` (vazia, 3 e 12 espaços) | ✔ |
| ABU-4 | `test_abu_4_login_do_admin_tem_limite_de_5_por_minuto` (texto) e **no ar**: 8 `POST` seguidos em `/entrelinhas/admin/login/` → 5 respostas 403 (CSRF, credenciais falsas) e **3 respostas 429**; `GET` da página e dos estáticos seguem 200; 65 s depois o `POST` volta a passar | ✔ |
| PROP-1 | repetição de 2 e 5 execuções (por exemplos, não property-based) | ✔ |
| PROP-2 | os três casos de senha fraca nunca criam usuário | ✔ |

## Checagens gerais
| Checagem | Comando | Resultado |
|---|---|---|
| Suíte completa | `uv run pytest --create-db` | 35 passaram |
| Lint / formato | `uv run ruff check . && uv run ruff format --check .` | ok (25 arquivos) |
| Django | `manage.py check` e `makemigrations --check --dry-run` | ok |
| Produção | `manage.py check --deploy --fail-level WARNING` | ok |
| Imagem | `docker build backend` | ok |
| Compose de produção | `docker compose -f docker-compose.deploy.yml config` | ok |
| Script de deploy | `bash -n infra/deploy.sh` e simulação do bloco com `.env.production` de teste (CRLF, variável ausente) | ok |
| Specs | `sdd_lint.py . --code backend` | 0 erros |

## Verificação independente
**Não feita.** A skill pede outro agente ou outra pessoa, sem ver o raciocínio de quem implementou. Quem
escreveu e testou foi o mesmo agente.

## Não verificado
- Segundo deploy com a conta já existente: a saída esperada é `Administrador já existe: <usuário>` (REQ-1.2 no ar).
- O 429 foi testado a partir de um único endereço de origem; não foi testado com vários.
- THR-5 (senha em texto no `.env.production`, modo 600) é risco aceito pelo dono em 2026-10-28, sem mitigação técnica.
- O 1º deploy falhou por senha curta, o que derrubou o Admin por pelo menos 16 horas (do 1º ao 2º deploy, ambos recusados) até a correção. É o comportamento
  da spec, mas o custo ficou à mostra: proposta de checar o tamanho no workflow antes de tocar na VPS segue em aberto.
