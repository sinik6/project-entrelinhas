# Rastreabilidade — 011-recuperacao-de-senha

Os testes da 011 levam `[011]` na docstring. Os IDs desta mudança são únicos no projeto (histórias, ABU, PROP, CTL e THR numerados
sem repetir os das outras mudanças). Estado: implementado e testado localmente; nada visto no ar. Evidência em `validation.md`.

| ID | Descrição curta | Tarefas | Testes / evidência | Status |
|---|---|---|---|---|
| REQ-20.1 | QUANDO alguém enviar um e-mail com conta, O sistema DEVE enviar a esse e… | T-1.1, T-2.2, T-5.1, T-5.2 | `test_req_20_1_*` | ✔ em teste; não visto no ar |
| REQ-20.2 | QUANDO alguém enviar um e-mail sem conta, mal formado ou acima do limite… | T-1.1 | `test_req_20_2_*` | ✔ em teste; não visto no ar |
| REQ-20.3 | O sistema DEVE montar o link com o endereço-base de configuração e NÃO D… | T-1.1 | `test_req_20_3_*` | ✔ em teste; não visto no ar |
| REQ-20.4 | O sistema DEVE enviar o e-mail fora do pedido, de modo que o tempo de re… | T-1.1 | `test_req_20_4_*` | ✔ em teste; não visto no ar |
| REQ-20.5 | SE o envio falhar, ENTÃO O sistema DEVE registrar a falha em log sem o e… | T-1.1 | `test_req_20_5_*` | ✔ em teste; não visto no ar |
| REQ-20.6 | O sistema DEVE enviar no máximo 3 e-mails de recuperação por conta por h… | T-1.1, T-2.1, T-2.2 | `test_req_20_6_*` | ✔ em teste; não visto no ar |
| REQ-21.1 | QUANDO alguém enviar uid, token válido e senha nova que atenda à polític… | T-1.2, T-2.3, T-5.1, T-5.2 | `test_req_21_1_*` | ✔ em teste; não visto no ar |
| REQ-21.2 | SE o uid ou o token forem inválidos, vencidos (mais de 1 hora) ou já usa… | T-1.2, T-2.1 | `test_req_21_2_*` | ✔ em teste; não visto no ar |
| REQ-21.3 | SE o token for válido mas a senha não atender à política, ENTÃO O sistem… | T-1.2 | `test_req_21_3_*` | ✔ em teste; não visto no ar |
| REQ-21.4 | QUANDO a senha for redefinida, O sistema DEVE enviar um e-mail de aviso … | T-1.2, T-5.2 | `test_req_21_4_*` | ✔ em teste; não visto no ar |
| REQ-21.5 | O token NÃO DEVE valer de novo depois de usado, nem depois de a senha se… | T-1.2, T-2.3 | `test_req_21_5_*` | ✔ em teste; não visto no ar |
| REQ-22.1 | QUANDO a pessoa abrir a tela de entrar, O app DEVE mostrar "Esqueci minh… | T-4.1, T-4.2 | `test_req_22_1_*` | ✔ em teste; não visto no ar |
| REQ-22.2 | QUANDO a pessoa enviar o e-mail, O app DEVE mostrar sempre a mesma confi… | T-4.1, T-4.2 | `test_req_22_2_*` | ✔ em teste; não visto no ar |
| REQ-22.3 | QUANDO a pessoa abrir o link de redefinição, O app DEVE mostrar a tela d… | T-4.1, T-4.2, T-5.1 | `test_req_22_3_*` | ✔ em teste; não visto no ar |
| REQ-22.4 | SE o link estiver inválido ou vencido, ENTÃO O app DEVE mostrar "Link in… | T-4.1, T-4.2 | `test_req_22_4_*` | ✔ em teste; não visto no ar |
| REQ-22.5 | SE o servidor recusar a senha, ENTÃO O app DEVE mostrar a mensagem em po… | T-4.1, T-4.2 | `test_req_22_5_*` | ✔ em teste; não visto no ar |
| REQ-22.6 | O app NÃO DEVE guardar o token nem a senha no armazenamento do navegador… | T-4.1, T-4.2 | `test_req_22_6_*` | ✔ em teste; não visto no ar |
| NFR-REC-1 | O sistema DEVE guardar as credenciais de e-mail só em segredos do ambien… | T-1.4, T-2.1, T-3.1, T-3.2 | `test_nfr_rec_1_*` ou `design.md` §10 | ✔ em teste; não visto no ar |
| NFR-REC-2 | O sistema DEVE aplicar toda validação no backend, com teste de API (Art.… | T-1.2, T-2.4 | `test_nfr_rec_2_*` ou `design.md` §10 | ✔ em teste; não visto no ar |
| NFR-REC-3 | O app DEVE atender WCAG 2.2 AA e funcionar sem rolagem horizontal de 360… | T-4.1, T-4.2, T-5.1 | `test_nfr_rec_3_*` ou `design.md` §10 | ✔ em teste; não visto no ar |
| NFR-REC-4 | O deploy DEVE exigir as variáveis de e-mail antes de parar a API, como f… | T-1.4, T-3.2 | `test_nfr_rec_4_*` ou `design.md` §10 | ✔ em teste; não visto no ar |
| ABU-24 | SE alguém tentar descobrir quais e-mails têm conta pelo pedido (conteúdo… | T-1.1, T-2.2, T-5.3 | `test_abu_24_*` | ✔ em teste; não visto no ar |
| ABU-25 | SE alguém pedir o link repetidas vezes para encher a caixa de e-mail de … | T-1.1, T-1.4, T-2.2, T-3.2, T-5.2 | `test_abu_25_*` | ✔ em teste; não visto no ar |
| ABU-26 | SE alguém adivinhar, reutilizar ou usar um token vencido, ou trocar o ui… | T-1.2, T-2.3, T-5.3 | `test_abu_26_*` | ✔ em teste; não visto no ar |
| ABU-27 | SE alguém mandar o cabeçalho Host ou X-Forwarded-Host de um domínio do a… | T-1.1, T-2.2 | `test_abu_27_*` | ✔ em teste; não visto no ar |
| PROP-14 | Para qualquer e-mail (existente, inexistente, com maiúsculas, com espaço… | T-1.1, T-2.2, T-5.3 | `test_prop_14_*` | ✔ em teste; não visto no ar |

Cadeia de segurança: THR → CTL → teste

| Ameaça | Controle | Requisito | Teste | Status |
|---|---|---|---|---|
| THR-91 | CTL-91 | ABU-24, REQ-20.2, REQ-20.4, PROP-14 | `test_prop_14_*`, `test_req_20_4_*`, `test_rotas_publicas` | ✔ em teste; não visto no ar |
| THR-92 | CTL-92 | ABU-27, REQ-20.3 | `test_abu_27_*`, `test_ctl_92_*` | ✔ em teste; não visto no ar |
| THR-93 | CTL-93 | ABU-26, REQ-21.2, REQ-21.5 | `test_req_21_2_*`, `test_req_21_5_*`, `test_abu_26_*` | ✔ em teste; não visto no ar |
| THR-94 | CTL-94 | ABU-25, REQ-20.6 | `test_abu_25_*`, `test_ctl_92_*` | ✔ em teste; não visto no ar |
| THR-95 | CTL-95 | REQ-21.1, REQ-21.4 | `test_req_21_1_*`, `test_req_21_4_*` | ✔ em teste; não visto no ar |
| THR-96 | CTL-96 | NFR-REC-1, NFR-REC-4 | `test_nfr_rec_1_*`, `test_nfr_rec_4_*` | ✔ em teste; não visto no ar |
| THR-97 | CTL-97 | REQ-20.5, REQ-22.6 | `test_req_20_5_*`, `recuperacao_test.dart` | ✔ em teste; não visto no ar |
