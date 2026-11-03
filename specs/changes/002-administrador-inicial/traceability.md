# Rastreabilidade — 002-administrador-inicial

| ID | Descrição curta | Tarefas | Testes / evidência | Status |
|---|---|---|---|---|
| REQ-1.1 | cria o superusuário quando não existe | T-1.1, T-2.2, T-3.1 | `test_req_1_1_cria_superusuario_quando_nao_existe` | ✔ |
| REQ-1.2 | usuário existente não muda | T-1.1, T-2.2 | `test_req_1_2_usuario_existente_nao_muda` | ✔ |
| REQ-1.3 | conta criada entra no Admin | T-1.1, T-2.2, T-3.2 | `test_req_1_3_conta_criada_entra_no_admin`; login do usuário | ✔ |
| REQ-2.1 | sem senha, recusa | T-1.1, T-2.2 | `test_req_2_1_sem_senha_recusa_e_nao_cria` | ✔ |
| REQ-2.2 | senha fraca, recusa | T-1.1, T-2.1, T-2.2 | `test_req_2_2_senha_fraca_recusa_e_nao_cria` | ✔ |
| REQ-2.3 | sem usuário ou e-mail, recusa | T-1.1, T-2.2, T-3.1 | `test_req_2_3_sem_usuario_ou_email_recusa` | ✔ |
| REQ-2.4 | erro interrompe o deploy com a API parada | T-1.2, T-2.3, T-3.2 | `test_req_2_4_administrador_entre_migrate_e_subida`; no ar, a recusa deixou a API parada | ✔ (texto) e no ar |
| NFR-SEC-1 | senha fora de repo, logs e ambiente da API | T-1.1, T-2.2, T-2.3 | `test_nfr_sec_1_senha_nao_aparece_na_saida` | ✔ |
| NFR-SEC-2 | senha só como hash | T-1.1, T-2.2 | `test_nfr_sec_2_senha_gravada_so_como_hash` | ✔ |
| ABU-1 | senha fora da saída e dos logs | T-1.1, T-2.2 | `test_abu_1_senha_nao_vai_para_saida_nem_para_log` | ✔ |
| ABU-2 | usuário comum não é promovido | T-1.1, T-2.2 | `test_abu_2_usuario_comum_existente_nao_e_promovido` | ✔ |
| ABU-3 | senha vazia ou só espaços, recusa | T-1.1, T-2.2 | `test_abu_3_senha_vazia_ou_so_espacos_recusa` | ✔ |
| ABU-4 | no máximo 5 tentativas de login por minuto | T-1.2, T-2.4, T-3.2 | `test_abu_4_login_do_admin_tem_limite_de_5_por_minuto`; 429 no ar | ✔ (texto) e no ar |
| PROP-1 | repetir não duplica nem troca a senha | T-1.1, T-2.2 | `test_prop_1_repetir_a_execucao_nao_duplica_nem_troca_senha` | ✔ |
| PROP-2 | senha recusada nunca cria usuário | T-1.1, T-2.2 | `test_req_2_2_senha_fraca_recusa_e_nao_cria` | ✔ |

Cadeia de segurança: THR → CTL → teste

| Ameaça | Controle | Requisito | Teste | Status |
|---|---|---|---|---|
| THR-1 | CTL-1 | ABU-2 | `test_abu_2_usuario_comum_existente_nao_e_promovido` | ✔ |
| THR-2 | CTL-2 | REQ-2.1, REQ-2.2, ABU-3 | `test_req_2_1_…`, `test_req_2_2_…`, `test_abu_3_…` | ✔ |
| THR-3 | CTL-3 | ABU-1, NFR-SEC-1 | `test_abu_1_…`, `test_nfr_sec_1_…` | ✔ |
| THR-4 | CTL-4 | NFR-SEC-1 | `test_ctl_4_senha_nao_entra_no_compose_nem_no_servico_da_api` | ✔ (texto) |
| THR-5 | CTL-5 | NFR-SEC-2 | `test_nfr_sec_2_…`; risco de texto no `.env.production` aceito pelo usuário (2026-10-28) | ✔ |
| THR-6 | CTL-6 | ABU-4 | `test_abu_4_…`; 429 no ar | ✔ (texto) e no ar |

"✔ (texto)": o teste prova que a regra está escrita no compose ou no script, não que o Traefik ou a VPS a cumprem.
PROP-1 e PROP-2 são testes por exemplos (parametrizados), não property-based: não há biblioteca de geração de casos no projeto.
