# Rastreabilidade — 010-lembretes

Os testes da 010 levam `[010]` na docstring. Os IDs desta mudança são únicos no projeto (histórias, ABU, PROP, CTL e THR numerados
sem repetir os das outras mudanças). Estado: tudo **planejado**; a coluna muda para ✔ conforme as tarefas fecham.

| ID | Descrição curta | Tarefas | Testes / evidência | Status |
|---|---|---|---|---|
| REQ-18.1 | O app DEVE ter manifesto válido (nome, nome curto, ícones de 192 e 512 p… | T-4.1, T-4.2 | `test_req_18_1_*` | planejado |
| REQ-18.2 | QUANDO o participante ligar o lembrete em Perfil e permitir notificações… | T-4.1, T-4.3 | `test_req_18_2_*` | planejado |
| REQ-18.3 | QUANDO o servidor receber uma assinatura válida, O sistema DEVE guardá-l… | T-1.1, T-2.2 | `test_req_18_3_*` | planejado |
| REQ-18.4 | SE o endereço da assinatura não for HTTPS de um serviço de push da lista… | T-1.1 | `test_req_18_4_*` | planejado |
| REQ-18.5 | SE a pessoa já tiver 5 assinaturas, ENTÃO O sistema DEVE recusar com 409. | T-1.1 | `test_req_18_5_*` | planejado |
| REQ-18.6 | QUANDO o participante desligar o lembrete, O app DEVE cancelar a assinat… | T-1.1, T-2.2, T-4.1, T-4.3 | `test_req_18_6_*` | planejado |
| REQ-18.7 | SE a permissão for negada ou o navegador não suportar push, ENTÃO O app … | T-4.1, T-4.3 | `test_req_18_7_*` | planejado |
| REQ-18.8 | O app DEVE mostrar o estado do lembrete (ligado neste aparelho, desligad… | T-4.1, T-4.3 | `test_req_18_8_*` | planejado |
| REQ-19.1 | QUANDO der 21h30 em America/Sao_Paulo, O disparador DEVE enviar o aviso … | T-1.2, T-2.3, T-5.2 | `test_req_19_1_*` | planejado |
| REQ-19.2 | O disparador NÃO DEVE enviar a quem já entregou o dia. | T-1.2, T-5.2 | `test_req_19_2_*` | planejado |
| REQ-19.3 | O disparador NÃO DEVE enviar mais de um aviso por pessoa por dia, mesmo … | T-1.2, T-1.3 | `test_req_19_3_*` | planejado |
| REQ-19.4 | SE o serviço push responder que a assinatura não existe mais (404 ou 410… | T-1.2 | `test_req_19_4_*` | planejado |
| REQ-19.5 | SE o disparador estiver fora do ar às 21h30 e voltar até as 23h00, ENTÃO… | T-1.2 | `test_req_19_5_*` | planejado |
| REQ-19.6 | O aviso DEVE trazer só o texto genérico e o endereço da tela Hoje; NÃO D… | T-1.2, T-2.3 | `test_req_19_6_*` | planejado |
| REQ-19.7 | QUANDO o participante tocar na notificação, O service worker DEVE abrir … | T-4.1, T-4.2, T-5.2 | `test_req_19_7_*` | planejado |
| REQ-19.8 | SE o envio a um aparelho falhar por outro motivo (rede, 5xx), ENTÃO O di… | T-1.2, T-2.3 | `test_req_19_8_*` | planejado |
| NFR-LEMB-1 | O sistema DEVE guardar as chaves VAPID só em segredos do ambiente, nunca… | T-1.3, T-3.1, T-3.2, T-5.1 | `test_nfr_lemb_1_*` ou `design.md` §10 | planejado |
| NFR-LEMB-2 | O service worker NÃO DEVE guardar em cache dados da API nem do diário (s… | T-3.1, T-4.1, T-4.2 | `test_nfr_lemb_2_*` ou `design.md` §10 | planejado |
| NFR-LEMB-3 | O disparador DEVE ter verificação de saúde e reiniciar sozinho (restart:… | T-2.3, T-3.1, T-3.2 | `test_nfr_lemb_3_*` ou `design.md` §10 | planejado |
| NFR-LEMB-4 | O app DEVE atender WCAG 2.2 AA na tela do lembrete e funcionar sem rolag… | T-4.1, T-4.3 | `test_nfr_lemb_4_*` ou `design.md` §10 | planejado |
| NFR-LEMB-5 | O sistema DEVE aplicar toda validação no backend, com teste de API (Art.… | T-1.1, T-2.4 | `test_nfr_lemb_5_*` ou `design.md` §10 | planejado |
| ABU-21 | SE alguém enviar como assinatura um endereço interno ou de terceiros (pa… | T-1.1, T-2.2, T-5.3 | `test_abu_21_*` | planejado |
| ABU-22 | SE alguém tentar remover ou ler a assinatura de outra pessoa, ENTÃO O si… | T-1.1, T-2.2 | `test_abu_22_*` | planejado |
| ABU-23 | SE o disparador for iniciado duas vezes, ou reiniciado no meio do envio,… | T-1.3, T-2.3, T-5.3 | `test_abu_23_*` | planejado |
| PROP-13 | Para qualquer conjunto de pessoas, assinaturas, entregas e instantes (an… | T-1.2, T-2.3, T-5.3 | `test_prop_13_*` | planejado |

Cadeia de segurança: THR → CTL → teste

| Ameaça | Controle | Requisito | Teste | Status |
|---|---|---|---|---|
| THR-81 | CTL-81 | ABU-21, REQ-18.4 | `test_req_18_4_*`, `test_abu_21_*` | planejado |
| THR-82 | CTL-82 | ABU-22 | `test_abu_22_*` | planejado |
| THR-83 | CTL-83 | NFR-LEMB-1 | `test_nfr_lemb_1_*`, `test_ctl_83_*` | planejado |
| THR-84 | CTL-84 | NFR-LEMB-3 | `test_ctl_84_*` | planejado |
| THR-85 | CTL-85 | REQ-19.6 | `test_req_19_6_*` | planejado |
| THR-86 | CTL-86 | REQ-19.3, ABU-23 | `test_abu_23_*`, `test_prop_13_*` | planejado |
| THR-87 | CTL-87 | NFR-LEMB-2 | teste do `sw.js` em Node; `test_ctl_87_*` (nginx) | planejado |
| THR-88 | CTL-88 | — | `uv.lock`; evidência | planejado |
