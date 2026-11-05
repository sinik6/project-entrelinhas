---
id: 011-recuperacao-de-senha
titulo: Recuperação de senha por e-mail
status: em-revisao
tamanho: P2
risco: alto
capacidades: [acesso-espaco]
autor: jpjamal
criado: 2026-11-05
---

# Requisitos — Recuperação de senha por e-mail

## Contexto e objetivo
Pedido do usuário em 2026-11-03: recuperação de senha **por e-mail**, como mudança própria depois da 003. Hoje, quem esquece a senha depende do administrador (o Admin) para redefini-la.
Esta mudança deixa a pessoa pedir um **link de redefinição** no e-mail cadastrado e escolher uma senha nova, sem revelar a ninguém se um e-mail tem conta. Mexe em autenticação,
envia e-mail e cria rotas públicas novas: risco alto.

> **Decisões tomadas pelo agente por delegação do usuário** (2026-11-05); entram em revisão no G1, com a alternativa descartada.

## Suposições
| Suposição | Status |
|---|---|
| O e-mail sai por **SMTP** com o `EmailMessage` do Django (sem pacote novo), configurado por variáveis (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`); **o usuário precisa escolher o provedor e criar as credenciais** (recomendação inicial: uma conta de e-mail dedicada com senha de app) | decidida pelo agente (alternativa descartada: serviço de e-mail transacional por API; mais uma conta e uma dependência sem necessidade para 2 pessoas) |
| O token é o **gerador de tokens de redefinição do Django** (HMAC sobre o usuário, o hash da senha e o último login), válido por **1 hora**, e deixa de valer assim que a senha muda | decidida pelo agente |
| O link vai **no fragmento** da URL (`…/entrelinhas/#/redefinir/<uid>/<token>`) e é montado com um endereço-base **de configuração** (`APP_URL_BASE`), nunca com o cabeçalho `Host` do pedido | decidida pelo agente |
| O pedido responde **sempre igual** (202, mesma mensagem), exista ou não a conta, e o e-mail é enviado **fora do pedido** (segundo plano) para o tempo de resposta não revelar nada | decidida pelo agente |
| No máximo **3 e-mails de recuperação por conta por hora** (silencioso, mesma resposta); no Traefik, o mesmo balde de **5 pedidos por minuto** por origem da 003 | decidida pelo agente |
| Ao redefinir, **todas as sessões da pessoa são encerradas** e ela **não entra sozinha**: volta à tela de entrar com a senha nova | decidida pelo agente |
| Depois de redefinir, a pessoa recebe um **e-mail de aviso** ("sua senha foi alterada") | decidida pelo agente |
| A conta do administrador/dono também usa a recuperação (o `ADMIN_EMAIL` é o e-mail da conta) | decidida pelo agente |
| A política de senha é a mesma da 002/003 (12 caracteres, sem senha comum ou só numérica) | decidida pelo agente |

## Métricas de sucesso
- A pessoa recupera o acesso em menos de 3 minutos, só com o navegador e o e-mail.
- Nenhuma resposta, em conteúdo ou em tempo, diferencia e-mail com conta de sem conta.

## Glossário
| Termo | Significado |
|---|---|
| Link de redefinição | endereço com o `uid` e o token, que leva à tela de senha nova |
| Token | valor assinado de uso único e vida curta, que prova que quem tem o link controla o e-mail |

## Papéis e autorização
| Papel | Ação | Recurso | Permitido? | Condição |
|---|---|---|---|---|
| Anônimo | pedir o link | recuperação | sim | rota pública (entra na lista de públicas) |
| Anônimo | redefinir com um token válido | senha | sim | token e `uid` válidos e dentro de 1 hora |
| Participante logado | usar a troca de senha da 003 | perfil | sim | já existente; não muda |
| Qualquer | pedir pelo e-mail de outra pessoa | recuperação | sim, sem efeito para o atacante | o link vai só ao e-mail dono da conta |

## Histórias e critérios de aceite

### US-20 — Pedir o link
**Como** pessoa que esqueceu a senha, **quero** pedir um link no meu e-mail, **para** voltar a entrar.

- **REQ-20.1** QUANDO alguém enviar um e-mail com conta, O sistema DEVE enviar a esse e-mail uma mensagem em português com o link de redefinição e responder 202.
- **REQ-20.2** QUANDO alguém enviar um e-mail sem conta, mal formado ou acima do limite por hora, O sistema DEVE responder exatamente o mesmo 202 e a mesma mensagem, sem enviar e-mail.
- **REQ-20.3** O sistema DEVE montar o link com o endereço-base de configuração e NÃO DEVE usar o cabeçalho `Host` nem qualquer dado do pedido na URL.
- **REQ-20.4** O sistema DEVE enviar o e-mail fora do pedido, de modo que o tempo de resposta seja o mesmo com e sem conta.
- **REQ-20.5** SE o envio falhar, ENTÃO O sistema DEVE registrar a falha em log sem o e-mail, o token nem o corpo da mensagem, e a resposta ao pedido DEVE permanecer a mesma.
- **REQ-20.6** O sistema DEVE enviar no máximo 3 e-mails de recuperação por conta por hora.

### US-21 — Escolher a senha nova
**Como** pessoa com o link, **quero** definir uma senha nova, **para** entrar de novo.

- **REQ-21.1** QUANDO alguém enviar `uid`, token válido e senha nova que atenda à política, O sistema DEVE gravar a senha, encerrar todas as sessões da conta e responder 204, sem abrir sessão.
- **REQ-21.2** SE o `uid` ou o token forem inválidos, vencidos (mais de 1 hora) ou já usados, ENTÃO O sistema DEVE recusar com 400 e a mesma resposta nos três casos, sem alterar nada.
- **REQ-21.3** SE o token for válido mas a senha não atender à política, ENTÃO O sistema DEVE recusar com erro de validação (422) sem alterar a senha, e o mesmo token DEVE continuar valendo até vencer.
- **REQ-21.4** QUANDO a senha for redefinida, O sistema DEVE enviar um e-mail de aviso ao endereço da conta.
- **REQ-21.5** O token NÃO DEVE valer de novo depois de usado, nem depois de a senha ser trocada por outro caminho (troca na 003 ou redefinição pelo Admin).

### US-22 — Telas
**Como** pessoa, **quero** telas simples, **para** pedir e redefinir sem confusão.

- **REQ-22.1** QUANDO a pessoa abrir a tela de entrar, O app DEVE mostrar "Esqueci minha senha", que leva à tela de pedido.
- **REQ-22.2** QUANDO a pessoa enviar o e-mail, O app DEVE mostrar sempre a mesma confirmação ("Se este e-mail tiver conta, enviamos um link. Vale por 1 hora.") e nunca dizer se o e-mail existe.
- **REQ-22.3** QUANDO a pessoa abrir o link de redefinição, O app DEVE mostrar a tela de senha nova (campo e confirmação) e, ao concluir, levar à tela de entrar com a mensagem "Senha trocada. Entre com a nova senha."
- **REQ-22.4** SE o link estiver inválido ou vencido, ENTÃO O app DEVE mostrar "Link inválido ou vencido." com o botão de pedir outro.
- **REQ-22.5** SE o servidor recusar a senha, ENTÃO O app DEVE mostrar a mensagem em português, sem detalhe técnico.
- **REQ-22.6** O app NÃO DEVE guardar o token nem a senha no armazenamento do navegador e DEVE tirar o token da barra de endereço ao abrir a tela de senha nova.

## Requisitos não funcionais
- **NFR-REC-1** O sistema DEVE guardar as credenciais de e-mail só em segredos do ambiente, nunca em git, log ou resposta.
- **NFR-REC-2** O sistema DEVE aplicar toda validação no backend, com teste de API (Art. 6).
- **NFR-REC-3** O app DEVE atender WCAG 2.2 AA e funcionar sem rolagem horizontal de 360 px a 1280 px, nos temas claro e escuro.
- **NFR-REC-4** O deploy DEVE exigir as variáveis de e-mail antes de parar a API, como faz com o administrador.

## Dados pessoais (LGPD)
| Dado | Finalidade | Base legal | Retenção | Quem acessa |
|---|---|---|---|---|
| E-mail da conta | enviar o link e o aviso | execução do serviço | enquanto a conta existir | o sistema e o provedor de e-mail (conteúdo: só o link) |
| Registro de pedidos (conta, instante) | limite de 3 por hora | legítimo interesse (segurança) | 24 horas | só o sistema |
| Token | provar o controle do e-mail | execução do serviço | 1 hora; não é guardado (derivado) | só quem recebeu o e-mail |

## Casos de abuso
- **ABU-24** SE alguém tentar descobrir quais e-mails têm conta pelo pedido (conteúdo, código, tempo, limite), ENTÃO O sistema DEVE responder do mesmo jeito.
- **ABU-25** SE alguém pedir o link repetidas vezes para encher a caixa de e-mail de outra pessoa, ENTÃO O sistema DEVE parar de enviar depois de 3 por hora por conta e o Traefik DEVE limitar a origem.
- **ABU-26** SE alguém adivinhar, reutilizar ou usar um token vencido, ou trocar o `uid`, ENTÃO O sistema DEVE recusar com a resposta única de link inválido.
- **ABU-27** SE alguém mandar o cabeçalho `Host` ou `X-Forwarded-Host` de um domínio do atacante, ENTÃO O link do e-mail DEVE continuar apontando para o endereço-base de configuração.

## Propriedades de corretude
- **PROP-14** Para qualquer e-mail (existente, inexistente, com maiúsculas, com espaços, vazio, acima do limite), a resposta do pedido é a mesma em status, corpo e cabeçalhos relevantes.

## Fora de escopo
Verificação do e-mail no cadastro; troca de e-mail da conta; passkey, biometria, segundo fator; recuperação por SMS; reabilitação de conta bloqueada (não há bloqueio).

## Esclarecimentos
Decididos pelo agente (ver Suposições): SMTP, token do Django com 1 hora, link no fragmento, resposta única, limite de 3 por hora, sem login automático, aviso por e-mail.
**Dependência do usuário:** escolher o provedor de e-mail e criar as credenciais (tarefa T-3.1).
