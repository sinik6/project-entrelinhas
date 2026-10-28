# Rastreabilidade — 001-base-do-projeto

| ID | Descrição curta | Tarefas | Testes / evidência | Status |
|---|---|---|---|---|
| REQ-1.1 | health responde ok sem login | T-1.1 | `test_req_1_1_health_responde_ok_sem_login` | ✔ |
| REQ-1.2 | health falha se o banco não responde | T-1.1 | `test_req_1_2_health_falha_quando_banco_nao_responde` | ✔ |
| REQ-2.1 | produção recusa subir sem chave secreta | T-1.2 | `test_req_2_1_producao_recusa_subir_sem_secret_key` | ✔ |
| REQ-3.1 | CI roda lint, checagens, testes e build | T-2.1, T-3.1, T-3.3 | CI verde (informado pelo usuário) | ✔ |
| REQ-3.2 | commit aprovado é publicado na VPS | T-2.4, T-3.3 | primeiro deploy; Admin respondeu 200 | ✔ |
| REQ-3.3 | Admin responde por HTTPS (domínio e IP) | T-2.2, T-3.3 | `curl` 200 por domínio e IP | ✔ |
| REQ-3.4 | HTTP redireciona para HTTPS | T-2.2, T-3.3 | `curl` HTTP → 301 para https | ✔ |
| REQ-3.5 | backup antes das migrações | T-2.3, T-2.5 | `test_req_3_5_backup_antes_das_migracoes` | ✔ (texto) |
| REQ-3.6 | guarda só 10 backups | T-2.3, T-2.5 | `test_req_3_6_guarda_so_os_10_backups_mais_novos` | ✔ (texto) |
| REQ-4.1 | ambiente local em localhost:8010 | T-1.4, T-1.5 | `docker compose up --build` + `curl` | planejado |
| NFR-SEC-1 | autenticação exigida, salvo rotas públicas | T-1.3 | `test_nfr_sec_1_permissao_padrao_exige_autenticacao` | ✔ |
| NFR-SEC-2 | segredos fora do repo e do rsync | T-2.4 | `test_ctl_2_segredos_fora_do_rsync` | ✔ (texto) |
| ABU-1 | CI falhou, não publica | T-2.4, T-2.5 | `test_abu_1_deploy_so_apos_ci_aprovado_na_main` | ✔ (texto) |
| ABU-2 | segredo faltando aborta o deploy | T-2.4, T-2.5, T-3.2 | `test_abu_2_deploy_aborta_sem_segredo` | ✔ (texto) |
| ABU-3 | sem rede do proxy, aborta antes de parar a API | T-2.3, T-2.5 | `test_abu_3_deploy_confere_rede_antes_de_parar_a_api` | ✔ (texto) |
| PROP-1 | rota anônima só se estiver na lista pública | T-1.3 | `test_prop_1_rotas_sem_login_estao_na_lista_publica` | ✔ |

Cadeia de segurança: THR → CTL → teste

| Ameaça | Controle | Requisito | Teste | Status |
|---|---|---|---|---|
| THR-1 | CTL-1 | REQ-3.2, ABU-1 | `test_abu_1_deploy_so_apos_ci_aprovado_na_main` | ✔ (texto) |
| THR-2 | CTL-2 | NFR-SEC-2, ABU-2 | `test_ctl_2_segredos_fora_do_rsync`, `test_abu_2_deploy_aborta_sem_segredo` | ✔ (texto) |
| THR-3 | CTL-3 | REQ-2.1 | `test_req_2_1_producao_recusa_subir_sem_secret_key` | ✔ |
| THR-4 | CTL-4 | — | revisão do compose de produção | planejado |
| THR-5 | CTL-5 | NFR-SEC-1, PROP-1 | `test_prop_1_rotas_sem_login_estao_na_lista_publica` | ✔ |
| THR-6 | CTL-6 | REQ-3.5, ABU-3 | `test_abu_3_…`, `test_req_3_5_…` | ✔ (texto) |
| THR-7 | CTL-7 | — | conferência do `authorized_keys` (T-3.2) | planejado |

"✔ (texto)": o teste prova que a regra está escrita no workflow ou no script, não que a VPS a cumpre.
