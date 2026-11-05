# Rastreabilidade — 003-acesso-e-grupo

Os testes da 003 levam `[003]` na docstring: REQ, ABU e PROP são provisórios por mudança e se repetem em outras mudanças. Os controles
e ameaças da 003 começam em CTL-11 e THR-11 para não colidirem com os da 001 (até 7) e os da 002 (até 10). O `sdd_lint` não separa as
mudanças; a cobertura é conferida por leitura e por mutação (ver `validation.md`).

| ID | Descrição curta | Tarefas | Testes / evidência | Status |
|---|---|---|---|---|
| REQ-1.1 | entrar com e-mail e senha corretos cria a sessão | T-1.2, T-2.3 | `test_req_1_1_*` | ✔ em teste; não visto no ar |
| REQ-1.2 | e-mail ou senha errados: mesma resposta | T-1.2, T-2.3 | `test_req_1_2_*` | ✔ em teste |
| REQ-1.3 | sair encerra a sessão no servidor | T-1.2, T-2.3 | `test_req_1_3_*` | ✔ em teste |
| REQ-1.4 | sem login só passam token de proteção, entrar e aceitar | T-1.2, T-2.3 | `test_req_1_4_*` | ✔ em teste |
| REQ-2.1 | criar grupo | T-1.3, T-2.4, T-4.2 | `test_req_2_1_*` | ✔ em teste; não visto no ar |
| REQ-2.2 | um grupo por pessoa | T-1.3, T-2.4 | `test_req_2_2_*` | ✔ em teste |
| REQ-2.3 | grupo de 2 nunca recebe um terceiro | T-1.4, T-2.1, T-2.5 | `test_prop_2_*` (threads reais) | ✔ em teste |
| REQ-2.4 | perfil incompleto não cria grupo | T-1.3, T-2.4 | `test_req_2_4_*` | ✔ em teste |
| REQ-3.1 | gerar convite com código e validade | T-1.4, T-2.5, T-4.2 | `test_req_3_1_*` | ✔ em teste; não visto no ar |
| REQ-3.2 | novo convite invalida o anterior | T-1.4, T-2.1, T-2.5 | `test_req_3_2_*` | ✔ em teste |
| REQ-3.3 | convite expira em 7 dias | T-1.4, T-2.5 | `test_req_3_3_*` | ✔ em teste |
| REQ-3.4 | aceitar cria conta, perfil e entrada | T-1.4, T-2.5, T-4.2 | `test_req_3_4_*` | ✔ em teste; não visto no ar |
| REQ-3.5 | convite inválido: mesma resposta | T-1.4, T-2.5 | `test_req_3_5_*` | ✔ em teste |
| REQ-3.6 | e-mail já usado: mesma resposta | T-1.4, T-2.5 | `test_req_3_6_*` | ✔ em teste |
| REQ-3.7 | grupo cheio recusa convite | T-1.4, T-2.5 | `test_req_3_7_*` | ✔ em teste |
| REQ-4.1 | consultar o próprio perfil | T-1.3, T-2.4 | `test_req_4_1_*` | ✔ em teste |
| REQ-4.2 | alterar nome e cor | T-1.3, T-2.4 | `test_req_4_2_*` | ✔ em teste |
| REQ-4.3 | cor fora de `#RRGGBB` recusada | T-1.1, T-2.2 | `test_req_4_3_*` | ✔ em teste |
| REQ-4.4 | cor ilegível recusada | T-1.1, T-2.2 | `test_prop_1_*` | ✔ em teste |
| REQ-4.5 | cor igual ou indistinguível da do parceiro recusada | T-1.1, T-2.2 | `test_req_4_5_*` | ✔ em teste |
| REQ-4.6 | trocar senha encerra as outras sessões | T-1.3, T-2.4 | `test_req_4_6_*` | ✔ em teste |
| REQ-4.7 | senha atual errada ou nova fraca recusadas | T-1.3, T-2.4 | `test_req_4_7_*` | ✔ em teste |
| REQ-4.8 | parceiro vê nome e cor, nunca o e-mail | T-1.3, T-2.4 | `test_req_4_8_*` | ✔ em teste |
| REQ-4.9 | conta do administrador sem perfil: incompleto | T-1.3, T-2.4 | `test_req_4_9_*` | ✔ em teste |
| REQ-5.1 | sem sessão, tela de entrar | T-3.3, T-3.4 | `entrar_test` | planejado |
| REQ-5.2 | link de convite abre a criação de conta | T-3.3, T-3.4 | `convite_test` | planejado |
| REQ-5.3 | perfil, grupo e botão de convidar | T-3.3, T-3.4, T-3.5 | `perfil_test`, `grupo_test`, e2e | planejado |
| REQ-5.4 | erros em português, sem detalhe técnico | T-3.3, T-3.4 | `erros_test` | planejado |
| REQ-5.5 | perfil incompleto leva ao perfil primeiro | T-3.3, T-3.4 | `perfil_test` | planejado |
| NFR-SEC-1 | cookies sem leitura por script, só por HTTPS, com proteção de CSRF | T-1.2, T-2.3 | `test_nfr_sec_1_*` | ✔ em teste |
| NFR-SEC-2 | código do convite com 128 bits, só o hash gravado | T-1.4, T-2.5 | `test_nfr_sec_2_*` | ✔ em teste |
| NFR-SEC-3 | toda validação também no backend | T-1.3, T-2.4 | um teste 422 por regra | ✔ em teste |
| NFR-A11Y-1 | WCAG 2.2 AA nos dois temas | T-3.4, T-3.5 | e2e com relatório de acessibilidade | planejado |
| NFR-RESP-1 | 360 a 1280 px sem rolagem horizontal | T-3.4, T-3.5 | e2e | planejado |
| ABU-1 | limite de tentativas de senha | T-3.1, T-3.2, T-4.2 | `test_abu_1_*`; medição no ar | planejado |
| ABU-2 | não revelar se o e-mail existe | T-1.2, T-2.3 | `test_abu_2_*` | ✔ em teste |
| ABU-3 | adivinhar ou reutilizar o código | T-1.4, T-2.5 | `test_abu_3_*` | ✔ em teste |
| ABU-4 | CSRF recusado, inclusive em rota anônima | T-1.2, T-2.3 | `test_abu_4_*` | ✔ em teste |
| PROP-1 | cor aceita se e somente se contraste ≥ 3:1 nos dois fundos | T-1.1, T-2.2 | `test_prop_1_*` | ✔ em teste |
| PROP-2 | grupo nunca passa do limite, mesmo com aceites simultâneos | T-1.4, T-2.5 | `test_prop_2_*` | ✔ em teste |
| PROP-3 | código só aceito uma vez e nunca gravado | T-1.4, T-2.5 | `test_prop_3_*` | ✔ em teste |
| PROP-4 | resposta de falha igual com e sem conta | T-1.2, T-2.3 | `test_req_1_2_*`, `test_abu_2_*` | ✔ em teste |

Cadeia de segurança: THR → CTL → teste

| Ameaça | Controle | Requisito | Teste | Status |
|---|---|---|---|---|
| THR-11 | CTL-11 | ABU-1 | `test_abu_1_*`; medição no ar | planejado |
| THR-12 | CTL-12 | ABU-2, REQ-1.2, REQ-3.6 | `test_abu_2_*` | ✔ em teste |
| THR-13 | CTL-13 | ABU-3, NFR-SEC-2, REQ-3.5 | `test_prop_3_*`, `test_abu_3_*` | ✔ em teste |
| THR-14 | CTL-14 | REQ-2.3, REQ-3.7 | `test_prop_2_*` | ✔ em teste |
| THR-15 | CTL-15 | ABU-4 | `test_abu_4_*` | ✔ em teste |
| THR-16 | CTL-16 | NFR-SEC-1, REQ-4.6 | `test_nfr_sec_1_*`, `test_req_4_6_*` | ✔ em teste |
| THR-17 | CTL-17 | — | `test_req_isolamento_*` | ✔ em teste |
| THR-18 | CTL-18 | REQ-1.4 | `test_req_1_4_*` | ✔ em teste |
| THR-19 | CTL-19 | — | `test_ctl_19_*` (texto do nginx) | planejado |
| THR-20 | CTL-20 | — | verificação do build; revisão do `pubspec.yaml` | planejado |


Legenda: "✔ em teste" = executado em ambiente de teste (PostgreSQL real, threads reais), não na VPS. Faltam as linhas do front (REQ-5.x, NFR-A11Y-1, NFR-RESP-1) e da infra (ABU-1, CTL-11, CTL-19, CTL-20), que são das ondas 3 e 4.
