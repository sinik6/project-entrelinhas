# Rastreabilidade — 005-registros-backend

Os testes da 005 levam `[005]` na docstring. Os IDs desta mudança são únicos no projeto (histórias, ABU, PROP, CTL e THR numerados
sem repetir os das outras mudanças). Estado em 2026-11-05: implementado e testado localmente; nada visto no ar ainda (T-3.1). Evidência em `validation.md`.

| ID | Descrição curta | Tarefas | Testes / evidência | Status |
|---|---|---|---|---|
| REQ-8.1 | QUANDO um participante com grupo enviar texto, visibilidade e de 1 a 3 f… | T-1.2, T-2.3, T-3.1 | `test_req_8_1_*` | ✔ em teste; não visto no ar |
| REQ-8.2 | SE faltar foto, ou houver mais de 3, ou uma foto não for do autor, não f… | T-1.2, T-2.3 | `test_req_8_2_*` | ✔ em teste; não visto no ar |
| REQ-8.3 | SE o texto tiver menos de 10 caracteres úteis, mais de 20 000, ou caract… | T-1.2, T-2.2 | `test_req_8_3_*` | ✔ em teste; não visto no ar |
| REQ-8.4 | QUANDO a visibilidade for partial, O sistema DEVE exigir inicio e fim co… | T-1.2, T-2.1, T-2.2 | `test_req_8_4_*` | ✔ em teste; não visto no ar |
| REQ-8.5 | SE o autor já tiver entregue um registro naquele dia, ENTÃO O sistema DE… | T-1.2, T-2.1, T-2.3 | `test_req_8_5_*` | ✔ em teste; não visto no ar |
| REQ-8.6 | SE o participante não pertencer a um grupo, ENTÃO O sistema DEVE recusar… | T-1.2, T-2.3 | `test_req_8_6_*` | ✔ em teste; não visto no ar |
| REQ-8.7 | O sistema DEVE recusar qualquer tentativa de editar, apagar ou mudar a v… | T-1.2, T-2.3 | `test_req_8_7_*` | ✔ em teste; não visto no ar |
| REQ-9.1 | QUANDO o autor ler o próprio registro, O sistema DEVE devolver texto int… | T-1.3, T-2.4 | `test_req_9_1_*` | ✔ em teste; não visto no ar |
| REQ-9.2 | QUANDO o parceiro ler um registro full, O sistema DEVE devolver o texto … | T-1.1, T-2.2 | `test_req_9_2_*` | ✔ em teste; não visto no ar |
| REQ-9.3 | QUANDO o parceiro ler um registro partial, O sistema DEVE devolver apena… | T-1.1, T-2.2, T-2.6, T-3.1 | `test_req_9_3_*` | ✔ em teste; não visto no ar |
| REQ-9.4 | QUANDO o parceiro ler um registro private, O sistema DEVE devolver só a … | T-1.1, T-2.2, T-3.1 | `test_req_9_4_*` | ✔ em teste; não visto no ar |
| REQ-9.5 | QUANDO o parceiro pedir a foto de um registro partial ou private, O sist… | T-1.3, T-2.4, T-2.6 | `test_req_9_5_*` | ✔ em teste; não visto no ar |
| REQ-9.6 | SE o registro for de outro grupo, ENTÃO O sistema DEVE responder 404, ta… | T-1.3, T-2.4 | `test_req_9_6_*` | ✔ em teste; não visto no ar |
| REQ-9.8 | QUANDO o autor sair do grupo (ou mudar de grupo), O sistema DEVE continu… | T-1.3 | `test_req_9_8_*` | ✔ em teste; não visto no ar |
| REQ-9.7 | O texto escondido NÃO DEVE aparecer em nenhum ponto de nenhuma resposta … | T-1.3, T-2.4, T-3.2 | `test_req_9_7_*` | ✔ em teste; não visto no ar |
| REQ-10.1 | QUANDO o participante pedir os registros de um mês (AAAA-MM), O sistema … | T-1.4, T-2.4 | `test_req_10_1_*` | ✔ em teste; não visto no ar |
| REQ-10.2 | SE o mês estiver mal formado ou for futuro, ENTÃO O sistema DEVE recusar… | T-1.4, T-2.4 | `test_req_10_2_*` | ✔ em teste; não visto no ar |
| REQ-10.3 | QUANDO o participante não tiver grupo, O sistema DEVE devolver só os reg… | T-1.4, T-2.4 | `test_req_10_3_*` | ✔ em teste; não visto no ar |
| NFR-REG-1 | O sistema DEVE concentrar a regra de visibilidade em um único ponto do c… | T-1.1, T-1.5, T-2.2 | `test_nfr_reg_1_*` ou `design.md` §10 | ✔ em teste; não visto no ar |
| NFR-REG-2 | O sistema DEVE aplicar toda validação no backend, com teste de API (Art.… | T-1.2, T-2.7 | `test_nfr_reg_2_*` ou `design.md` §10 | ✔ em teste; não visto no ar |
| NFR-REG-3 | O sistema NÃO DEVE registrar em log texto, trecho, nome de foto nem corp… | T-1.5, T-2.5 | `test_nfr_reg_3_*` ou `design.md` §10 | ✔ em teste; não visto no ar |
| NFR-REG-4 | O Django Admin NÃO DEVE listar nem mostrar o texto dos registros. | T-1.5, T-2.5 | `test_nfr_reg_4_*` ou `design.md` §10 | ✔ em teste; não visto no ar |
| ABU-8 | SE o parceiro tentar ler o texto escondido por qualquer rota (lista, det… | T-1.3, T-2.4 | `test_abu_8_*` | ✔ em teste; não visto no ar |
| ABU-9 | SE alguém tentar entregar dois registros no mesmo dia em pedidos simultâ… | T-1.2, T-2.1, T-2.3 | `test_abu_9_*` | ✔ em teste; não visto no ar |
| ABU-10 | SE alguém trocar o identificador de um registro ou de uma foto, ENTÃO O … | T-1.3, T-2.4 | `test_abu_10_*` | ✔ em teste; não visto no ar |
| ABU-11 | SE alguém enviar trecho com valores absurdos (negativos, gigantes, inver… | T-1.2, T-2.3 | `test_abu_11_*` | ✔ em teste; não visto no ar |
| PROP-6 | Para qualquer texto, visibilidade e trecho, tudo o que o parceiro recebe… | T-1.1, T-2.2, T-2.6, T-3.2 | `test_prop_6_*` | ✔ em teste; não visto no ar |
| PROP-7 | Para qualquer texto (com emoji, acentos compostos e quebras de linha) e … | T-1.1, T-2.2 | `test_prop_7_*` | ✔ em teste; não visto no ar |

Cadeia de segurança: THR → CTL → teste

| Ameaça | Controle | Requisito | Teste | Status |
|---|---|---|---|---|
| THR-31 | CTL-31 | REQ-9.3, REQ-9.4, REQ-9.7, NFR-REG-1, PROP-6 | `test_req_9_7_*`, `test_prop_6_*`, `test_nfr_reg_1_*` | ✔ em teste; não visto no ar |
| THR-31 | CTL-32 | ABU-8 | `test_req_9_7_*`; roteiro de mutação (T-2.6) | ✔ em teste; não visto no ar |
| THR-32 | CTL-33 | REQ-9.5 | `test_req_9_5_*` | ✔ em teste; não visto no ar |
| THR-33 | CTL-31 | REQ-9.3, REQ-9.4, REQ-9.7, NFR-REG-1, PROP-6 | `test_req_9_7_*`, `test_prop_6_*`, `test_nfr_reg_1_*` | ✔ em teste; não visto no ar |
| THR-34 | CTL-34 | REQ-8.5, ABU-9 | `test_abu_9_*` (threads reais) | ✔ em teste; não visto no ar |
| THR-35 | CTL-35 | ABU-10, REQ-9.6 | `test_abu_10_*`, `test_req_9_6_*` | ✔ em teste; não visto no ar |
| THR-36 | CTL-36 | REQ-8.2 | `test_req_8_2_*` | ✔ em teste; não visto no ar |
| THR-37 | CTL-37 | NFR-REG-3, NFR-REG-4 | `test_nfr_reg_3_*`, `test_nfr_reg_4_*` | ✔ em teste; não visto no ar |
| THR-38 | CTL-39 | NFR-REG-4 | `test_nfr_reg_4_*`; ADR-0010 aceito pelo dono | ✔ em teste; não visto no ar |
| THR-40 | CTL-40 | REQ-9.8 | `test_troca_de_grupo.py` | ✔ em teste; não visto no ar |
| THR-39 | CTL-38 | REQ-8.4, ABU-11 | `test_req_8_4_*`, `test_abu_11_*` | ✔ em teste; não visto no ar |
