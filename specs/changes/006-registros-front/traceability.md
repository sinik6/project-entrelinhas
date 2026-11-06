# Rastreabilidade — 006-registros-front

Os testes da 006 levam `[006]` na docstring. Os IDs desta mudança são únicos no projeto (histórias, ABU, PROP, CTL e THR numerados
sem repetir os das outras mudanças). Estado em 2026-11-06: implementado e testado localmente; testado também no navegador, na pilha local (um caminho: `partial` com emoji); nada visto no ar. Evidência em `validation.md`.

| ID | Descrição curta | Tarefas | Testes / evidência | Status |
|---|---|---|---|---|
| REQ-11.1 | QUANDO o participante com grupo abrir Hoje sem ter entregue, O app DEVE … | T-1.2, T-2.4 | `hoje_test.dart` | ✔ em teste; não visto no ar |
| REQ-11.2 | ENQUANTO faltar texto com 10 caracteres úteis, ou foto, ou visibilidade,… | T-1.2 | `hoje_test.dart`, `texto_test.dart` (caracteres úteis) | ✔ em teste; não visto no ar |
| REQ-11.3 | QUANDO o participante escolher "só um trecho", selecionar parte do texto… | T-1.3, T-3.1 | `trecho_test.dart`; navegador local (prévia "tudo bem hoje") | ✔ em teste; parte no navegador local; não visto no ar |
| REQ-11.4 | O app DEVE enviar o trecho em pontos de código, convertendo da posição U… | T-1.1, T-1.3, T-2.1, T-2.2 | `texto_test.dart`, `trecho_test.dart` | ✔ em teste; não visto no ar |
| REQ-11.5 | QUANDO o participante tocar em Entregar, O app DEVE pedir confirmação co… | T-1.2 | `hoje_test.dart`, `trecho_test.dart` | ✔ em teste; não visto no ar |
| REQ-11.6 | QUANDO o participante confirmar, O app DEVE enviar as fotos, depois o re… | T-1.2, T-2.3, T-3.2 | `hoje_test.dart`, `api_http_test.dart`; navegador local (fotos 201, registro 201) | ✔ em teste; parte no navegador local; não visto no ar |
| REQ-11.7 | SE o envio de uma foto ou do registro falhar, ENTÃO O app DEVE mostrar a… | T-1.2 | `hoje_test.dart` | ✔ em teste; não visto no ar |
| REQ-11.8 | SE o servidor responder que o dia já foi entregue, ENTÃO O app DEVE most… | T-1.2 | `hoje_test.dart` | ✔ em teste; não visto no ar |
| REQ-11.9 | O app NÃO DEVE gravar o texto, o trecho nem as fotos no armazenamento do… | T-1.5, T-2.4, T-3.3 | `sem_persistencia_test.dart`; recarregar no navegador descartou o rascunho | ✔ em teste; parte no navegador local; não visto no ar |
| REQ-12.1 | QUANDO o participante abrir o Diário, O app DEVE mostrar os registros do… | T-1.4, T-2.3, T-2.5, T-3.2 | `diario_test.dart`, `api_http_test.dart` | ✔ em teste; não visto no ar |
| REQ-12.2 | O app DEVE mostrar, em cada registro, nome e cor de quem escreveu, o dia… | T-1.4 | `diario_test.dart` | ✔ em teste; não visto no ar |
| REQ-12.3 | QUANDO o registro for da outra pessoa, O app DEVE mostrar o texto visíve… | T-1.4, T-3.1 | `diario_test.dart`; navegador local (visão da Bia) | ✔ em teste; parte no navegador local; não visto no ar |
| REQ-12.4 | QUANDO o registro for do próprio participante, O app DEVE mostrar o text… | T-1.4 | `diario_test.dart` | ✔ em teste; não visto no ar |
| REQ-12.5 | QUANDO o participante tocar numa foto, O app DEVE abri-la em tela cheia … | T-1.4 | `diario_test.dart` | ✔ em teste; não visto no ar |
| REQ-12.6 | SE não houver registro no mês, ENTÃO O app DEVE mostrar a mensagem "Nenh… | T-1.4 | `diario_test.dart` | ✔ em teste; não visto no ar |
| REQ-12.7 | SE o servidor recusar um pedido ou a sessão tiver acabado, ENTÃO O app D… | T-1.4, T-2.5 | `diario_test.dart`, `hoje_test.dart` | ✔ em teste; não visto no ar |
| NFR-TELA-1 | O app DEVE atender WCAG 2.2 AA e funcionar sem rolagem horizontal de 360… | T-1.5, T-2.6, T-3.1 | `acessibilidade_test.dart` (6 telas novas, 2 temas, 360 e 1280 px) | ✔ em teste; não visto no ar |
| NFR-TELA-2 | O app NÃO DEVE interpretar o texto de registro como HTML nem como marcaç… | T-1.4, T-2.5 | `diario_test.dart` | ✔ em teste; não visto no ar |
| NFR-TELA-3 | O app DEVE funcionar com o teclado: toda ação alcançável sem mouse. | T-1.5, T-2.6 | `acessibilidade_test.dart` (alvos de toque e rótulos); sem teste de teclado dedicado | ✔ em teste; não visto no ar |
| ABU-12 | SE a pessoa tocar duas vezes em Entregar (ou o clique repetir por rede l… | T-1.2, T-2.4 | `duplo_toque_test.dart` | ✔ em teste; não visto no ar |
| ABU-13 | SE um texto de registro contiver marcação (<script>, <b>, &lt;), ENTÃO O… | T-1.4, T-2.5 | `diario_test.dart` | ✔ em teste; não visto no ar |
| PROP-8 | Para qualquer texto (emoji, acento composto, quebra de linha, bandeira) … | T-1.1, T-1.3, T-2.2, T-3.3 | `texto_test.dart` (600 sorteios, semente fixa), `trecho_test.dart` | ✔ em teste; não visto no ar |

Cadeia de segurança: THR → CTL → teste

| Ameaça | Controle | Requisito | Teste | Status |
|---|---|---|---|---|
| THR-41 | CTL-41 | REQ-11.9 | `sem_persistencia_test.dart` (varredura do código e do que fica gravado) | ✔ em teste; não visto no ar |
| THR-42 | CTL-42 | REQ-11.3, REQ-11.4, PROP-8 | `texto_test.dart`, `trecho_test.dart`; E2E com emoji | ✔ em teste; não visto no ar |
| THR-43 | CTL-43 | NFR-TELA-2, ABU-13 | `diario_test.dart` (texto com marcação) | ✔ em teste; não visto no ar |
| THR-44 | CTL-44 | REQ-11.5, ABU-12 | `hoje_test.dart`, `duplo_toque_test.dart` | ✔ em teste; não visto no ar |
| THR-45 | CTL-45 | — | `test_req_6_5_*` (da 004); navegador local: a foto veio com 200 pelo cookie | ✔ em teste; não visto no ar |
