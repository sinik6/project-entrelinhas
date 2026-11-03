---
id: 002-administrador-inicial
tipo: auditoria-independente (portão G5)
data: 2026-11-03
auditor: agente verificador, sem acesso ao raciocínio de quem implementou
base: commit 225324a (código da mudança em 5fe8e66)
veredito: não apto para o G5 até corrigir A1 e A2; pendente de decisão humana
---

# Auditoria independente — 002-administrador-inicial

Somente leitura: nenhum arquivo do projeto foi alterado além deste relatório. Nada foi commitado.

## O que foi executado
| Checagem | Comando | Resultado |
|---|---|---|
| Lint de specs | `python ~/.claude/skills/spec-driven-dev/scripts/sdd_lint.py . --code backend` | 0 erros, 6 avisos, **todos da 001** (REQ-3.1 a 3.4, REQ-4.1, CTL-7 sem teste). Código de saída 1 (avisos). Ver A2: parte da cobertura da 002 é falsa |
| Suíte completa | `uv run pytest --create-db` (PostgreSQL 17 descartável na porta 55433) | **35 passaram**: confere com o `validation.md` |
| Lint / formato | `uv run ruff check . && uv run ruff format --check .` | ok, 25 arquivos |
| Política de senhas | script avulso com `validate_password` nas settings de teste | ver M1 |
| Senha com `$` no `.env` | `docker compose --env-file` com `SENHA_ADMIN_INICIAL=Abc$Segredo123xyz` (Docker Desktop local) | ver A1: fragmento da senha impresso |
| Ramo de corrida (`IntegrityError`) | script avulso forçando a busca a não achar o usuário já criado | funciona: superusuário → "já existe" sem trocar a senha; usuário comum → recusa sem promover. **Sem teste na suíte** (B1) |
| Autoria dos commits | `git log -3` | `jpjamal <jpfisica3@gmail.com>`, sem coautor nem atribuição de IA: cumpre as fronteiras |

## Achados, do mais grave ao menos grave

### ALTA

**A1. Pedaço da senha vai para o log do deploy quando ela tem `$`** — `.github/workflows/deploy.yml:90`, `infra/deploy.sh:13`
- O workflow grava `SENHA_ADMIN_INICIAL=<valor>` sem aspas no `.env.production`, e o `deploy.sh` passa esse arquivo como
  `--env-file` a **toda** chamada `dc` (build, stop, ps, exec, run, up). O Compose interpola `$NOME` dentro de valores sem aspas
  e, para cada um, escreve um aviso com o nome da "variável". Reproduzido localmente:
  `level=warning msg="The \"Segredo123xyz\" variable is not set. Defaulting to a blank string."` (4 vezes num só `config`).
- O mascaramento do GitHub cobre o segredo inteiro, não um trecho dele: o trecho depois do `$` sai em claro no log do Actions.
  Viola NFR-SEC-1, ABU-1 e o Art. 9. Nenhum teste cobre esse caminho; o teste de ABU-1 olha só a saída do comando.
- O comando em si recebe o valor certo (o `run -e` lê do shell, que recebeu o valor cru de `valor()`); o problema é só o aviso.
- Vale também para `DJANGO_SECRET_KEY` e `POSTGRES_PASSWORD` (herdado da 001).
- **Correção** (escolher uma): (a) no laço dos segredos do workflow, recusar valor com `$` (uma linha, junto da checagem de quebra
  de linha) e documentar a restrição; (b) gravar `NOME='valor'` com aspas simples e recusar `'` no valor; (c) tirar a senha do
  `.env.production` e gravá-la num arquivo próprio (modo 600) que o `valor()` lê e que nunca vai ao `--env-file`. Recomendo (c),
  que também tira a senha do alcance de qualquer interpolação futura. Acrescentar teste de contrato do caminho escolhido.

**A2. Cobertura de CTL-2 (e o "0 erros" do lint) depende de colisão de IDs com a 001** — `backend/tests/test_pipeline.py:15-47`
- Nenhum teste da 002 cita `CTL-2`. O lint dá o controle como coberto porque encontra `test_ctl_2_segredos_fora_do_rsync`, que é da
  **001** e trata de rsync, não de política de senhas. O mesmo arquivo tem `test_abu_1_…`, `test_abu_2_…`, `test_abu_3_…` e docstring
  com `CTL-6` da 001: são IDs que também existem na 002, com outro significado. Um teste da 002 apagado pode continuar "coberto"
  por um homônimo da 001.
- **Correção**: citar `CTL-2` nas docstrings de `test_req_2_1_…`, `test_req_2_2_…` e `test_abu_3_…`; e, para eliminar a colisão,
  qualificar os IDs por mudança nos testes (ex.: docstring `002/ABU-1`, ou prefixo `test_002_…`) até o arquivamento dar IDs
  permanentes (`REQ-BASE.n`). Em `traceability.md:26`, trocar `test_req_2_1_…` abreviado pelo nome inteiro.

### MÉDIA

**M1. O mínimo de 12 caracteres não é provado por teste** — `backend/apps/common/tests/test_administrador_inicial.py:90`
- O caso "curta" é `"Curta1!"` (7 caracteres): com `min_length` 8 (o padrão do Django) ele continua sendo recusado. Conferi:
  com a política reduzida a mínimo 8, `"Curta1!"` falha do mesmo jeito. Trocar 12 por 8 em `base.py:95` não quebra nenhum teste.
- A senha comum (`CommonPasswordValidator`) está no design (§10: "comum, curta, só números, igual ao usuário") e **não tem caso**.
  O `match="política de senhas"` também não diz qual regra recusou.
- No ar há evidência (log do 1º deploy com "pelo menos 12 caracteres"), mas sem teste a regra não é protegida contra regressão.
- **Correção**: caso de 11 caracteres que só falha pelo tamanho (ex.: `"abcdefgh9!x"`, conferido: recusado só por ser curta) com
  `match="12"`; caso comum (ex.: `"password1234"`, conferido: recusado por "muito comum"); um caso de 12 caracteres aceito.

**M2. ABU-4 não descreve o que o Traefik faz, e a prova no ar é parcial** — `docker-compose.deploy.yml:74-89`, `requirements.md:82`
- `ratelimit` do Traefik é balde de fichas: `average: 5`, `period: 1m`, `burst: 5` libera 5 de uma vez e depois **uma a cada 12 s**.
  Num minuto passam até ~10 tentativas, e não há "janela" que recusa tudo até acabar, como diz ABU-4. O teste no ar (8 `POST`
  seguidos → 3 com 429) prova só a rajada.
- Os dois roteadores (`…-login-duckdns` e `…-login-ip`) usam o mesmo middleware. O Traefik instancia middleware por roteador,
  então é provável que cada um tenha o seu balde: alternando `jpsys.duckdns.org` e `217.216.82.25` o atacante dobra a cota.
  **Não verificado** (depende da versão do Traefik da VPS).
- **Correção**: reescrever ABU-4 com a semântica real ("até 5 seguidas e depois no máximo 1 a cada 12 s por endereço") ou
  ajustar o limite; conferir no ar alternando os dois hosts e registrar no `validation.md`.

**M3. Configuração errada derruba o Admin, embora dê para recusar antes de parar a API** — `infra/deploy.sh:33,49-52`
- O passo do administrador roda depois de `dc stop entrelinhas-api`. Qualquer recusa (senha curta, e-mail ausente, usuário comum
  com o mesmo nome) deixa o sistema fora do ar até o próximo deploy; o `validation.md` registra ≥16 h fora. O workflow só confere
  se o segredo está vazio.
- É o que REQ-2.4 manda, então a correção é decisão de spec, não do implementador.
- **Correção** (exige mudar REQ-2.4 com aprovação): validar antes de parar a API, com `administrador_inicial --verificar`
  (só valida valores e política, sem escrever no banco) rodado antes do `dc stop`; ou, no mínimo, checar no workflow tamanho ≥ 12
  e ausência de `$`/quebra de linha antes de tocar na VPS.

**M4. E-mail e usuário do administrador aparecem no log do Actions; valor de variável pode quebrar o script** — `.github/workflows/deploy.yml:78`
- `echo '...toJSON(vars)...'` (a expressão do Actions entre chaves duplas) expande as variables **dentro do texto do script**, que o Actions mostra no cabeçalho do passo.
  `ADMIN_EMAIL` vai para o log, contrariando design §11 ("sem o e-mail em log"). Um valor com `'` fecha a aspa e vira comando
  shell (injeção por quem edita variables). Herdado da 001, mas agora carrega dado pessoal.
- **Correção**: `env: VARS_JSON: <toJSON(vars) entre chaves duplas>` no passo e `jq … <<< "$VARS_JSON"` no script.
- **Não verificado** no log real (não abri o Actions).

**M5. Precedência ambígua entre variable e secret de mesmo nome** — `infra/deploy.sh:15`, `.github/workflows/deploy.yml:78-91`
- As variables entram primeiro no `.env.production` e os segredos depois. Se alguém criar por engano uma *variable*
  `SENHA_ADMIN_INICIAL` (visível em claro no GitHub), o `valor()` usa a primeira ocorrência (`grep -m1`), ou seja, a variable,
  enquanto o Compose usaria a última.
- **Correção**: no `jq`, excluir também os nomes dos segredos (`DJANGO_SECRET_KEY|POSTGRES_PASSWORD|SENHA_ADMIN_INICIAL`) e falhar
  se algum aparecer em `vars`.

### BAIXA

**B1. Ramo de corrida sem teste** — `backend/apps/common/services.py:41-43`
O design (§7) e o threat model (A10) afirmam que a corrida é tratada. Conferi por script que funciona, mas a suíte não exercita o
`except IntegrityError`. Correção: teste que cria o usuário entre a busca e a criação (ex.: `monkeypatch` da busca) para os dois
casos, superusuário e usuário comum.

**B2. NFR-SEC-2 é provado com MD5 de teste** — `backend/config/settings/test.py` (`PASSWORD_HASHERS`)
O teste prova "não está em texto puro", não o hasher de produção. Correção: teste que importa `config.settings.prod` (ou `base`)
e confere que `PASSWORD_HASHERS` não foi sobrescrito (PBKDF2/Argon2 como primeiro).

**B3. NFR-SEC-1 tem três partes e só uma é testada de verdade** — `requirements.md:69`
"Fora do repositório": nenhuma checagem (sem varredura de segredos no CI). "Fora do ambiente da API": só leitura de texto
(`test_ctl_4_…`); o contêiner avulso do `run --rm` mostra a senha em `docker inspect` enquanto roda, o que é aceitável, mas não está
dito. "Fora dos logs": ver A1 e M4.

**B4. A senha precisa existir para sempre, mesmo depois de usada** — `backend/apps/common/services.py:23` e `deploy.yml:86`
A checagem de senha vem antes da busca: com a conta já criada, apagar o segredo aborta o deploy. Resultado: a senha inicial fica em
texto no `.env.production` indefinidamente (THR-5, risco aceito) e continua válida se o dono não a trocou. Sugestão (decisão
humana): exigir a senha só quando a conta não existe, e orientar a troca no primeiro acesso, ou remover o segredo depois.

**B5. E-mail e nome não são validados** — `backend/apps/common/services.py:19-22`
`create_superuser` não roda validadores: aceita e-mail sem `@` e nome com espaços. Nome com mais de 150 caracteres gera `DataError`
com traceback em vez de `CommandError` limpo (não vaza senha: traceback não imprime variáveis locais). Correção: `validate_email` e
`full_clean` (ou o validador de nome do modelo) antes de criar, com mensagem curta.

**B6. Art. 9 pede auditoria de ação sensível** — `backend/apps/common/management/commands/administrador_inicial.py:27`
A criação de um superusuário fica registrada só como uma linha no log do deploy (que expira no Actions). Sugestão: registro
persistente (ex.: `LogEntry` do Admin ou log estruturado com data e origem), ou aceite explícito do humano.

**B7. Superusuário inativo passa como "já existe"** — `backend/apps/common/services.py:47-52`
Com `is_active=False`, o deploy termina verde e ninguém entra. É coerente com REQ-1.2 (não muda nada), mas a mensagem poderia
avisar. Informativo.

## Rastreabilidade: o teste prova o critério?
| ID | Teste | Prova? | Observação |
|---|---|---|---|
| REQ-1.1 | `test_req_1_1_…` | sim | |
| REQ-1.2 | `test_req_1_2_…`, `test_prop_1_…` | sim | senha, e-mail e superusuário conferidos |
| REQ-1.3 | `test_req_1_3_…` | sim | sem o prefixo `/entrelinhas` de produção; no ar, confirmado pelo dono |
| REQ-2.1 | `test_req_2_1_…` | sim | |
| REQ-2.2 | `test_req_2_2_…` | **parcial** | não prova 12 nem senha comum (M1) |
| REQ-2.3 | `test_req_2_3_…` | sim | 4 casos |
| REQ-2.4 | `test_req_2_4_…` | parcial (texto) | prova a ordem no script e o `set -e`; o efeito foi visto no ar |
| NFR-SEC-1 | `test_nfr_sec_1_…`, `test_ctl_4_…` | **parcial** | A1, M4, B3 |
| NFR-SEC-2 | `test_nfr_sec_2_…` | parcial | B2 |
| ABU-1 | `test_abu_1_…` | parcial | saída e `caplog` do comando sim; log do deploy não (A1) |
| ABU-2 | `test_abu_2_…` | sim | não promove, não troca senha nem `is_staff` |
| ABU-3 | `test_abu_3_…` | sim | |
| ABU-4 | `test_abu_4_…` | parcial (texto) | M2 |
| PROP-1 | `test_prop_1_…` | parcial | exemplos (2 e 5), sem corrida (B1) |
| PROP-2 | `test_req_2_2_…` | parcial | 3 exemplos; o "curta" falharia com qualquer política |

| Ameaça | Controle | Prova? |
|---|---|---|
| THR-1 | CTL-1 | sim (`test_abu_2_…`) |
| THR-2 | CTL-2 | sim nos testes de REQ-2.1/2.2/ABU-3, mas **o ID só é achado por colisão** (A2) e o mínimo de 12 não é provado (M1) |
| THR-3 | CTL-3 | parcial: o comando não imprime; o deploy pode imprimir trecho (A1) |
| THR-4 | CTL-4 | texto apenas |
| THR-5 | CTL-5 | hash sim (com MD5 de teste); texto em claro no `.env.production` é risco aceito |
| THR-6 | CTL-6 | texto + rajada no ar; semântica e roteadores duplos em aberto (M2) |

Ameaças sem entrada no threat model que esta auditoria levanta: vazamento por interpolação do Compose (A1), dado pessoal no
log do Actions (M4), precedência variable × secret (M5), indisponibilidade por configuração errada (M3).

## Constituição e fronteiras
- **Art. 6**: não há front; a validação está toda no comando. E-mail e nome sem validação (B5).
- **Art. 7**: deny-by-default mantido (sem cadastro público, não promove usuário comum). Política de senhas agora existe.
- **Art. 9**: senha fora da saída do comando, mas não garantidamente fora do log do deploy (A1); e-mail no log (M4);
  auditoria persistente da criação ausente (B6).
- **Fronteiras**: a mudança alterou CI, deploy e Traefik, que estão em "Perguntar antes". O checkpoint "revisão humana do
  `deploy.sh` e dos rótulos" (`tasks.md:45`) não tem registro de que aconteceu. Commits com autor certo e sem atribuição de IA.

## O que o `validation.md` dá como provado e não está
- **REQ-2.2 "✔ em teste e no ar"**: no ar sim; em teste, o mínimo de 12 e a senha comum não (M1).
- **NFR-SEC-1 "✔"**: o log colado não tinha a senha porque ela não tem `$`; o caminho de vazamento existe (A1); "fora do
  repositório" não tem checagem (B3).
- **ABU-4 "✔"**: provou a rajada, de um endereço, num host não identificado; não provou "até a janela terminar" nem o outro host (M2).
- **PROP-2 "✔"**: os três exemplos não distinguem a política do projeto da padrão do Django.
- **Checagem "Specs: 0 erros"**: verdadeira, mas CTL-2 só passa por colisão de ID (A2).
- O resto confere: 35 testes, ruff limpo, `veredito: parcial` e a seção "Não verificado" são honestos.

## O que NÃO consegui verificar
- Logs reais do GitHub Actions (se `ADMIN_EMAIL` aparece no cabeçalho do passo; se algum aviso do Compose já saiu).
- Versão do Docker Compose da VPS: reproduzi A1 no Docker Desktop local; o comportamento da VPS é presumido igual.
- Versão e comportamento do Traefik da VPS: balde por roteador (M2), normalização de caminho (`//`, `%2F`, codificação) que
  poderia escapar do `Path` exato do roteador limitado, e se há outro proxy na frente mudando o endereço de origem.
- Estado do banco de produção (se só existe o superusuário do dono) e o segundo deploy com a conta existente (T-3.2 aberta).
- Visibilidade do repositório `sinik6/project-entrelinhas` (o `gh` não está instalado aqui), que muda o peso de M4.
- Se a revisão humana de CI/deploy/Traefik foi pedida e dada antes do push de `5fe8e66`.
- `manage.py check --deploy`, `docker build` e `docker compose config` do projeto: não rodei de novo.

## Efeitos colaterais desta auditoria
- `uv run` criou `backend/.venv` (ignorado pelo `.gitignore`, linha 16).
- Um contêiner PostgreSQL descartável (`auditoria-002-pg`, porta 55433) foi criado e parado (`--rm`).
- Scripts de sonda ficaram fora do repositório, na pasta temporária da sessão.
