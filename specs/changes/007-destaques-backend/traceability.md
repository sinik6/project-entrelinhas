# Rastreabilidade — 007-destaques-backend

Os testes da 007 levam `[007]` na docstring. Os IDs desta mudança são únicos no projeto (histórias, ABU, PROP, CTL e THR numerados
sem repetir os das outras mudanças). Estado: implementado e testado localmente; nada visto no ar. Evidência em `validation.md`.

| ID | Descrição curta | Tarefas | Testes / evidência | Status |
|---|---|---|---|---|
| REQ-13.1 | QUANDO um membro do grupo enviar inicio e fim válidos para um registro c… | T-1.1, T-2.2, T-2.3, T-3.1 | `test_req_13_1_*` | ✔ em teste; não visto no ar |
| REQ-13.2 | SE inicio e fim não forem inteiros com 0 ≤ inicio < fim ≤ tamanho do tex… | T-1.1, T-2.1 | `test_req_13_2_*` | ✔ em teste; não visto no ar |
| REQ-13.3 | SE o registro for private (para o parceiro e para o autor), ENTÃO O sist… | T-1.1, T-3.1 | `test_req_13_3_*` | ✔ em teste; não visto no ar |
| REQ-13.4 | QUANDO um destaque for criado com um comentário, O sistema DEVE guardar … | T-1.1, T-2.3 | `test_req_13_4_*` | ✔ em teste; não visto no ar |
| REQ-13.5 | SE a pessoa já tiver 50 destaques no registro, ENTÃO O sistema DEVE recu… | T-1.2, T-2.4 | `test_req_13_5_*` | ✔ em teste; não visto no ar |
| REQ-13.6 | QUANDO o autor do destaque o apagar, O sistema DEVE apagar também os com… | T-1.2 | `test_req_13_6_*` | ✔ em teste; não visto no ar |
| REQ-13.7 | SE outra pessoa tentar apagar um destaque que não criou, ENTÃO O sistema… | T-1.2, T-2.4 | `test_req_13_7_*` | ✔ em teste; não visto no ar |
| REQ-14.1 | QUANDO um membro do grupo comentar um destaque, O sistema DEVE guardar o… | T-1.2, T-2.2, T-2.4, T-3.1 | `test_req_14_1_*` | ✔ em teste; não visto no ar |
| REQ-14.2 | SE o destaque já tiver 20 comentários, ENTÃO O sistema DEVE recusar com … | T-1.2 | `test_req_14_2_*` | ✔ em teste; não visto no ar |
| REQ-14.3 | QUANDO o autor do comentário o editar, O sistema DEVE gravar o novo text… | T-1.2 | `test_req_14_3_*` | ✔ em teste; não visto no ar |
| REQ-14.4 | QUANDO o autor do comentário o apagar, O sistema DEVE removê-lo. | T-1.2, T-2.4 | `test_req_14_4_*` | ✔ em teste; não visto no ar |
| REQ-14.5 | QUANDO um membro listar os destaques de um registro, O sistema DEVE devo… | T-1.3, T-2.5 | `test_req_14_5_*` | ✔ em teste; não visto no ar |
| REQ-14.6 | SE o registro, o destaque ou o comentário for de outro grupo, ENTÃO O si… | T-1.3, T-2.5 | `test_req_14_6_*` | ✔ em teste; não visto no ar |
| REQ-14.7 | O texto de comentário ou do trecho destacado NÃO DEVE aparecer em log ne… | T-1.3, T-2.5 | `test_req_14_7_*` | ✔ em teste; não visto no ar |
| NFR-DEST-1 | O sistema DEVE aplicar toda validação no backend, com teste de API (Art.… | T-1.3, T-2.7 | `test_nfr_dest_1_*` ou `design.md` §10 | ✔ em teste; não visto no ar |
| NFR-DEST-2 | O Django Admin NÃO DEVE mostrar destaques nem comentários. | T-1.3, T-2.5 | `test_nfr_dest_2_*` ou `design.md` §10 | ✔ em teste; não visto no ar |
| ABU-14 | SE o parceiro tentar descobrir o texto escondido ou o tamanho dele por p… | T-1.1, T-2.3, T-2.6, T-3.2 | `test_abu_14_*` | ✔ em teste; não visto no ar |
| ABU-15 | SE alguém criar destaques ou comentários em volume (pedidos simultâneos)… | T-1.2, T-2.4 | `test_abu_15_*` | ✔ em teste; não visto no ar |
| ABU-16 | SE alguém tentar editar ou apagar o comentário ou o destaque de outra pe… | T-1.2, T-2.4, T-2.6 | `test_abu_16_*` | ✔ em teste; não visto no ar |
| PROP-9 | Para qualquer registro, visibilidade e posição válida, o trecho destacad… | T-1.1, T-2.3, T-2.6, T-3.2 | `test_prop_9_*` | ✔ em teste; não visto no ar |

Cadeia de segurança: THR → CTL → teste

| Ameaça | Controle | Requisito | Teste | Status |
|---|---|---|---|---|
| THR-51 | CTL-51 | ABU-14, REQ-13.2 | `test_abu_14_*`, `test_req_13_2_*` | ✔ em teste; não visto no ar |
| THR-52 | CTL-52 | REQ-13.3, REQ-14.6 | `test_req_13_3_*`, `test_req_14_6_*` | ✔ em teste; não visto no ar |
| THR-53 | CTL-53 | ABU-16, REQ-13.7, REQ-14.3 | `test_abu_16_*`, `test_req_13_7_*` | ✔ em teste; não visto no ar |
| THR-54 | CTL-54 | ABU-15, REQ-13.5, REQ-14.2 | `test_abu_15_*` (threads reais) | ✔ em teste; não visto no ar |
| THR-55 | CTL-55 | REQ-14.7, NFR-DEST-2 | `test_nfr_dest_*` | ✔ em teste; não visto no ar |
| THR-56 | CTL-56 | PROP-9 | `test_nfr_dest_*`, `test_prop_9_*` | ✔ em teste; não visto no ar |
