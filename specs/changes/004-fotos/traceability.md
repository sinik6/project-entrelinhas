# Rastreabilidade — 004-fotos

Os testes da 004 levam `[004]` na docstring. Os IDs desta mudança são únicos no projeto (histórias, ABU, PROP, CTL e THR numerados
sem repetir os das outras mudanças). Estado em 2026-11-05: implementado e testado localmente; nada disso foi visto no ar ainda (T-4.1). Evidência em `validation.md`.

| ID | Descrição curta | Tarefas | Testes / evidência | Status |
|---|---|---|---|---|
| REQ-6.1 | QUANDO o participante enviar um arquivo JPEG, PNG ou WebP válido de até … | T-1.1, T-2.2 | `test_req_6_1_*` | ✔ em teste; não visto no ar |
| REQ-6.2 | SE o conteúdo do arquivo não for uma imagem JPEG, PNG ou WebP (mesmo que… | T-1.1 | `test_req_6_2_*` | ✔ em teste; não visto no ar |
| REQ-6.3 | SE o arquivo passar de 8 MB ou o lado maior da imagem passar de 4096 px,… | T-1.1 | `test_req_6_3_*` | ✔ em teste; não visto no ar |
| REQ-6.4 | O sistema DEVE guardar a foto recodificada, sem metadados, com nome gera… | T-1.1 | `test_req_6_4_*` | ✔ em teste; não visto no ar |
| REQ-6.5 | QUANDO o autor consultar uma foto de manuscrito dele, O sistema DEVE dev… | T-1.2, T-2.3 | `test_req_6_5_*` | ✔ em teste; não visto no ar |
| REQ-6.6 | SE outra pessoa (do mesmo grupo ou de outro) consultar uma foto de manus… | T-1.2 | `test_req_6_6_*` | ✔ em teste; não visto no ar |
| REQ-6.7 | QUANDO o autor apagar uma foto avulsa dele, O sistema DEVE remover o reg… | T-1.2 | `test_req_6_7_*` | ✔ em teste; não visto no ar |
| REQ-6.8 | SE o autor tentar apagar uma foto já anexada a registro, ENTÃO O sistema… | T-1.2 | `test_req_6_8_*` | ✔ em teste; não visto no ar |
| REQ-6.9 | QUANDO o comando limpar_fotos rodar, O sistema DEVE apagar as fotos avul… | T-1.2, T-2.5 | `test_req_6_9_*` | ✔ em teste; não visto no ar |
| REQ-7.1 | QUANDO o participante enviar uma imagem válida com a finalidade perfil e… | T-1.3, T-2.4 | `test_req_7_1_*` | ✔ em teste; não visto no ar |
| REQ-7.2 | QUANDO o participante trocar ou remover a foto de perfil, O sistema DEVE… | T-1.3 | `test_req_7_2_*` | ✔ em teste; não visto no ar |
| REQ-7.3 | QUANDO o participante consultar o grupo, O sistema DEVE incluir, para ca… | T-1.3 | `test_req_7_3_*` | ✔ em teste; não visto no ar |
| REQ-7.4 | QUANDO um membro do grupo consultar a foto de perfil da outra pessoa do … | T-1.3, T-3.5 | `test_req_7_4_*` | ✔ em teste; não visto no ar |
| REQ-7.5 | SE o participante tentar usar como foto de perfil uma foto de finalidade… | T-1.3 | `test_req_7_5_*` | ✔ em teste; não visto no ar |
| REQ-7.6 | QUANDO o participante abrir o perfil, O app DEVE permitir escolher uma f… | T-3.3, T-3.4, T-3.5 | `test_req_7_6_*` | ✔ em teste; não visto no ar |
| REQ-7.7 | SE o servidor recusar a foto, ENTÃO O app DEVE mostrar a mensagem em por… | T-3.3, T-3.4 | `test_req_7_7_*` | ✔ em teste; não visto no ar |
| REQ-7.8 | ENQUANTO a foto de perfil não existir ou não carregar, O app DEVE mostra… | T-3.3, T-3.4 | `test_req_7_8_*` | ✔ em teste; não visto no ar |
| NFR-FOTO-1 | O sistema DEVE gravar as fotos fora da pasta pública (nenhum static nem … | T-3.1, T-3.2 | `test_nfr_foto_1_*` ou `design.md` §10 | ✔ em teste; não visto no ar |
| NFR-FOTO-2 | O sistema DEVE limitar o corpo do envio de foto a 9 MB no nginx e a 8 MB… | T-3.1, T-3.2 | `test_nfr_foto_2_*` ou `design.md` §10 | ✔ em teste; não visto no ar |
| NFR-FOTO-3 | O app DEVE funcionar sem rolagem horizontal de 360 px a 1280 px e atende… | T-3.3, T-3.5 | `test_nfr_foto_3_*` ou `design.md` §10 | ✔ em teste; não visto no ar |
| NFR-FOTO-4 | O sistema DEVE aplicar toda validação no backend, com teste de API (Art.… | T-1.1, T-2.6 | `test_nfr_foto_4_*` ou `design.md` §10 | ✔ em teste; não visto no ar |
| ABU-5 | SE alguém enviar um arquivo que parece imagem mas carrega outro conteúdo… | T-1.1, T-2.2 | `test_abu_5_*` | ✔ em teste; não visto no ar |
| ABU-6 | SE alguém trocar o identificador da foto na URL, ENTÃO O sistema DEVE re… | T-1.2, T-2.3 | `test_abu_6_*` | ✔ em teste; não visto no ar |
| ABU-7 | SE alguém enviar fotos em volume para encher o disco, ENTÃO O sistema DE… | T-1.2, T-2.3 | `test_abu_7_*` | ✔ em teste; não visto no ar |
| PROP-5 | Para qualquer arquivo enviado, o que é guardado é sempre uma imagem deco… | T-1.1, T-2.2, T-4.2 | `test_prop_5_*` | ✔ em teste; não visto no ar |

Cadeia de segurança: THR → CTL → teste

| Ameaça | Controle | Requisito | Teste | Status |
|---|---|---|---|---|
| THR-21 | CTL-21 | ABU-5, REQ-6.2, REQ-6.4 | `test_req_6_2_*`, `test_req_6_4_*`, `test_prop_5_*` | ✔ em teste; não visto no ar |
| THR-22 | CTL-22 | ABU-7, NFR-FOTO-2 | `test_ctl_22_*`, `test_req_6_3_*`, `test_abu_7_*` | ✔ em teste; não visto no ar |
| THR-23 | CTL-23 | ABU-6, REQ-6.6, REQ-7.4 | `test_req_6_6_*`, `test_req_7_4_*` | ✔ em teste; não visto no ar |
| THR-24 | CTL-24 | REQ-6.5, NFR-FOTO-1 | `test_req_6_5_*`, `test_ctl_24_*` | ✔ em teste; não visto no ar |
| THR-25 | CTL-21 | ABU-5, REQ-6.2, REQ-6.4 | `test_req_6_2_*`, `test_req_6_4_*`, `test_prop_5_*` | ✔ em teste; não visto no ar |
| THR-26 | CTL-25 | — | `test_ctl_25_*` (texto do deploy); conferência no ar | ✔ em teste; não visto no ar |
