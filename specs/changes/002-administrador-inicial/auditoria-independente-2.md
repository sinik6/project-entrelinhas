---
id: 002-administrador-inicial
tipo: auditoria-independente 2 (portão G5, segunda rodada)
data: 2026-11-03
auditor: agente verificador independente, sem acesso ao raciocínio de quem implementou
base: árvore de trabalho com a onda 5 ainda NÃO commitada (git: 11 arquivos modificados sobre 225324a); nada da onda 5 está no ar
veredito: apto com ressalvas (o comportamento do código confere em tudo que executei; as provas e a governança ainda não sustentam o "✔" que os documentos dão; o critério do T-5.8, "sem achado alto aberto", NÃO está cumprido enquanto ALTA-1 e ALTA-2 estiverem abertos)
---

# Auditoria independente 2 — 002-administrador-inicial

Somente leitura no projeto: o único arquivo criado aqui é este relatório. Nada foi commitado, nenhuma requisição foi enviada à produção. Mutações e simulações rodaram numa cópia em pasta temporária da sessão.

## O que foi executado
| Checagem | Comando / método | Resultado |
|---|---|---|
| Suíte completa | `uv run pytest --create-db -q` (PostgreSQL 17 em 55433) | **55 passaram**. O `validation.md` ainda diz 35 (ver MÉDIA-5) |
| Lint / formato | `ruff check .` e `ruff format --check .` | ok, 25 arquivos |
| Lint de specs | `sdd_lint.py . --code backend` | 0 erros, 6 avisos, todos da 001. Ver MÉDIA-2: o "0 erros" não prova a cobertura da 002 |
| Compose de produção | `docker compose -f docker-compose.deploy.yml config` (Docker Compose 5.1.3) | válido, sem aviso; rótulos do limite presentes (prioridade 300 nos roteadores de login) |
| `bash -n infra/deploy.sh` | | ok |
| Bloco real do workflow ("Generate .env.production") | executado em contêiner `postgres:17-alpine` com `bash` e `jq`, só valores falsos, com as variáveis por `env` | senha `Abc$Segredo #123 \n "q" `x` ${Y} xyz` gravada como `SENHA_ADMIN_INICIAL='…'`; `docker compose --env-file` **sem nenhum aviso**; `valor()` devolveu a senha idêntica. Recusas conferidas: variable com aspa simples, variable com nome de segredo, segredo com aspa simples, vazio, com quebra de linha |
| `infra/deploy.sh` inteiro com um `docker`/`curl` falsos no PATH | 3 cenários: tudo ok; `--verificar` falha; criação (2ª chamada) falha | ok: sai com 0 e a ordem é rede → build → `--verificar` → stop → backup → up db → migrate → criação → up; `--verificar` falhando termina com código 1 **sem chegar ao `stop`**; a criação falhando termina com 1 com a API já parada (REQ-2.4). A senha chega ao `docker` só pelo ambiente (o argv traz `-e SENHA_ADMIN_INICIAL` sem valor) e a migração não recebe `-e` |
| `manage.py administrador_inicial` de verdade, settings de produção, banco inexistente | | `--verificar` ok devolve 0 sem banco; senha comum e e-mail ruim dão `CommandError` com código 1; sem `--verificar` e sem banco, o traceback não contém a senha (0 ocorrências) |
| Sondas avulsas no banco real | NFKC, caixa, inativo | ver BAIXA-1, BAIXA-3, BAIXA-2 |
| `docker compose run` e rótulos | contêiner descartável | o contêiner de `run` mantém os rótulos `traefik.*` do serviço (ver MÉDIA-1) |
| 54 mutações manuais | ver tabela abaixo | 29 detectadas, 25 não |

## Achado do 1º relatório → resolvido? → evidência
| Achado | Resolvido? | Evidência |
|---|---|---|
| A1 (trecho da senha com `$` no aviso do Compose) | **Sim, no código** · prova automática fraca | `deploy.yml:96-102` grava `NOME='valor'`; reproduzi o bloco real e o `docker compose --env-file` não emitiu aviso nem imprimiu a senha; `valor()` (`deploy.sh:18`) devolve o valor cru. Os testes só leem texto (mutações 42-43 e 45-47 passam). Os nomes citados nos documentos não existem (MÉDIA-3). Ver MÉDIA-4 para a transição |
| A2 (CTL-2 coberto por colisão de ID) | **Parcial** | `CTL-2` agora está nas docstrings de `test_administrador_inicial.py:84,101,109,217` e os testes ganharam `[001]`/`[002]`. Mas o lint continua enganável: apaguei de uma cópia todos os testes da 002 com ABU-1, ABU-2, ABU-3, REQ-2.1, CTL-1 e CTL-3 e o `sdd_lint` seguiu com 0 erros e nenhum aviso novo da 002. `test_req_2_1_producao_recusa_subir_sem_secret_key` (`test_configuracao.py:9`) não tem a marca `[001]`, e os nomes `test_abu_1/2/3_…` ainda existem nos dois contextos |
| M1 (12 caracteres não provado) | **Sim** | `test_administrador_inicial.py:91-120`. Mutações 0, 1, 2 (mínimo 8, 11 e 13), 3, 4 e 5 (sem Common, Numeric, Similarity) e 15 (validar sem `user`) foram todas detectadas |
| M2 (ABU-4 vs balde de fichas) | **Parcial** | `requirements.md:ABU-4` e D-6 foram reescritos com a semântica de balde; a medição no ar (domínio e IP em baldes separados) não pude refazer. O teste só compara texto (mutações 34, 35, 36, 37, 38, 41 passam; ver MÉDIA-8). Redação "endereço de acesso (domínio ou IP)" mistura destino com origem (BAIXA-5) |
| M3 (recusa só depois de parar a API) | **Sim, no código** | `deploy.sh:43-46`, REQ-2.5, `--verificar` sem banco (`administrador_inicial.py:38-41`, `test_req_2_5_verificar_valida_sem_tocar_no_banco`). Comprovei com o `docker` falso que a falha para antes do `stop`. O teste do pipeline só confere a ordem de duas strings (mutações 25 e 27 passam) e a correção introduz o problema da MÉDIA-1 |
| M4 (e-mail no log; injeção por `toJSON` dentro do script) | **Parcial** | Injeção resolvida: `deploy.yml:75` passa por `env:` e o teste da mutação 53 detecta o retorno. O e-mail **continua visível**: o Actions imprime os valores do bloco `env:` do passo, então `VARS_JSON` expõe `ADMIN_EMAIL`. Os documentos já tratam como risco aceito, mas pelo agente (ALTA-2). Não verifiquei o log real |
| M5 (variable e secret de mesmo nome) | **Sim, no código** | `deploy.yml:81-83` recusa; executei com `{"SENHA_ADMIN_INICIAL":"x"}` e parou com a mensagem. `valor()` pega a última ocorrência (`deploy.sh:18`). Teste só de texto (mutação 44 passa) |
| B1 (corrida sem teste) | **Sim** | `test_prop_1_corrida…` e `test_abu_2_corrida…`; remover o `except IntegrityError` (mutação 14) quebra. É corrida simulada por `monkeypatch`, não concorrência real |
| B2 (NFR-SEC-2 com MD5 de teste) | **Sim** | `test_configuracao.py:26`; mutações 23 e 24 detectadas. A 2ª asserção (`global_settings.PASSWORD_HASHERS[0]`) é tautológica, só a 1ª vale (BAIXA-7) |
| B3 (NFR-SEC-1 em três partes) | **Parcial** | "Fora do repositório" aceito sem varredura (threat-model:81). "Fora do ambiente da API": o teste de CTL-4 só procura o nome da variável no compose, e `env_file: .env.production` no serviço passa (mutação 32). `docker inspect` do contêiner avulso (BAIXA-6) segue sem texto |
| B4 (senha sempre exigida) | **Sim, por decisão** | D-9 e risco aceito; comportamento confere com o código (`services.py:25`). Aceito pelo agente (ALTA-2) |
| B5 (nome e e-mail sem validação) | **Sim** | `services.py:28-38`; 3 casos em `test_administrador_inicial.py:135-150`; mutações 12 e 13 detectadas. Resta o caso NFKC (BAIXA-1) |
| B6 (auditoria persistente, Art. 9) | **Aceito, não corrigido** | linha 82 do threat-model, aceita pelo agente (ALTA-2) |
| B7 (superusuário inativo vira "já existe") | **Não** | nenhuma menção em código, spec ou risco aceito (`grep` de "inativ" e `is_active` só acha o relatório anterior). Reproduzi: superusuário com `is_active=False` + execução → "já existe", deploy verde |

## Achados novos

### ALTA

**ALTA-1. Os controles de pipeline (CTL-4, 8, 9, 10, NFR-SEC-1, REQ-2.5) são dados como provados por testes que não os provam** — `backend/tests/test_pipeline.py:82-161`, `traceability.md`, `design.md §10`
- Os testes do pipeline leem texto. Das 28 mutações que fiz em `deploy.sh`, `docker-compose.deploy.yml` e `deploy.yml`, **só 11 foram detectadas**. Passaram sem nenhum teste vermelho:
  - `env_file: .env.production` no serviço da API (mutação 32): a senha, o segredo do Django e a do banco entram no ambiente do contêiner da API, que é exatamente o que NFR-SEC-1 e CTL-4 proíbem. O teste de CTL-4 só procura `SENHA_ADMIN_INICIAL` no texto do compose.
  - `echo "… $SENHA_ADMIN_INICIAL"` no workflow (52): vazamento direto no log. Nenhum teste olha o workflow por isso.
  - `admin_inicial --verificar || true` (25) e `admin_inicial || true` (26): a recusa deixa de abortar o deploy, o oposto de REQ-2.4 e REQ-2.5. O teste só confere a ordem de `index()`.
  - `# admin_inicial --verificar` comentado (27): a string ainda existe, a ordem passa.
  - `-e SENHA_ADMIN_INICIAL="$(valor …)"` (28): a senha iria no argv do `docker`, visível em `ps`; o teste procura só o prefixo `-e SENHA_ADMIN_INICIAL`.
  - Segredo da senha fora da lista do laço (48), recusa de aspa/quebra/vazio removida (45-47), variables sem aspas simples (42), sem checagem de aspa em variable (43), sem checagem de nome de segredo (44), `umask 077` e `chmod 600` removidos (50, 51), ordem `>`/`>>` trocada (49): todos passam. Alguns são fail-closed na prática (48 faz o `--verificar` recusar no deploy), mas ninguém descobre isso antes do deploy.
- `traceability.md` marca THR-4, THR-8, THR-9, THR-10 como "✔" e NFR-SEC-1 "✔" sem ressalva, e o `design.md §10` chama de "contrato do pipeline, com bash de verdade" testes que só executam `valor()`.
- **Como reproduzir**: copiar o projeto para outra pasta, aplicar qualquer mutação acima e rodar `uv run pytest -q`. O script usado está fora do repositório (pasta temporária da sessão, `mut.py`).
- **Como corrigir**: (a) teste do `deploy.sh` com `docker` falso no PATH, como fiz: confere ordem real das chamadas, que `--verificar` falhando não chega ao `stop`, que o argv não traz a senha; (b) teste que executa o bloco do workflow (extraído do YAML) com `bash` e `jq` para os 5 casos de recusa e confere o arquivo gerado; (c) em CTL-4, checar que o serviço da API não tem `env_file` nem `${SENHA…}`; (d) até lá, trocar os "✔" de THR-4/8/9/10 e NFR-SEC-1 por "✔ (texto)" ou "provado só manualmente em 2026-11-03".

**ALTA-2. Decisões de spec, edição de CI/deploy/Traefik e aceite de seis riscos assinados pelo agente** — `requirements.md:25`, `threat-model.md:76-82`, `tasks.md:62`
- A tabela de riscos aceitos tem o título "somente pelo humano" e cinco das seis linhas novas dizem "agente, por delegação do dono (2026-11-03)". A constituição proíbe "aprovar portão em nome do humano", e CI, deploy e Traefik estão em "Perguntar antes".
- O `requirements.md:25` diz "confirmada (usuário, 2026-11-03)" para uma suposição cujo texto é "foram delegadas ao agente, **sem a participação do usuário** nem de outro dev": a coluna de status afirma uma confirmação que a própria linha nega. Não tenho como verificar se a delegação existiu; só existe o texto escrito pelo mesmo agente.
- Entre os riscos aceitos dessa forma há dado pessoal em log (e-mail, Art. 9), THR-6 residual (2 baldes), ausência de auditoria persistente (Art. 9) e segredo para sempre em texto (THR-5 ampliado).
- **Correção**: o dono assina as seis linhas (nome e data) e marca o checkpoint "revisão humana do `deploy.sh` e dos rótulos" de `tasks.md:45`, que continua sem registro; ou as linhas voltam a "pendente". Corrigir a coluna de status do `requirements.md:25`.

### MÉDIA

**MÉDIA-1. `--verificar` roda um contêiner `run` com os rótulos do Traefik enquanto a API está no ar** — `infra/deploy.sh:24,46`
- Verifiquei localmente que `docker compose run` mantém os rótulos do serviço (`traefik.enable=true`, mais `com.docker.compose.oneoff=True`). O contêiner de `run` entra nas redes do serviço, incluindo `traefik_proxy`. Com o provedor Docker, o Traefik tende a registrá-lo como mais um servidor do serviço `entrelinhas-api` pelo tempo de vida dele; como ele não escuta na 8000, parte das requisições do Admin pode receber 502 por alguns segundos, **a cada deploy**, justamente na janela em que o REQ-2.5 quer o Admin saudável. Antes da onda 5, o `run` só acontecia com a API parada. Não consegui verificar o comportamento do Traefik da VPS.
- **Correção**: `dc run --rm --no-deps -l traefik.enable=false …` nas duas chamadas (ou `--no-deps` com rede só `internal`). Acrescentar ao teste do `deploy.sh` com `docker` falso.

**MÉDIA-2. O "0 erros" do `sdd_lint` não prova cobertura da 002** — `traceability.md`, `validation.md` (checagem "Specs: 0 erros")
- Demonstrado na A2: removendo os testes da 002 de ABU-1/2/3, REQ-2.1, CTL-1, CTL-3 o lint continua verde porque os mesmos IDs aparecem em testes da 001 (`test_pipeline.py:24-56`, `test_configuracao.py:9`). A marca `[001]`/`[002]` na docstring não entra no lint.
- **Correção**: renomear os testes da 001 ou da 002 com prefixo (`test_002_…`) e/ou checar a cobertura por arquivo/mudança; no mínimo, deixar escrito na validação que o lint não separa as mudanças. Marcar `[001]` em `test_configuracao.py:10`.

**MÉDIA-3. Nomes de teste citados nos documentos não existem e os comandos de verificação da onda 5 rodam zero testes** — `design.md §10`, `threat-model.md:50-51`, `traceability.md`, `tasks.md:T-5.1 e T-5.6`
- Documentos citam `test_ctl_8_valor_devolve_a_senha_crua_com_cifrao_e_aspas`, `test_ctl_8_workflow_grava_com_aspas_simples_e_recusa_aspa_no_valor`, `test_ctl_9_*`; no código são `test_ctl_3_valor_devolve…` (`test_pipeline.py:128,136,143,152,158`). `pytest -k ctl_8`, `-k ctl_9` e `-k ctl_10` selecionam **0 testes** (rodei: "55 deselected"). O `design.md §10` também cita `test_abu_4_login_do_admin_tem_limite_de_5_por_minuto`, que não existe (o nome é `…_balde_de_5_fichas_por_minuto`).
- **Correção**: renomear as funções para `test_ctl_8_…`/`test_ctl_9_…` (provável erro de substituição) e refazer as citações; rodar os `-k` das tarefas e conferir que selecionam algo.

**MÉDIA-4. Risco de transição ao regravar `.env.production` entre aspas** — `deploy.yml:96-102`
- Antes, o arquivo era sem aspas e o Compose interpolava `$` e cortava ` #`. Se `POSTGRES_PASSWORD` já tem `$` (ou ` #`) o valor que o Postgres usou ao inicializar o volume era o valor "mastigado"; com aspas, o Compose passa o valor cru e a API deixa de autenticar no banco já criado: o deploy falharia na migração com a API parada. `DJANGO_SECRET_KEY` com `$` só invalida sessões. Não sei como são os segredos reais.
- **Correção**: conferir antes do push que `POSTGRES_PASSWORD` não tem `$` nem ` #` (ou usar o valor antigo equivalente), e registrar a transição em `design.md §15`.

**MÉDIA-5. `validation.md` desatualizado** — `validation.md:12,29-35`
- Diz "35 passaram", "commit 5fe8e66", nomes antigos de teste (ABU-4), e não tem linha para REQ-2.5, CTL-8, CTL-9 nem CTL-10, que `traceability.md` dá como "✔ em teste". O `design.md §13` ainda fala em "6 ameaças e 6 controles" (hoje 9 e 9). O `status: rascunho`/`veredito: parcial` é honesto; o resto é cópia velha. Também nada da onda 5 foi commitada nem implantada: o "no ar" vale só para o que foi publicado em `5fe8e66`.

**MÉDIA-6. ABU-1 e NFR-SEC-1 são provados só no caminho da senha fraca e na saída do `call_command`** — `test_administrador_inicial.py:171-197`
- Mutações 19 (mensagem de "ADMIN_EMAIL inválido" concatenando a senha) e 21 (`print()` da senha em `sys.stdout`) passam. `caplog` e `StringIO` do comando não pegam `print`; o teste de erro usa só a senha parecida com o usuário.
- **Correção**: `capsys` + `capfd` no teste, e rodar os erros de e-mail, usuário, usuário comum e `--verificar` com a senha, conferindo que ela não aparece em nenhuma saída.

**MÉDIA-7. O teste de ABU-4 não protege o limite** — `test_pipeline.py:98-106`, `docker-compose.deploy.yml:71-89`
- Passam: prioridade do roteador de login 300→100 (mutação 34), o que faria o roteador de login perder para o do Admin (200) e **desligar o limite sem aviso**; `login-ip` sem `service` (35); host errado (36); sem `tls` (37) ou `entrypoints` (38); sem `secure-headers` (41). Só mudar média, período ou rajada (39, 40) quebra.
- Também não existe prova de que o Traefik da VPS conta por IP de origem: se houver NAT ou outro proxy na frente, todos os clientes dividem o mesmo balde (negação de serviço do login) ou o limite não vale por cliente. Isso não foi verificado nem por mim nem pelo `validation.md` (medido de um único endereço).
- **Correção**: testar a prioridade (login > admin) e a presença de `service`, `tls`, `entrypoints` em ambos os roteadores; documentar a suposição sobre a origem do IP.

### BAIXA

- **BAIXA-1. Nome de usuário com forma Unicode não normalizada dá traceback** — `services.py:58-67`. `create_superuser` normaliza o nome (NFKC); a busca `filter(username=usuario)` usa o texto cru. Com `admin` existente e `ADMIN_USUARIO=ａdmin` (a de largura total), a busca não acha, a criação bate em `IntegrityError` e o `get(username=usuario)` do tratamento levanta `DoesNotExist` não tratado (traceback, código 1). Reproduzi com superusuário e com usuário comum. **Não promove ninguém** (falha fechada), mas, com superusuário existente, o deploy falha para sempre. Correção: normalizar com `modelo.normalize_username(usuario)` antes de buscar e validar.
- **BAIXA-2. Superusuário inativo passa como "já existe"** (B7, não tratado): `services.py:75-80`. Reproduzido. Aviso ou erro com `is_active=False`.
- **BAIXA-3. Nomes que só diferem na caixa** (`Dono` comum existente, `dono` configurado) criam um segundo usuário; ABU-2 só fala em "mesmo nome". Sem promoção. Decidir se é aceitável e registrar.
- **BAIXA-4. Variable com quebra de linha não é recusada** (só os segredos): `deploy.yml:84-86`. Uma variable `ADMIN_USUARIO` com `\nADMIN_EMAIL=x` injeta uma linha no `.env.production`; reproduzido. Como os segredos são gravados por último e `valor()` pega a última ocorrência, a senha não é afetada; um e-mail ou nome injetado sim, e só por quem já edita variables. Recusar `\n`/`\r` também nas variables.
- **BAIXA-5. ABU-4 mistura destino e origem**: "mesmo endereço de acesso (domínio ou IP)". O Traefik limita por IP de origem **por roteador** (host de destino). Reescrever, e dizer em THR-6 que ataque vindo de muitos IPs não é contido.
- **BAIXA-6. A senha fica visível em `docker inspect` do contêiner avulso enquanto o `run` dura** (B3, parte "ambiente"): aceitável, mas sem texto na spec.
- **BAIXA-7. Segunda asserção do teste de hasher é tautológica** (`test_configuracao.py:44`): lê `global_settings` do Django, não as settings do projeto.
- **BAIXA-8. Mutações equivalentes**: `.strip()` do usuário e do e-mail (7 e 8) não mudam nada observável porque os validadores já recusam espaços nas pontas; não é lacuna de teste.

## Mutações tentadas
Executadas por `uv run pytest -q -x` numa cópia, uma por vez.

| # | Mutação | Detectada? |
|---|---|---|
| 0 | `min_length` 12 → 8 | sim |
| 1 | 12 → 11 | sim |
| 2 | 12 → 13 | sim |
| 3 | sem `CommonPasswordValidator` | sim |
| 4 | sem `NumericPasswordValidator` | sim |
| 5 | sem `UserAttributeSimilarityValidator` | sim |
| 6 | senha só de espaços aceita (tira `.strip()` da senha) | sim |
| 7 | usuário sem `.strip()` | **não** (equivalente, BAIXA-8) |
| 8 | e-mail sem `.strip()` | **não** (equivalente) |
| 9 | promove usuário comum | sim |
| 10 | usuário existente tem a senha trocada | sim |
| 11 | usuário existente tem o e-mail trocado | sim |
| 12 | sem `validate_email` | sim |
| 13 | sem validador do nome de usuário | sim |
| 14 | sem tratar `IntegrityError` | sim |
| 15 | `validate_password` sem `user` | sim |
| 16 | `--verificar` cria o usuário | sim |
| 17 | comando imprime parte da senha | sim |
| 18 | erro de política imprime a senha | sim |
| 19 | erro de e-mail imprime a senha | **não** (MÉDIA-6) |
| 20 | `logging` com a senha | sim |
| 21 | `print()` da senha no stdout do processo | **não** (MÉDIA-6) |
| 22 | senha em texto no banco | sim |
| 23 | hasher MD5 em `base.py` | sim |
| 24 | hasher fraco em `prod.py` | sim |
| 25 | `admin_inicial --verificar \|\| true` | **não** |
| 26 | `admin_inicial \|\| true` (criação) | **não** |
| 27 | `--verificar` comentado | **não** |
| 28 | senha no argv (`-e SENHA=$(valor …)`) | **não** |
| 29 | `valor()` não tira a aspa final | sim |
| 30 | `set -eu` sem `pipefail` | sim |
| 31 | `dc stop` antes do `--verificar` | sim |
| 32 | `env_file: .env.production` no serviço da API | **não** |
| 33 | `SENHA_ADMIN_INICIAL` citada no compose | sim |
| 34 | prioridade do roteador de login 300 → 100 | **não** |
| 35 | `login-ip` sem `service` | **não** |
| 36 | `login-ip` com host errado | **não** |
| 37 | `login-duckdns` sem `tls` | **não** |
| 38 | `login-duckdns` sem `entrypoints` | **não** |
| 39 | rajada 5 → 500 | sim |
| 40 | período 1m → 1h | sim |
| 41 | login sem `secure-headers` | **não** |
| 42 | variables sem aspas simples | **não** |
| 43 | sem checar aspa em variable | **não** |
| 44 | sem checar variable com nome de segredo | **não** |
| 45 | não recusa quebra de linha no segredo | **não** |
| 46 | não recusa segredo vazio | **não** |
| 47 | não recusa aspa no segredo | **não** |
| 48 | `SENHA_ADMIN_INICIAL` fora do laço dos segredos | **não** |
| 49 | `>` trocado por `>>` | **não** |
| 50 | `chmod 600` remoto removido | **não** |
| 51 | `umask 077` removido | **não** |
| 52 | `echo` da senha no workflow | **não** |
| 53 | `VARS_JSON` de volta ao texto do script | sim |

Resumo: o código Python do comando está bem protegido (21 de 23 detectadas; as duas que passam são equivalentes ou de saída). A camada de pipeline e compose está protegida em 8 de 31 pontos.

## Cada ID tem teste que prova o critério?
| ID | Prova? | Observação |
|---|---|---|
| REQ-1.1, 1.2, 1.3 | sim | senha, e-mail, flags conferidos; 1.3 usa `/admin/login/` sem o prefixo de produção |
| REQ-2.1, 2.2, 2.3 | sim | mutações do mínimo, comum, só números e parecida detectadas |
| REQ-2.4 | parcial | só ordem de strings; `|| true` na criação passa (26). Verifiquei com `docker` falso que o comportamento está certo |
| REQ-2.5 | parcial | `--verificar` sem banco prova bem; "aborta com a API no ar" é só ordem textual (25, 27) |
| NFR-SEC-1 | parcial | ver ALTA-1 e MÉDIA-6 |
| NFR-SEC-2 | sim | hash e hasher da produção |
| ABU-1 | parcial | MÉDIA-6 |
| ABU-2, ABU-3 | sim | incluindo corrida |
| ABU-4 | parcial (texto) | MÉDIA-7 |
| PROP-1, PROP-2 | parcial | exemplos; PROP-1 sem corrida real |
| CTL-1, 2, 3, 5 | sim | |
| CTL-4 | **não** | só procura o nome no compose (32) |
| CTL-6 | parcial | MÉDIA-7 |
| CTL-8, 9, 10 | **não** (só texto) | ALTA-1 |

## O que `validation.md` e `traceability.md` dão como provado e não está
- `traceability.md`: "THR-4 ✔ (texto)" está honesto; "NFR-SEC-1 ✔", "THR-8 ✔", "THR-9 ✔", "THR-10 ✔ em teste" e "REQ-2.5 ✔ em teste" não são sustentados pelas mutações de ALTA-1. "ABU-1 ✔" tem a lacuna da MÉDIA-6. Os nomes de teste citados em CTL-8 e CTL-9 não existem (MÉDIA-3).
- `validation.md`: números e nomes velhos (MÉDIA-5); "Specs: 0 erros" é verdade e não prova nada da 002 (MÉDIA-2).
- A nota "✔ (texto): o teste prova que a regra está escrita, não que o Traefik ou a VPS a cumprem" é honesta e deveria valer para mais linhas.
- Onde um risco aceito aparece como mitigado: THR-6 "CTL-6 ✔ (texto) e no ar" omite que a origem do IP não foi verificada e que muitos IPs passam; THR-3/NFR-SEC-1 descrevem o e-mail no log como aceito, mas o e-mail continua no cabeçalho do passo mesmo depois de ir para `env:`.

## Constituição e fronteiras
- **Art. 6**: sem front; a validação está toda no comando. Ok.
- **Art. 7**: deny-by-default mantido; ninguém é promovido (mutação 9 detectada, corrida testada).
- **Art. 9**: senha fora da saída do comando (conferido por execução); e-mail em log aceito e auditoria persistente ausente, ambos aceitos só pelo agente (ALTA-2).
- **Sempre / Perguntar antes / Nunca**: a onda 5 mexeu em CI, deploy e Traefik ("Perguntar antes") e em segredos; a autorização está só como "delegação" escrita pelo agente (ALTA-2). Nada foi commitado nem enviado (git: só arquivos modificados), de acordo com "commit só quando o dono mandar".

## O que NÃO consegui verificar
- O log real do GitHub Actions (se `ADMIN_EMAIL` aparece no bloco `env:`; se algum aviso de Compose saiu) e o comportamento de `bash -e {0}` do runner (reproduzi o bloco em `bash` simples sem `-e`).
- O Traefik da VPS: balde por roteador, origem do IP (NAT, outro proxy), normalização de caminho, e se o contêiner de `run` entra no balanceador (MÉDIA-1). Não enviei POST à produção, como mandado.
- Versão do Docker Compose da VPS (usei a 5.1.3 local) e o valor real de `POSTGRES_PASSWORD`/`DJANGO_SECRET_KEY` (MÉDIA-4).
- A medição "domínio e IP com baldes separados" e o 429 no ar.
- Se os testes da onda 5 foram escritos antes e vistos falhando (Art. 2): não há histórico, a onda 5 não está commitada.
- A existência e o conteúdo da "delegação" do dono (ALTA-2).
- O estado do banco de produção e o segundo deploy com a conta existente (T-3.2 aberta).

## Efeitos colaterais desta auditoria
- No repositório: apenas este arquivo. `uv run pytest` e `ruff` na raiz do `backend/` podem ter atualizado `backend/.pytest_cache` e `backend/.ruff_cache` (ambos já ignorados pelo `.gitignore`).
- Fora do repositório (pasta temporária da sessão): cópia do projeto, scripts de mutação e stubs de `docker`/`curl`; contêineres `postgres:17-alpine` e `auditlab` descartáveis, removidos.
