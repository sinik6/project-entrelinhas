# Rastreabilidade — 002-administrador-inicial

Os testes da 002 levam `[002]` na docstring: REQ, ABU e CTL são provisórios por mudança e se repetem na 001.
O `sdd_lint` não separa as mudanças; a cobertura da 002 foi conferida por mutação (ver `validation.md`).

| ID | Descrição curta | Tarefas | Testes / evidência | Status |
|---|---|---|---|---|
| REQ-1.1 | cria o superusuário quando não existe | T-1.1, T-2.2, T-3.1 | `test_req_1_1_cria_superusuario_quando_nao_existe` | ✔ |
| REQ-1.2 | usuário existente não muda | T-1.1, T-2.2, T-6.6 | `test_req_1_2_usuario_existente_nao_muda`, `…_forma_unicode_nao_normalizada_*`, `…_so_difere_na_caixa_*` | ✔ em teste; 2º deploy não visto |
| REQ-1.3 | conta criada entra no Admin | T-1.1, T-2.2, T-3.2 | `test_req_1_3_conta_criada_entra_no_admin`; login do dono no ar | ✔ em teste e no ar |
| REQ-1.4 | superusuário inativo avisa sem alterar | T-6.6 | `test_req_1_4_superusuario_inativo_avisa_sem_alterar` | ✔ em teste; não visto no ar |
| REQ-2.1 | sem senha, recusa | T-1.1, T-2.2 | `test_req_2_1_sem_senha_recusa_e_nao_cria` | ✔ |
| REQ-2.2 | senha fora da política, recusa | T-1.1, T-2.1, T-2.2, T-5.3 | `test_req_2_2_*` (3 testes, o motivo certo em cada caso) | ✔ em teste e no ar |
| REQ-2.3 | nome ou e-mail ausente ou inválido, recusa | T-1.1, T-2.2, T-3.1, T-5.7 | `test_req_2_3_*` (2 testes) | ✔ |
| REQ-2.4 | erro depois de parar a API mantém a API parada | T-1.2, T-2.3, T-3.2, T-6.1 | `test_req_2_4_criacao_recusada_aborta_com_a_api_parada` (`deploy.sh` executado), `test_req_2_4_administrador_entre_migrate_e_subida`; no ar | ✔ em teste e no ar |
| REQ-2.5 | conferir a configuração antes de parar a API | T-5.5, T-6.1 | `test_req_2_5_*` (7 testes, entre eles o `deploy.sh` executado com `docker` falso) | ✔ em teste; não visto no ar |
| NFR-SEC-1 | senha fora de repo, logs e ambiente da API | T-1.1, T-2.2, T-2.3, T-5.1, T-6.1, T-6.5 | `test_nfr_sec_1_*`, `test_ctl_4_*`, `test_ctl_8_*`, `test_req_2_5_deploy_ok_*` | ✔ em teste; log do Actions não lido |
| NFR-SEC-2 | senha só como hash | T-1.1, T-2.2, T-5.7, T-6.6 | `test_nfr_sec_2_senha_gravada_so_como_hash`, `test_nfr_sec_2_producao_usa_hasher_forte_por_padrao` | ✔ |
| ABU-1 | senha fora da saída e dos logs | T-1.1, T-2.2, T-6.5 | `test_abu_1_*` (4 testes, 5 caminhos de erro) | ✔ |
| ABU-2 | usuário comum não é promovido | T-1.1, T-2.2, T-5.7, T-6.6 | `test_abu_2_*` (3 testes) | ✔ |
| ABU-3 | senha vazia ou só espaços, recusa | T-1.1, T-2.2 | `test_abu_3_senha_vazia_ou_so_espacos_recusa` | ✔ |
| ABU-4 | balde de 5 fichas, 1 a cada 12 s | T-1.2, T-2.4, T-3.2, T-5.4, T-6.1, T-6.6 | `test_abu_4_login_do_admin_tem_balde_de_5_fichas_por_minuto`; medido no ar | ✔ (texto) e no ar |
| PROP-1 | repetir não duplica nem troca a senha | T-1.1, T-2.2, T-5.7 | `test_prop_1_*` (3 testes, duas corridas simuladas) | ✔ (exemplos) |
| PROP-2 | senha recusada nunca cria usuário | T-1.1, T-2.2, T-5.3 | `test_req_2_2_*` | ✔ (exemplos) |

Cadeia de segurança: THR → CTL → teste

| Ameaça | Controle | Requisito | Teste | Status |
|---|---|---|---|---|
| THR-1 | CTL-1 | ABU-2 | `test_abu_2_*` (3 testes) | ✔ |
| THR-2 | CTL-2 | REQ-2.1, REQ-2.2, ABU-3 | `test_req_2_1_*`, `test_req_2_2_*`, `test_abu_3_*` | ✔ |
| THR-3 | CTL-3 | ABU-1, NFR-SEC-1 | `test_abu_1_*`, `test_nfr_sec_1_*` | ✔ |
| THR-4 | CTL-4 | NFR-SEC-1 | `test_ctl_4_*`, `test_req_2_5_deploy_ok_*` | ✔ em teste |
| THR-5 | CTL-5 | NFR-SEC-2 | `test_nfr_sec_2_*` (2 testes); texto em claro no `.env.production` é risco aceito pelo agente | ✔; risco pendente de ratificação |
| THR-6 | CTL-6 | ABU-4 | `test_abu_4_*`; medido no ar de um endereço | ✔ (texto) e no ar |
| THR-8 | CTL-8 | NFR-SEC-1, ABU-1 | `test_ctl_8_*` (`valor()`, bloco do workflow com `jq`, `docker compose config` sem aviso) | ✔ em teste; Actions não visto |
| THR-9 | CTL-9 | NFR-SEC-1 | `test_ctl_9_*` (texto e bloco do workflow com `jq`) | ✔ em teste; Actions não visto |
| THR-10 | CTL-10 | REQ-2.5 | `test_req_2_5_*`, `test_ctl_10_*` (`deploy.sh` executado) | ✔ em teste; Traefik da VPS não verificado |

Legenda: "✔ em teste" = executado, mas em ambiente de teste (Windows com Git Bash e contêiner Linux), não na VPS nem no Actions.
"✔ (texto)" = o teste prova que a regra está escrita, não que o Traefik a cumpre.
PROP-1 e PROP-2 são testes por exemplos (parametrizados), não property-based: não há biblioteca de geração de casos no projeto.
A numeração dos controles novos começa em CTL-8 e THR-8 para não colidir com os da 001, que vão até 7.
