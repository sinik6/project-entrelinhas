# Rastreabilidade — 009-calendario

Os testes da 009 levam `[009]` na docstring. Os IDs desta mudança são únicos no projeto (histórias, ABU, PROP, CTL e THR numerados
sem repetir os das outras mudanças). Estado: tudo **planejado**; a coluna muda para ✔ conforme as tarefas fecham.

| ID | Descrição curta | Tarefas | Testes / evidência | Status |
|---|---|---|---|---|
| REQ-16.1 | QUANDO o membro pedir o calendário de um mês (AAAA-MM), O sistema DEVE d… | T-1.2, T-2.3 | `test_req_16_1_*` | planejado |
| REQ-16.2 | O sistema DEVE marcar escreveu quando houver registro da pessoa naquele … | T-1.1, T-2.2 | `test_req_16_2_*` | planejado |
| REQ-16.3 | O sistema DEVE marcar falhou quando o dia já terminou sem registro da pe… | T-1.1, T-1.3, T-2.1 | `test_req_16_3_*` | planejado |
| REQ-16.4 | O sistema DEVE marcar juntos no dia em que os dois membros entregaram co… | T-1.1 | `test_req_16_4_*` | planejado |
| REQ-16.5 | SE os dois entregaram no mesmo dia com mais de 2 horas de diferença, ou … | T-1.1 | `test_req_16_5_*` | planejado |
| REQ-16.6 | O sistema DEVE devolver, para cada membro, nome e cor, e NÃO DEVE devolv… | T-1.2, T-2.3 | `test_req_16_6_*` | planejado |
| REQ-16.7 | SE o mês estiver mal formado, for futuro ou anterior ao mês de entrada d… | T-1.2, T-2.3 | `test_req_16_7_*` | planejado |
| REQ-16.8 | QUANDO o participante não tiver grupo, O sistema DEVE devolver o calendá… | T-1.2, T-2.3 | `test_req_16_8_*` | planejado |
| REQ-16.9 | O estado de um dia DEVE depender só dos registros e da data de entrada, … | T-1.1, T-2.2 | `test_req_16_9_*` | planejado |
| REQ-17.1 | QUANDO o membro abrir o Calendário, O app DEVE mostrar a grade do mês at… | T-1.4, T-2.5 | `test_req_17_1_*` | planejado |
| REQ-17.2 | O app DEVE mostrar, em cada dia, um marcador por membro na cor dele: pre… | T-1.4, T-3.1, T-3.2 | `test_req_17_2_*` | planejado |
| REQ-17.3 | O app NÃO DEVE depender só da cor: cada estado tem forma própria e texto… | T-1.4 | `test_req_17_3_*` | planejado |
| REQ-17.4 | QUANDO o membro tocar num dia, O app DEVE abrir a lista dos registros da… | T-1.4, T-3.1, T-3.2 | `test_req_17_4_*` | planejado |
| REQ-17.5 | O app DEVE mostrar uma legenda dos marcadores. | T-1.4 | `test_req_17_5_*` | planejado |
| REQ-17.6 | SE o servidor recusar um pedido ou a sessão tiver acabado, ENTÃO O app D… | T-1.4, T-2.5 | `test_req_17_6_*` | planejado |
| NFR-CAL-1 | O app DEVE atender WCAG 2.2 AA e funcionar sem rolagem horizontal de 360… | T-1.4, T-2.5, T-3.1 | `test_nfr_cal_1_*` ou `design.md` §10 | planejado |
| NFR-CAL-2 | O sistema DEVE aplicar toda validação no backend, com teste de API (Art.… | T-1.2, T-2.4 | `test_nfr_cal_2_*` ou `design.md` §10 | planejado |
| NFR-CAL-3 | A rota DEVE responder com no máximo 3 consultas ao banco, independente d… | T-1.2, T-2.3 | `test_nfr_cal_3_*` ou `design.md` §10 | planejado |
| ABU-19 | SE alguém pedir o calendário de outro grupo ou de meses fora do interval… | T-1.2, T-2.3 | `test_abu_19_*` | planejado |
| ABU-20 | SE a entrega acontecer perto da meia-noite de São Paulo (23h59, 00:00, 0… | T-1.1, T-2.2 | `test_abu_20_*` | planejado |
| PROP-11 | Para qualquer conjunto de entregas, o estado de cada dia é o mesmo calcu… | T-1.1, T-2.2, T-3.3 | `test_prop_11_*` | planejado |
| PROP-12 | juntos é simétrico (não depende de quem entregou primeiro) e nunca é ver… | T-1.1, T-2.2, T-3.3 | `test_prop_12_*` | planejado |

Cadeia de segurança: THR → CTL → teste

| Ameaça | Controle | Requisito | Teste | Status |
|---|---|---|---|---|
| THR-71 | CTL-71 | ABU-19, REQ-16.7 | `test_abu_19_*`, `test_req_16_7_*` | planejado |
| THR-72 | CTL-72 | REQ-16.6 | `test_req_16_6_*` | planejado |
| THR-73 | CTL-73 | REQ-16.9, ABU-20, PROP-11 | `test_abu_20_*`, `test_prop_11_*` | planejado |
| THR-74 | CTL-74 | NFR-CAL-3 | `test_nfr_cal_3_*` | planejado |
