---
id: 001-base-do-projeto
status: rascunho
veredito: parcial
---

# Validação — Base do projeto

Evidência do que foi **realmente executado**. A mudança continua aberta: faltam as tarefas T-1.5, T-3.2, T-3.3,
T-4.1 e T-4.2.

## Ambiente
2026-10-23 · máquina local (Windows), PostgreSQL 17 descartável em porta 55433 (container apagado depois) ·
commit base `d511cbc`, mais as alterações desta reestruturação ainda sem commit.

## Critério → evidência
| ID | Como foi provado | Resultado |
|---|---|---|
| REQ-1.1 | `test_req_1_1_health_responde_ok_sem_login` (integração) | ✔ passou |
| REQ-1.2 | `test_req_1_2_health_falha_quando_banco_nao_responde` (consulta forçada a falhar) | ✔ passou |
| REQ-2.1 | `test_req_2_1_producao_recusa_subir_sem_secret_key` (processo isolado) | ✔ passou |
| REQ-3.1 | CI escrito em `.github/workflows/ci.yml`; execução no GitHub **não conferida** | pendente |
| REQ-3.2 | `deploy.yml` escrito; deploy **não executado** | pendente |
| REQ-3.3 | conferência pública está em `deploy.sh`; **não executado** | pendente |
| REQ-3.4 | idem | pendente |
| REQ-3.5 | `test_req_3_5_backup_antes_das_migracoes` (lê o script como texto) | ✔ passou (texto) |
| REQ-3.6 | `test_req_3_6_guarda_so_os_10_backups_mais_novos` (texto) | ✔ passou (texto) |
| REQ-4.1 | `docker compose config` válido; `docker compose up --build` **não executado** | pendente |
| NFR-SEC-1 | `test_nfr_sec_1_permissao_padrao_exige_autenticacao` | ✔ passou |
| NFR-SEC-2 | `test_ctl_2_segredos_fora_do_rsync` (texto) | ✔ passou (texto) |
| ABU-1 | `test_abu_1_deploy_so_apos_ci_aprovado_na_main` (texto) | ✔ passou (texto) |
| ABU-2 | `test_abu_2_deploy_aborta_sem_segredo` (texto) | ✔ passou (texto) |
| ABU-3 | `test_abu_3_deploy_confere_rede_antes_de_parar_a_api` (texto) | ✔ passou (texto) |
| PROP-1 | `test_prop_1_rotas_sem_login_estao_na_lista_publica` | ✔ passou |

## Checagens gerais
| Checagem | Comando | Resultado |
|---|---|---|
| Suíte completa | `uv run pytest --create-db` | 11 passaram |
| Lint / formato | `uv run ruff check . && uv run ruff format --check .` | ok (22 arquivos) |
| Checagens do Django | `manage.py check` e `makemigrations --check --dry-run` | ok (2026-10-19; settings sem mudança desde então) |
| Produção | `manage.py check --deploy --fail-level WARNING` com settings de produção | ok (2026-10-19) |
| Imagem | `docker build backend` | ok (2026-10-19) |
| Compose de produção | `docker compose -f docker-compose.deploy.yml config` | ok (2026-10-19) |
| Script de deploy | `bash -n infra/deploy.sh` | ok (2026-10-19) |
| Specs | `sdd_lint.py . --code backend` | 0 erros · 7 avisos (REQ-3.1 a REQ-3.4, REQ-4.1, CTL-4, CTL-7: sem teste automático; provas no deploy e na conferência manual) |

## Verificação independente
Ainda não feita (T-4.2).

## Não verificado
- Execução do CI no GitHub e do deploy na VPS (REQ-3.1 a REQ-3.4), incluindo o certificado do domínio.
- `docker compose up --build` completo (REQ-4.1).
- Os testes marcados "texto" provam que a regra está escrita, não que a VPS a cumpre.
- `PROP-1` foi visto passando, mas não foi visto falhando com uma rota pública fora da lista (sem mutação).
- CTL-4 (nomes únicos na rede) e CTL-7 (chave SSH dedicada) dependem de conferência manual.
