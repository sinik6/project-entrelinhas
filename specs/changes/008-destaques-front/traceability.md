# Rastreabilidade — 008-destaques-front

Os testes da 008 levam `[008]` na docstring. Os IDs desta mudança são únicos no projeto (histórias, ABU, PROP, CTL e THR numerados
sem repetir os das outras mudanças). Estado: implementado e testado localmente; nada visto no ar. Evidência em `validation.md`.

| ID | Descrição curta | Tarefas | Testes / evidência | Status |
|---|---|---|---|---|
| REQ-15.1 | QUANDO o membro selecionar texto num registro com texto visível, O app D… | T-1.2, T-2.3 | `test_req_15_1_*` | ✔ em teste; não visto no ar |
| REQ-15.2 | QUANDO o membro confirmar o destaque, O app DEVE enviar posições em pont… | T-1.2, T-2.1, T-2.3, T-3.1, T-3.2 | `test_req_15_2_*` | ✔ em teste; não visto no ar |
| REQ-15.3 | O app DEVE desenhar cada destaque com fundo translúcido na cor de quem o… | T-1.1, T-2.2 | `test_req_15_3_*` | ✔ em teste; não visto no ar |
| REQ-15.4 | QUANDO o membro tocar num trecho destacado, O app DEVE abrir a folha com… | T-1.3, T-2.4, T-3.1, T-3.2 | `test_req_15_4_*` | ✔ em teste; não visto no ar |
| REQ-15.5 | QUANDO o membro comentar, editar o próprio comentário ou apagar o própri… | T-1.3, T-2.1 | `test_req_15_5_*` | ✔ em teste; não visto no ar |
| REQ-15.6 | QUANDO o autor apagar o destaque, O app DEVE avisar que os comentários t… | T-1.3 | `test_req_15_6_*` | ✔ em teste; não visto no ar |
| REQ-15.7 | SE dois destaques se sobrepuserem no ponto tocado, ENTÃO O app DEVE abri… | T-1.1, T-2.2 | `test_req_15_7_*` | ✔ em teste; não visto no ar |
| REQ-15.8 | SE o servidor recusar (limite, sem texto visível, sessão acabada), ENTÃO… | T-1.3 | `test_req_15_8_*` | ✔ em teste; não visto no ar |
| REQ-15.9 | ENQUANTO o registro for private ou sem texto visível, O app NÃO DEVE ofe… | T-1.2, T-2.3 | `test_req_15_9_*` | ✔ em teste; não visto no ar |
| NFR-DESTF-1 | O app DEVE atender WCAG 2.2 AA e funcionar sem rolagem horizontal de 360… | T-1.4, T-2.5, T-3.1, T-3.3 | `test_nfr_destf_1_*` ou `design.md` §10 | ✔ em teste; não visto no ar |
| NFR-DESTF-2 | O app NÃO DEVE interpretar texto de comentário ou de registro como HTML. | T-1.3 | `test_nfr_destf_2_*` ou `design.md` §10 | ✔ em teste; não visto no ar |
| NFR-DESTF-3 | Toda ação DEVE ser possível pelo teclado (selecionar, abrir a folha, com… | T-1.4, T-2.5 | `test_nfr_destf_3_*` ou `design.md` §10 | ✔ em teste; não visto no ar |
| ABU-17 | SE um comentário ou registro contiver marcação (<script>, <b>), ENTÃO O … | T-1.3, T-2.4 | `test_abu_17_*` | ✔ em teste; não visto no ar |
| ABU-18 | SE a pessoa tocar duas vezes em Destacar ou Comentar, ENTÃO O app DEVE e… | T-1.3, T-2.3, T-2.4 | `test_abu_18_*` | ✔ em teste; não visto no ar |
| PROP-10 | Para qualquer texto visível (emoji, acento composto, quebras) e qualquer… | T-1.1, T-2.2, T-3.3 | `test_prop_10_*` | ✔ em teste; não visto no ar |

Cadeia de segurança: THR → CTL → teste

| Ameaça | Controle | Requisito | Teste | Status |
|---|---|---|---|---|
| THR-61 | CTL-61 | ABU-17, NFR-DESTF-2 | `destaque_folha_test.dart` | ✔ em teste; não visto no ar |
| THR-62 | CTL-62 | REQ-15.2, PROP-10 | `destaque_selecao_test.dart`, `destaque_pintura_test.dart` | ✔ em teste; não visto no ar |
| THR-63 | CTL-63 | ABU-18 | `destaque_folha_test.dart` | ✔ em teste; não visto no ar |
