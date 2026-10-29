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

## Controles
| ID | Controle | Atende | Teste/evidência |
|---|---|---|---|
| CTL-1 | usuário existente que não é superusuário faz o comando recusar, sem promover | THR-1, ABU-2 | `test_abu_2_usuario_comum_existente_nao_e_promovido` |
| CTL-2 | senha obrigatória, recusa vazia/só espaços e passa por `AUTH_PASSWORD_VALIDATORS` (12+, comum, só números, similar ao usuário) | THR-2, REQ-2.1, REQ-2.2, ABU-3 | `test_req_2_1_…`, `test_req_2_2_…`, `test_abu_3_…` |
| CTL-3 | o comando imprime só o nome do usuário; erros listam motivos sem repetir a senha | THR-3, ABU-1, NFR-SEC-1 | `test_abu_1_senha_nao_vai_para_saida_nem_para_log`, `test_nfr_sec_1_senha_nao_aparece_na_saida` |
| CTL-4 | a senha vai por `docker compose run -e` só àquela execução; o compose de produção não cita a variável | THR-4, NFR-SEC-1 | `test_ctl_4_senha_nao_entra_no_compose_nem_no_servico_da_api` |
| CTL-5 | senha gravada só como hash; `.env.production` com modo 600 e fora do rsync (mudança 001) | THR-5, NFR-SEC-2 | `test_nfr_sec_2_senha_gravada_so_como_hash`, `test_ctl_2_segredos_fora_do_rsync` (001) |
| CTL-6 | roteador próprio para `POST` em `/entrelinhas/admin/login/` com `ratelimit` do Traefik (média 5, período 1 minuto, rajada 5), definido nos rótulos do compose; sem dependência nova | THR-6, ABU-4 | `test_abu_4_login_do_admin_tem_limite_de_5_por_minuto`; conferência após o deploy |

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
| A09 Log e alerta | sim | CTL-3; tentativas de login falhas não geram alerta (fora de escopo) |
| A10 Condições excepcionais | sim | `IntegrityError` na corrida tratado; qualquer erro encerra com código 1 |

## Dependências novas
| Pacote | Versão | Verificado no registro? | Motivo |
|---|---|---|---|
| (nenhuma) | | | |

## Riscos aceitos (somente pelo humano)
| Ameaça | Motivo | Quem aceitou | Data |
|---|---|---|---|
| THR-5 (senha em texto no `.env.production`, modo 600) | mesmo padrão do Vinculus; quem lê o arquivo já tem acesso de `deploy` à VPS | usuário | 2026-10-28 |
