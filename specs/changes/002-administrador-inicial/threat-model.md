---
id: 002-administrador-inicial
status: em-revisao
asvs_nivel: L2
---

# Modelo de ameaças — Administrador inicial

## Ativos e dados
| Ativo | Classificação | Por que importa |
|---|---|---|
| Senha do administrador (`SENHA_ADMIN_INICIAL`) | segredo | dá acesso total ao Admin e, depois, a todo o texto íntimo dos registros |
| Conta de superusuário | segredo | privilégio máximo: lê e altera qualquer dado |
| Admin público (`/entrelinhas/admin/`) | interno exposto na internet | único ponto de login enquanto o app não existe |
| `.env.production` na VPS | segredo | guarda a senha em texto, modo 600 |

## Fronteiras de confiança e fluxo de dados
```mermaid
flowchart LR
  G[Secrets do GitHub] -- SSH, modo 600 --> E[.env.production na VPS]
  E -- run --rm -e --> C[administrador_inicial]
  C --> D[(Banco: hash da senha)]
  I[Internet] -- HTTPS --> T[Traefik]
  T --> A[Admin do Django]
  A --> D
```

## Ameaças (STRIDE por fluxo)
| ID | Fluxo | STRIDE | Ameaça | Prob. | Impacto | Risco | Controle(s) |
|---|---|---|---|---|---|---|---|
| THR-1 | comando → banco | E | usuário comum com o nome configurado é promovido a superusuário | B | A | M | CTL-1 |
| THR-2 | segredo → comando | S | senha vazia, curta, comum ou igual ao usuário vira a senha do administrador | M | A | A | CTL-2 |
| THR-3 | comando → log do deploy | I | a senha aparece na saída do comando ou nos logs do Actions | M | A | A | CTL-3 |
| THR-4 | compose → contêiner | I | a senha fica no ambiente do contêiner da API e aparece em `docker inspect` | M | A | A | CTL-4 |
| THR-5 | VPS | I | quem lê `.env.production` obtém a senha em texto | B | A | M | CTL-5 |
| THR-6 | Internet → Admin | S | força bruta contra o login do Admin exposto, sem limite de tentativas | M | A | M | CTL-6 |
| THR-8 | `.env.production` → Compose → log | I | a senha tem `$` e o Compose imprime um pedaço dela num aviso do log do deploy | M | A | A | CTL-8 |
| THR-9 | variables → workflow | T | variable com nome de segredo prevalece sobre o segredo, ou valor com aspa simples vira comando no script | B | A | M | CTL-9 |
| THR-10 | deploy → API | D | configuração errada derruba o Admin porque a recusa só vem depois de parar a API | M | M | M | CTL-10 |

## Controles
| ID | Controle | Atende | Teste/evidência |
|---|---|---|---|
| CTL-1 | usuário existente que não é superusuário faz o comando recusar, sem promover | THR-1, ABU-2 | `test_abu_2_usuario_comum_existente_nao_e_promovido` |
| CTL-2 | senha obrigatória, recusa vazia/só espaços e passa por `AUTH_PASSWORD_VALIDATORS` (12+, comum, só números, similar ao usuário) | THR-2, REQ-2.1, REQ-2.2, ABU-3 | `test_req_2_1_…`, `test_req_2_2_…`, `test_abu_3_…` |
| CTL-3 | o comando imprime só o nome do usuário; erros listam motivos sem repetir a senha | THR-3, ABU-1, NFR-SEC-1 | `test_abu_1_*`, `test_nfr_sec_1_senha_nao_aparece_na_saida` |
| CTL-4 | a senha vai por `docker compose run -e` só àquela execução; o compose de produção não cita a variável | THR-4, NFR-SEC-1 | `test_ctl_4_senha_nao_entra_no_compose_nem_no_servico_da_api` |
| CTL-5 | senha gravada só como hash; `.env.production` com modo 600 e fora do rsync (mudança 001) | THR-5, NFR-SEC-2 | `test_nfr_sec_2_senha_gravada_so_como_hash`, `test_ctl_2_segredos_fora_do_rsync` (001) |
| CTL-6 | roteador próprio para `POST` em `/entrelinhas/admin/login/` com `ratelimit` do Traefik (balde de 5 fichas, recarga de 1 a cada 12 s), definido nos rótulos do compose; sem dependência nova. O domínio e o IP têm baldes separados (medido no ar em 2026-11-03) | THR-6, ABU-4 | `test_abu_4_login_do_admin_tem_balde_de_5_fichas_por_minuto`; medição no ar |
| CTL-8 | `.env.production` gravado com aspas simples (o Compose não interpola `$` nem lê `#` como comentário); valor com aspa simples é recusado; `valor()` tira as aspas | THR-8, NFR-SEC-1, ABU-1 | `test_ctl_8_valor_devolve_a_senha_crua_com_cifrao_e_aspas`, `test_ctl_8_workflow_grava_com_aspas_simples_e_recusa_aspa_no_valor`; bloco real do workflow e `docker compose config` sem aviso |
| CTL-9 | `toJSON(vars)` chega por `env:` do passo, não dentro do texto do script; variable com nome de segredo derruba o passo; `valor()` usa a última ocorrência | THR-9, NFR-SEC-1 | `test_ctl_9_variables_chegam_por_env_e_nao_dentro_do_texto_do_script`, `test_ctl_9_variable_com_nome_de_segredo_e_recusada`, `test_ctl_9_valor_usa_a_ultima_ocorrencia` |
| CTL-10 | `administrador_inicial --verificar` roda antes de `dc stop`, sem usar o banco; senha ausente, curta ou comum aborta o deploy com a API no ar | THR-10, REQ-2.5 | `test_req_2_5_*` (entre eles o `deploy.sh` executado com `docker` falso) |

## OWASP Top 10:2025 — percorrido
| Cat. | Aplica? | Como foi tratado |
|---|---|---|
| A01 Controle de acesso / SSRF | sim | CTL-1; só um superusuário; sem cadastro público |
| A02 Configuração | sim | CTL-4; política de senhas passa a existir (hoje não existe) |
| A03 Cadeia de suprimentos | não | sem dependência nova |
| A04 Criptografia | sim | hash da senha pelo Django (PBKDF2 por padrão); TLS pelo Traefik |
| A05 Injeção | não | sem entrada do usuário; valores do ambiente vão ao ORM |
| A06 Design inseguro | sim | falha fechada: erro interrompe o deploy com a API parada |
| A07 Autenticação | sim | CTL-2 e THR-6; sem MFA (fora de escopo) |
| A08 Integridade | não | — |
| A09 Log e alerta | sim | CTL-3, CTL-8; o e-mail do administrador, por ser variable, aparece no cabeçalho do passo no Actions (aceito, ver riscos); tentativas de login falhas não geram alerta (fora de escopo) |
| A10 Condições excepcionais | sim | `IntegrityError` na corrida tratado; qualquer erro encerra com código 1 |

## Dependências novas
| Pacote | Versão | Verificado no registro? | Motivo |
|---|---|---|---|
| (nenhuma) | | | |

## Riscos aceitos (somente pelo humano)
| Ameaça | Motivo | Quem aceitou | Data |
|---|---|---|---|
| THR-5 (senha em texto no `.env.production`, modo 600) | mesmo padrão do Vinculus; quem lê o arquivo já tem acesso de `deploy` à VPS | usuário | 2026-10-28 |
| E-mail do administrador visível no cabeçalho do passo no Actions (variable, não segredo) | é o e-mail do próprio dono; a senha não é variable; para mudar, o e-mail teria de virar secret | agente, por delegação do usuário em chat; **ratificado pelo usuário em 2026-11-03** | 2026-11-03 |
| Domínio e IP com baldes de login separados (até 10 tentativas seguidas em vez de 5) | com a política de 12 caracteres, 10 tentativas seguidas são desprezíveis; fechar o IP tiraria o acesso de contingência | agente, por delegação do usuário em chat; **ratificado pelo usuário em 2026-11-03** | 2026-11-03 |
| A senha inicial continua exigida e em texto no `.env.production` depois de usada | o deploy fica determinístico; o dono pode trocar a senha no Admin e o segredo passa a ser só um valor que o deploy revalida | agente, por delegação do usuário em chat; **ratificado pelo usuário em 2026-11-03** | 2026-11-03 |
| Sem registro persistente da criação do superusuário (só o log do deploy) | MVP de uso pessoal, um administrador; o Admin já registra as ações seguintes | agente, por delegação do usuário em chat; **ratificado pelo usuário em 2026-11-03** | 2026-11-03 |
| Sem varredura de segredos no repositório (NFR-SEC-1, parte "fora do repositório") | pendência já registrada em `security.md` (gitleaks) | agente, por delegação do usuário em chat; **ratificado pelo usuário em 2026-11-03** | 2026-11-03 |
| Ataque ao login vindo de muitos IPs não é contido pelo balde por origem; atrás de um NAT compartilhado todos dividem o balde; a origem do IP no Traefik da VPS não foi verificada | o limite protege contra senha adivinhada por uma origem; com 12 caracteres e política, o risco restante é a indisponibilidade do login | agente, por delegação do usuário em chat; **ratificado pelo usuário em 2026-11-03** | 2026-11-03 |
| A senha fica visível em `docker inspect` do contêiner avulso enquanto o `run` dura (segundos) | só quem tem acesso ao Docker da VPS, que já pode ler o `.env.production` | agente, por delegação do usuário em chat; **ratificado pelo usuário em 2026-11-03** | 2026-11-03 |

As linhas decididas pelo agente por delegação foram ratificadas pelo usuário em 2026-11-03 (resposta "Aprovo e ratifico" no chat; tasks.md, T-6.8).
