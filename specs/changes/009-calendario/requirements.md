---
id: 009-calendario
titulo: Calendário — dia escrito, dia que falhou e "escreveram juntos"
status: em-revisao
tamanho: P2
risco: medio
capacidades: [calendario]
autor: jpjamal
criado: 2026-11-05
---

# Requisitos — Calendário (backend e telas)

## Contexto e objetivo
Da visão do dono (2026-11-03): *"no calendário vai aparecer o dia que cada um escreveu, o dia que cada um falhou, e quando os dois escreveram num intervalo de 2 horas, ele vai
aparecer informando que os dois escreveram juntos, meio que para incentivar um ao outro."* Esta mudança entrega isso: uma rota que **deriva** o estado de cada dia dos registros
(005) e uma tela de calendário. Não guarda nada novo sobre os registros; só acrescenta a data em que cada pessoa entrou no grupo, para não contar como falha o que veio antes dela.
Risco médio: erro de dia na virada da meia-noite desmotiva e corrói a confiança no hábito.

> **Decisões tomadas pelo agente por delegação do usuário** (2026-11-05); entram em revisão no G1, com a alternativa descartada.

## Suposições
| Suposição | Status |
|---|---|
| **"Falhou"**: o dia terminou (meia-noite de `America/Sao_Paulo`) sem entrega daquela pessoa. Hoje, sem entrega, é **pendente**, não falha | decidida pelo agente (alternativa descartada: falhar às 21h30, no horário do lembrete; punitivo e dependente do lembrete) |
| **"Escreveram juntos"**: os dois entregaram no **mesmo dia** e a diferença entre os horários de entrega é de **até 2 horas** (inclusive) | decidida pelo agente (entre horários de entrega, como a visão dá a entender; alternativa descartada: janela fixa de 2 horas no relógio) |
| Registro **`private` conta como escreveu** para o calendário do parceiro: ele só vê que houve entrega, sem texto | decidida pelo agente (coerente com a 005: a indicação de entrega já é visível) |
| O **fuso é `America/Sao_Paulo` para todos** (como na 003); fuso por pessoa fica para uma mudança futura, junto com o lembrete | decidida pelo agente |
| Dia **antes de a pessoa entrar no grupo** não conta (estado `fora`); a data de entrada é guardada no perfil (`entrou_em`); contas existentes recebem a data de criação da conta | decidida pelo agente |
| A API **não devolve horários** de entrega, só o estado do dia e se escreveram juntos (mínimo necessário) | decidida pelo agente |
| Sem sequências, pontos, conquistas nem ranking (não foram pedidos) | decidida pelo agente |
| Navegação por mês, do mês de entrada do grupo até o atual | decidida pelo agente |
| Sem pacote novo: a grade do mês é desenhada com widgets do Flutter | decidida pelo agente |

## Métricas de sucesso
- O estado de cada dia bate com os registros em 100% dos casos de teste, inclusive às 23h59 e às 00:01 de São Paulo.
- O calendário do mês abre em menos de 1 segundo.

## Glossário
| Termo | Significado |
|---|---|
| Escreveu | a pessoa entregou um registro naquele dia (qualquer visibilidade) |
| Falhou | o dia passou sem entrega daquela pessoa, desde que ela já estivesse no grupo |
| Pendente | hoje, ainda sem entrega |
| Fora | dia anterior à entrada da pessoa no grupo |
| Juntos | os dois entregaram no mesmo dia com até 2 horas de diferença |

## Papéis e autorização
| Papel | Ação | Recurso | Permitido? | Condição |
|---|---|---|---|---|
| Membro do grupo | ver o calendário do grupo | calendário | sim | só do próprio grupo |
| Participante sem grupo | ver | calendário | sim, vazio | |
| Anônimo | qualquer | calendário | não | 401 |

## Histórias e critérios de aceite

### US-16 — Estado dos dias
**Como** membro do grupo, **quero** saber como cada um foi em cada dia, **para** manter o hábito juntos.

- **REQ-16.1** QUANDO o membro pedir o calendário de um mês (`AAAA-MM`), O sistema DEVE devolver os dias do mês até hoje (dia em `America/Sao_Paulo`) com o estado de cada membro: `escreveu`, `falhou`, `pendente` ou `fora`.
- **REQ-16.2** O sistema DEVE marcar `escreveu` quando houver registro da pessoa naquele dia, seja qual for a visibilidade.
- **REQ-16.3** O sistema DEVE marcar `falhou` quando o dia já terminou sem registro da pessoa e ela já estava no grupo naquele dia; DEVE marcar `pendente` no dia de hoje sem registro; DEVE marcar `fora` nos dias anteriores à entrada dela.
- **REQ-16.4** O sistema DEVE marcar `juntos` no dia em que os dois membros entregaram com até 2 horas (7200 s, inclusive) de diferença entre os horários de entrega.
- **REQ-16.5** SE os dois entregaram no mesmo dia com mais de 2 horas de diferença, ou só um entregou, ENTÃO O sistema NÃO DEVE marcar `juntos`.
- **REQ-16.6** O sistema DEVE devolver, para cada membro, nome e cor, e NÃO DEVE devolver horários de entrega, texto, visibilidade nem e-mail.
- **REQ-16.7** SE o mês estiver mal formado, for futuro ou anterior ao mês de entrada do grupo, ENTÃO O sistema DEVE recusar com erro de validação.
- **REQ-16.8** QUANDO o participante não tiver grupo, O sistema DEVE devolver o calendário vazio.
- **REQ-16.9** O estado de um dia DEVE depender só dos registros e da data de entrada, de modo que uma mesma entrega nunca mude de dia por causa do horário do servidor (a virada é a da meia-noite de São Paulo).

### US-17 — Tela de calendário
**Como** membro, **quero** ver o mês numa grade, **para** enxergar o hábito de relance.

- **REQ-17.1** QUANDO o membro abrir o Calendário, O app DEVE mostrar a grade do mês atual, com navegação ao mês anterior e de volta, limitada ao mês de entrada do grupo e ao mês atual.
- **REQ-17.2** O app DEVE mostrar, em cada dia, um marcador por membro na cor dele: preenchido (escreveu), vazado com "×" (falhou), tracejado (pendente), nada (fora), mais um selo "juntos" quando for o caso.
- **REQ-17.3** O app NÃO DEVE depender só da cor: cada estado tem forma própria e texto alternativo ("Dia 12: Ana escreveu; Bia não escreveu; escreveram juntos").
- **REQ-17.4** QUANDO o membro tocar num dia, O app DEVE abrir a lista dos registros daquele dia, na visão de quem pede (a mesma da 006), ou "Nenhum registro neste dia".
- **REQ-17.5** O app DEVE mostrar uma legenda dos marcadores.
- **REQ-17.6** SE o servidor recusar um pedido ou a sessão tiver acabado, ENTÃO O app DEVE mostrar a mensagem em português ou levar à tela de entrar.

## Requisitos não funcionais
- **NFR-CAL-1** O app DEVE atender WCAG 2.2 AA e funcionar sem rolagem horizontal de 360 px a 1280 px, nos temas claro e escuro, com toda ação alcançável pelo teclado.
- **NFR-CAL-2** O sistema DEVE aplicar toda validação no backend, com teste de API (Art. 6).
- **NFR-CAL-3** A rota DEVE responder com no máximo 3 consultas ao banco, independente do mês.

## Dados pessoais (LGPD)
| Dado | Finalidade | Base legal | Retenção | Quem acessa |
|---|---|---|---|---|
| Data de entrada no grupo (`entrou_em`) | não contar falha antes da entrada | execução do serviço | enquanto a conta existir | só o sistema |
| Estado do dia (derivado) | calendário | execução do serviço | derivado, não guardado | o grupo |

## Casos de abuso
- **ABU-19** SE alguém pedir o calendário de outro grupo ou de meses fora do intervalo, ENTÃO O sistema DEVE devolver só o do próprio grupo ou recusar com validação.
- **ABU-20** SE a entrega acontecer perto da meia-noite de São Paulo (23h59, 00:00, 00:01, mudança de horário de verão), ENTÃO O sistema DEVE atribuí-la ao dia certo.

## Propriedades de corretude
- **PROP-11** Para qualquer conjunto de entregas, o estado de cada dia é o mesmo calculado por um oráculo independente (definição direta das regras REQ-16.2 a 16.5).
- **PROP-12** `juntos` é simétrico (não depende de quem entregou primeiro) e nunca é verdadeiro sem os dois membros em `escreveu`.

## Fora de escopo
Horário do lembrete (010); fuso por pessoa; sequência de dias, pontos, ranking; exportar; calendário de mais de um grupo; push de "escreveram juntos".

## Esclarecimentos
Decididos pelo agente (ver Suposições): definição de falha e de "juntos", `private` conta como escreveu, fuso fixo.
