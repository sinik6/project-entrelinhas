---
id: 002-administrador-inicial
status: rascunho
veredito: parcial
---

# Validação — Administrador inicial criado pelo deploy

Evidência do que foi **realmente executado**. A mudança continua aberta e **a onda 5 e a onda 6 não estão
commitadas nem implantadas**: o que está no ar é o commit `225324a`. Quando o texto diz "no ar", vale só para o
que já estava nesse commit (criação da conta, política de 12 caracteres, limite de login).

## Ambiente
- Testes: máquina local (Windows, Git Bash) com PostgreSQL 17 descartável em porta 55433 (apagado depois); os testes
  que precisam de `jq` rodaram também num contêiner Linux `python:3.13-slim` com `jq`, que é o ambiente do CI.
- Produção: `https://jpsys.duckdns.org/entrelinhas` na VPS, conferida por `curl` em 2026-10-29 e 2026-11-03.
- Base das alterações desta validação: árvore de trabalho sobre `225324a`, sem commit.

## Critério → evidência
| ID | Como foi provado | Resultado |
|---|---|---|
| REQ-1.1 | `test_req_1_1_cria_superusuario_quando_nao_existe`; no ar, o deploy com a senha corrigida terminou verde (informado pelo usuário) | ✔ em teste; a conta em si foi vista pelo login (REQ-1.3) |
| REQ-1.2 | `test_req_1_2_usuario_existente_nao_muda`, `test_req_1_2_nome_em_forma_unicode_nao_normalizada_acha_a_conta_existente`, `test_req_1_2_nome_que_so_difere_na_caixa_acha_o_superusuario`, `test_prop_1_*` | ✔ em teste; **2º deploy com a conta existente não visto no ar** |
| REQ-1.3 | `test_req_1_3_conta_criada_entra_no_admin`; o dono entrou no Admin (informado em 2026-11-03) | ✔ em teste e no ar |
| REQ-1.4 | `test_req_1_4_superusuario_inativo_avisa_sem_alterar` | ✔ em teste; **não visto no ar** |
| REQ-2.1 | `test_req_2_1_sem_senha_recusa_e_nao_cria` (ausente e vazia) | ✔ |
| REQ-2.2 | `test_req_2_2_senha_fraca_recusa_e_nao_cria` (curta, 11 caracteres, só números, comum, cada uma com o motivo certo), `…_senha_parecida_com_o_usuario_recusa`, `…_senha_de_12_caracteres_forte_e_aceita`; no ar, o 1º deploy parou com "pelo menos 12 caracteres" | ✔ em teste e no ar |
| REQ-2.3 | `test_req_2_3_sem_usuario_ou_email_recusa` (4 casos), `…_usuario_ou_email_invalido_recusa_com_mensagem_limpa` (3 casos) | ✔ |
| REQ-2.4 | `test_req_2_4_criacao_recusada_aborta_com_a_api_parada` (executa o `deploy.sh` com `docker` falso); no ar, a recusa deixou a API parada | ✔ em teste e no ar |
| REQ-2.5 | `test_req_2_5_verificar_valida_sem_tocar_no_banco`, `test_req_2_5_verificar_recusa_configuracao_ruim`, `test_req_2_5_conferencia_recusada_aborta_antes_de_parar_a_api` (executa o `deploy.sh` com `docker` falso: sem `stop` e sem `up`) | ✔ em teste; **não visto no ar** |
| NFR-SEC-1 | `test_nfr_sec_1_senha_nao_aparece_na_saida`, `test_ctl_4_*`, `test_ctl_8_*`, `test_req_2_5_deploy_ok_chama_na_ordem_certa_e_a_senha_so_vai_pelo_ambiente` (a senha não aparece em nenhum argumento) | ✔ em teste; **o log real do Actions não foi lido** |
| NFR-SEC-2 | `test_nfr_sec_2_senha_gravada_so_como_hash`, `test_nfr_sec_2_producao_usa_hasher_forte_por_padrao` (settings de produção, PBKDF2) | ✔ |
| ABU-1 | `test_abu_1_*` (sucesso, 5 caminhos de erro, usuário comum, `--verificar`), com `capsys` e `caplog` | ✔ |
| ABU-2 | `test_abu_2_usuario_comum_existente_nao_e_promovido`, `…_corrida_entre_duas_execucoes_*`, `…_nome_que_so_difere_na_caixa_*` | ✔ |
| ABU-3 | `test_abu_3_senha_vazia_ou_so_espacos_recusa` | ✔ |
| ABU-4 | `test_abu_4_login_do_admin_tem_balde_de_5_fichas_por_minuto` (texto, agora com prioridade, service, tls, entrypoints e middlewares dos dois roteadores); no ar em 2026-11-03: no domínio 5 `POST` passaram e o 6º e o 7º deram 429; logo depois o IP aceitou 5 (balde próprio); 1 ficha voltou em ~13 s | ✔ (texto) e no ar, de **um único endereço de origem** |
| PROP-1 | repetições de 2 e 5 execuções e duas corridas simuladas por `monkeypatch` (não é concorrência real) | ✔ (exemplos) |
| PROP-2 | os casos de senha fraca nunca criam usuário | ✔ (exemplos) |

## Controles de pipeline (CTL-4, 8, 9, 10)
Substituem as provas só de texto da onda 2. Três camadas, todas executadas:
- `test_pipeline.py`: leitura do texto com checagens por linha (sem `|| true`, sem `env_file`, sem senha no argv, prioridade do login maior que a do Admin).
- `test_deploy_script.py`: executa o `infra/deploy.sh` inteiro com `docker` e `curl` falsos (4 cenários).
- `test_workflow_env.py`: executa o bloco real do workflow que gera o `.env.production`, com `bash` e `jq` (12 casos); **só roda onde há `jq`** (pulado nesta máquina; 12 passam no contêiner Linux).
Mutações aplicadas aos arquivos de infra, contra esses testes, no contêiner Linux: **30 de 30 detectadas** (a auditoria
mostrou 8 de 31 detectadas antes). Contra a mesma lista, a única que passou na primeira rodada (`chmod 600` → `644`)
foi corrigida e detectada na segunda.

## Checagens gerais
| Checagem | Comando | Resultado |
|---|---|---|
| Suíte completa | `uv run pytest --create-db` | **72 passaram, 12 pulados** (sem `jq`) |
| Testes de infra em Linux | `pytest` dos 3 arquivos de pipeline num contêiner com `jq` | 33 passaram, 0 pulados |
| Lint / formato | `uv run ruff check . && uv run ruff format --check .` | ok (27 arquivos) |
| Django | `manage.py check` e `makemigrations --check --dry-run` | ok |
| Produção | `manage.py check --deploy --fail-level WARNING` | ok |
| Imagem | `docker build backend` | ok |
| Compose de produção | `docker compose -f docker-compose.deploy.yml config` | ok |
| Script de deploy | `bash -n infra/deploy.sh` | ok |
| Specs | `sdd_lint.py . --code backend` | 0 erros. **O lint não separa as mudanças**: um ID citado por um teste da 001 também conta como coberto na 002 (a auditoria apagou testes da 002 e o lint seguiu verde). Por isso a cobertura da 002 foi conferida por mutação e por leitura, e não pelo lint |

## Verificação independente
Duas rodadas, ambas por agente separado, sem acesso ao raciocínio de quem implementou:
1. `auditoria-independente.md`: "não apto" (2 ALTA, 5 MÉDIA, 7 BAIXA). Corrigido na onda 5.
2. `auditoria-independente-2.md`: "apto com ressalvas" (2 ALTA, 7 MÉDIA, 8 BAIXA). Tratado na onda 6; situação por achado:

| Achado da 2ª rodada | Situação |
|---|---|
| ALTA-1 testes de pipeline só liam texto | **Tratado**: execução do `deploy.sh` e do bloco do workflow, checagens por linha, 30 de 30 mutações detectadas |
| ALTA-2 riscos aceitos e decisões "pelo agente" | **Parcial**: a delegação do usuário foi citada em `requirements.md`; as linhas passaram a "pendente de ratificação"; **só o usuário pode ratificar** (T-6.8) |
| MÉDIA-1 `run` com rótulos do Traefik durante a API no ar | **Corrigido** com `-l traefik.enable=false` nas duas chamadas; o comportamento do Traefik da VPS **não foi verificado** |
| MÉDIA-2 lint não separa as mudanças | **Documentado** aqui e no cabeçalho de `test_pipeline.py`; os IDs levam `[001]`/`[002]` e os controles novos começam em CTL-8 |
| MÉDIA-3 nomes de teste inexistentes | **Corrigido**: `-k ctl_8` e `-k ctl_9` selecionam testes |
| MÉDIA-4 transição do `.env.production` com aspas | **Mitigado**: o workflow recusa `POSTGRES_PASSWORD` com `$` ou ` #`; **depende do dono conferir** a senha real |
| MÉDIA-5 `validation.md` desatualizado | **Corrigido** (este arquivo) |
| MÉDIA-6 ABU-1 só no caminho da senha fraca | **Corrigido**: todos os caminhos de erro, com `capsys` |
| MÉDIA-7 teste de ABU-4 não protegia o limite | **Corrigido** para o texto do compose; a origem do IP na VPS segue sem verificação |
| BAIXA-1 Unicode, BAIXA-2 inativo, BAIXA-3 caixa, BAIXA-4 quebra em variable, BAIXA-5 redação do ABU-4, BAIXA-7 asserção tautológica | **Corrigidos** (REQ-1.4 novo; ABU-2 e ABU-4 reescritos) |
| BAIXA-6 `docker inspect`, BAIXA-8 mutações equivalentes | **Registrados** como risco aceito pendente / sem ação |

## Não verificado
- O log real do GitHub Actions: se `ADMIN_EMAIL` aparece no cabeçalho do passo, e se o `bash -e` do runner se comporta como o bash simples dos testes.
- O Traefik da VPS: contêiner de `run` fora do balanceador (MÉDIA-1), origem do IP atrás de NAT, versão.
- Um segundo deploy com a conta já existente (REQ-1.2 no ar) e a conferência `--verificar` no ar (REQ-2.5).
- O valor real de `POSTGRES_PASSWORD`: se tem `$` ou ` #`, a mudança de aspas o altera (o workflow recusa antes).
- O limite de 429 foi medido de um único endereço de origem.
- O Art. 2 (teste primeiro) foi seguido na onda 1 (24 testes vistos falhando). Nas ondas 5 e 6 os testes foram escritos junto das correções e o vermelho antes do código não foi registrado; a prova de que eles pegam os defeitos é a mutação (30 de 30 detectadas).
- A ratificação do usuário sobre os riscos aceitos e a revisão de CI, deploy e Traefik (T-6.8).
