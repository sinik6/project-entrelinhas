---
id: 010-lembretes
titulo: Lembretes — app instalável (PWA) e aviso diário às 21h30 (Web Push)
status: em-revisao
tamanho: P3
risco: alto
capacidades: [lembretes]
autor: jpjamal
criado: 2026-11-05
---

# Requisitos — Lembretes (PWA e Web Push)

## Contexto e objetivo
O dono quer incentivar as duas pessoas a escrever todo dia: *"todo dia tá o horário, ele manda um alerta para as duas pessoas"*. Esta mudança entrega o **app instalável na tela inicial (PWA)** e o
**aviso diário às 21h30** por Web Push (T0502 da origem), só a quem ainda não entregou o dia. Risco alto: acrescenta um serviço novo (o disparador), uma dependência
(`pywebpush`), segredos novos (chaves VAPID) e uma rota que faz o servidor chamar endereços informados pelo usuário (risco de SSRF).

> **Decisões tomadas pelo agente por delegação do usuário** (2026-11-05); entram em revisão no G1, com a alternativa descartada.

## Suposições
| Suposição | Status |
|---|---|
| O aviso é **opt-in**: nasce desligado; a pessoa liga em Perfil → "Lembrete diário às 21h30" e o navegador pede a permissão | decidida pelo agente (alternativa descartada: ligado por padrão; permissão pedida sem contexto é negada) |
| Horário **fixo às 21h30 de `America/Sao_Paulo`** para todos (fuso por pessoa, em mudança futura) | decidida pelo agente |
| O aviso **não vai a quem já entregou o dia**; quem não entregou recebe | decidida pelo agente |
| O texto é **genérico**: "Entrelinhas — Hora de escrever o seu dia." Sem nome da outra pessoa e sem nada do diário (a notificação aparece com o celular bloqueado) | decidida pelo agente |
| Tocar na notificação abre o app na tela **Hoje** | decidida pelo agente |
| O disparador é um **serviço do compose** (`entrelinhas-lembretes`, a mesma imagem da API com outro comando), com chave de idempotência no banco para nunca enviar duas vezes no mesmo dia | decidida pelo agente (alternativa descartada: cron da VPS fora do compose; deploy e estado ficariam em dois lugares) |
| Se o serviço estiver fora do ar às 21h30 e voltar **até as 23h00**, envia atrasado; depois disso, **pula o dia** | decidida pelo agente |
| Biblioteca de envio: **`pywebpush`** (ADR-0012); chaves **VAPID** geradas pelo comando `gerar_vapid` e guardadas nos segredos do GitHub (`VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY`) mais `VAPID_ASSUNTO` (um `mailto:`) | decidida pelo agente |
| O servidor só envia a endereços de **serviços de push conhecidos** (lista fixa de domínios, só HTTPS) | decidida pelo agente |
| **iPhone:** o Web Push só funciona com o app instalado na tela inicial (iOS 16.4 ou mais novo); o app explica isso | decidida pelo agente (limitação do sistema, não do app) |
| O PWA tem manifesto completo (nome, ícones próprios, cores, escopo `/entrelinhas/`) e um service worker mínimo **só para push**, sem cache de dados (Art. 12: nada de conteúdo guardado no aparelho) | decidida pelo agente |
| No máximo **5 aparelhos** por pessoa | decidida pelo agente |

## Métricas de sucesso
- A pessoa liga o lembrete em até 3 toques e recebe o aviso do dia às 21h30, uma vez só.
- Quem já entregou o dia não recebe nada.

## Glossário
| Termo | Significado |
|---|---|
| PWA | o app instalado na tela inicial, abrindo sem a barra do navegador |
| Web Push | aviso enviado pelo serviço de push do navegador (Google, Mozilla, Apple), mesmo com o app fechado |
| Assinatura | endereço e chaves de um aparelho que aceitou receber avisos |
| VAPID | par de chaves que prova ao serviço de push que o aviso vem deste servidor |
| Disparador | o serviço que, no horário, envia os avisos |

## Papéis e autorização
| Papel | Ação | Recurso | Permitido? | Condição |
|---|---|---|---|---|
| Participante | ligar ou desligar o lembrete do próprio aparelho | assinatura | sim | só a própria |
| Participante | ver a chave pública VAPID | chave | sim | autenticado |
| Disparador (sistema) | enviar o aviso | assinatura | sim | só às 21h30 e só a quem não entregou |
| Anônimo | qualquer rota | lembretes | não | 401 |
| Participante | mexer em assinatura de outra pessoa | assinatura | não | 404 |

## Histórias e critérios de aceite

### US-18 — App instalável e assinatura
**Como** participante, **quero** instalar o app e ligar o lembrete, **para** ser avisado todo dia.

- **REQ-18.1** O app DEVE ter manifesto válido (nome, nome curto, ícones de 192 e 512 px e máscara, cores, `start_url` e escopo dentro de `/entrelinhas/`) para ser instalável.
- **REQ-18.2** QUANDO o participante ligar o lembrete em Perfil e permitir notificações, O app DEVE registrar o service worker, assinar o push com a chave pública do servidor e enviar a assinatura ao servidor.
- **REQ-18.3** QUANDO o servidor receber uma assinatura válida, O sistema DEVE guardá-la para o participante e responder 201; reenviar a mesma assinatura DEVE ser aceito sem duplicar, e uma assinatura já ligada a outra conta passa para a conta atual.
- **REQ-18.4** SE o endereço da assinatura não for HTTPS de um serviço de push da lista permitida, ou as chaves forem inválidas, ENTÃO O sistema DEVE recusar com erro de validação, sem fazer nenhuma chamada a esse endereço.
- **REQ-18.5** SE a pessoa já tiver 5 assinaturas, ENTÃO O sistema DEVE recusar com 409.
- **REQ-18.6** QUANDO o participante desligar o lembrete, O app DEVE cancelar a assinatura no navegador e o servidor DEVE removê-la.
- **REQ-18.7** SE a permissão for negada ou o navegador não suportar push, ENTÃO O app DEVE explicar em português o que fazer (no iPhone, instalar na tela inicial) e deixar o botão desligado.
- **REQ-18.8** O app DEVE mostrar o estado do lembrete (ligado neste aparelho, desligado, bloqueado pelo navegador).

### US-19 — Aviso diário
**Como** participante, **quero** receber o aviso às 21h30 se ainda não escrevi, **para** não esquecer.

- **REQ-19.1** QUANDO der 21h30 em `America/Sao_Paulo`, O disparador DEVE enviar o aviso a cada assinatura de quem ainda não entregou o registro do dia.
- **REQ-19.2** O disparador NÃO DEVE enviar a quem já entregou o dia.
- **REQ-19.3** O disparador NÃO DEVE enviar mais de um aviso por pessoa por dia, mesmo reiniciado ou rodando em dois processos.
- **REQ-19.4** SE o serviço push responder que a assinatura não existe mais (404 ou 410), ENTÃO O disparador DEVE removê-la.
- **REQ-19.5** SE o disparador estiver fora do ar às 21h30 e voltar até as 23h00, ENTÃO DEVE enviar os avisos pendentes do dia; depois das 23h00 DEVE pular o dia.
- **REQ-19.6** O aviso DEVE trazer só o texto genérico e o endereço da tela Hoje; NÃO DEVE trazer nome, texto de registro nem informação do parceiro.
- **REQ-19.7** QUANDO o participante tocar na notificação, O service worker DEVE abrir (ou focar) o app na tela Hoje.
- **REQ-19.8** SE o envio a um aparelho falhar por outro motivo (rede, 5xx), ENTÃO O disparador DEVE registrar a falha sem texto sensível, seguir com os demais e não repetir no mesmo dia.

## Requisitos não funcionais
- **NFR-LEMB-1** O sistema DEVE guardar as chaves VAPID só em segredos do ambiente, nunca em git, log ou resposta; só a chave pública sai pela API.
- **NFR-LEMB-2** O service worker NÃO DEVE guardar em cache dados da API nem do diário (só reage a push e a toque na notificação).
- **NFR-LEMB-3** O disparador DEVE ter verificação de saúde e reiniciar sozinho (`restart: unless-stopped`).
- **NFR-LEMB-4** O app DEVE atender WCAG 2.2 AA na tela do lembrete e funcionar sem rolagem horizontal de 360 px a 1280 px.
- **NFR-LEMB-5** O sistema DEVE aplicar toda validação no backend, com teste de API (Art. 6).

## Dados pessoais (LGPD)
| Dado | Finalidade | Base legal | Retenção | Quem acessa |
|---|---|---|---|---|
| Assinatura de push (endereço e chaves) | entregar o aviso ao aparelho | consentimento (a pessoa liga) | até desligar, expirar (404/410) ou apagar a conta | só o sistema |
| Registro de envio do dia (pessoa, data) | não enviar duas vezes | execução do serviço | 30 dias | só o sistema |

## Casos de abuso
- **ABU-21** SE alguém enviar como assinatura um endereço interno ou de terceiros (para o servidor chamá-lo), ENTÃO O sistema DEVE recusar sem chamá-lo (SSRF).
- **ABU-22** SE alguém tentar remover ou ler a assinatura de outra pessoa, ENTÃO O sistema DEVE responder 404.
- **ABU-23** SE o disparador for iniciado duas vezes, ou reiniciado no meio do envio, ENTÃO O sistema NÃO DEVE duplicar avisos.

## Propriedades de corretude
- **PROP-13** Para qualquer conjunto de pessoas, assinaturas, entregas e instantes (antes de 21h30, entre 21h30 e 23h00, depois), o conjunto de avisos enviados é exatamente o definido pelas regras REQ-19.1, 19.2, 19.5, sem repetição entre execuções.

## Fora de escopo
Aviso de "escreveram juntos", de comentário novo ou de atraso do parceiro; horário por pessoa; mais de um horário; e-mail ou SMS; app nativo; cache offline do app (Art. 12: o service worker não guarda dados).

## Esclarecimentos
Decididos pelo agente (ver Suposições): opt-in, texto genérico, serviço próprio no compose, janela de atraso, lista de serviços de push, limite de aparelhos.
