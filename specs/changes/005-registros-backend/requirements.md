---
id: 005-registros-backend
titulo: Registros diários — entrega com foto e texto, visibilidade filtrada no servidor
status: em-revisao
tamanho: P3
risco: alto
capacidades: [registros, fotos]
autor: jpjamal
criado: 2026-11-05
---

# Requisitos — Registros diários (backend)

## Contexto e objetivo
O coração do produto: cada pessoa entrega **um registro por dia**, com **foto do manuscrito e texto digitado**, e escolhe quem pode ler:
tudo (`full`), nada (`private`) ou só um trecho (`partial`). O servidor é quem filtra; texto que o autor escondeu **nunca** sai na resposta
da API (Art. 12, ADR-0002). Esta mudança é só o backend (modelo, regras, API); as telas são da 006. Risco alto: é dado sensível e a regra de
visibilidade é a mais crítica do sistema.

> **Decisões tomadas pelo agente por delegação do usuário** ("faça todas as specs faltantes, sem me perguntar nada", 2026-11-05). Entram em
> revisão no G1 e só valem depois da ratificação do dono; cada uma traz a alternativa descartada.

## Suposições
| Suposição | Status |
|---|---|
| Unidade dos offsets: **ponto de código Unicode** (o que o Python chama de caractere), contados no texto exatamente como foi enviado; o front converte de e para UTF-16 (ADR-0009) | decidida pelo agente (alternativa descartada: unidade UTF-16 do JavaScript; o Python não indexa assim e emoji quebrariam o corte) |
| O texto é guardado **como veio**, sem normalização (nem NFC): qualquer transformação deslocaria os offsets. O servidor só recusa o que não é texto válido | decidida pelo agente |
| Trecho `partial` é **um intervalo contínuo** `[inicio, fim)` em pontos de código, escolhido pelo autor | decidida pelo agente (alternativa descartada: vários trechos e seleção por linhas; mais complexidade sem pedido do dono) |
| Tamanho: o texto precisa de **pelo menos 10 caracteres** fora espaços e quebras nas pontas (para valer como entrega) e no máximo **20 000** | decidida pelo agente |
| A entrega é **atômica**: um só pedido envia texto, visibilidade, trecho e fotos. Não há rascunho no servidor (o campo `status` da origem não existe); rascunho é coisa do app | decidida pelo agente (Art. 4; o texto íntimo não fica guardado antes de a pessoa decidir) |
| **Um registro por pessoa por dia**; o dia é o do instante da entrega em `America/Sao_Paulo` | decidida pelo agente |
| Registro entregue é **imutável**: não se edita, não se apaga e a visibilidade não muda; o administrador resolve pelo Admin (o Admin não mostra o texto) | decidida pelo agente (editar depois permitiria burlar o calendário e a leitura do parceiro) |
| De **1 a 3 fotos** de manuscrito por registro, todas do próprio autor, de finalidade `manuscrito` e ainda avulsas | decidida pelo agente |
| O parceiro vê as fotos **só quando o registro é `full`**; em `partial` e `private` nenhuma foto vai (ela mostraria o texto inteiro) | decidida pelo agente |
| Registro `private` **conta como entregue** para o parceiro (ele vê a indicação de entrega, sem texto nem fotos) | decidida pelo agente (confirma o texto da origem: "Enviado, mas mantido privado pelo autor") |
| **Confiança no operador:** a pessoa que administra a VPS (uma das duas) consegue ler o banco; `private` vale na API e na interface, não contra o operador. Sem criptografia por usuário no MVP; o Admin do Django não expõe registros (ADR-0010) | decidida pelo agente (alternativa descartada: criptografia por usuário; sem recuperação de senha no MVP, uma senha esquecida apagaria o diário) |
| Um registro pertence ao **grupo** do autor no momento da entrega | decidida pelo agente |

## Métricas de sucesso
- Em nenhum teste, em nenhuma resposta, o texto fora do trecho ou o texto `private` aparece para o parceiro (PROP-6).
- Entregar um registro leva um único pedido e menos de 1 segundo, sem contar o envio das fotos.

## Glossário
| Termo | Significado |
|---|---|
| Registro | a entrega do dia de uma pessoa: texto, fotos e visibilidade |
| Visibilidade | `full` (tudo), `private` (nada), `partial` (um trecho) |
| Trecho | intervalo `[inicio, fim)` de pontos de código do texto que o parceiro pode ler |
| Texto visível | o que o parceiro pode ler: o texto todo, o trecho ou nada |
| Ponto de código | um caractere Unicode; um emoji ou uma letra com acento decomposta conta como o que a norma Unicode define |

## Papéis e autorização
| Papel | Ação | Recurso | Permitido? | Condição |
|---|---|---|---|---|
| Participante com grupo | entregar o registro do dia | registro | sim | se ainda não entregou hoje |
| Autor | ler o próprio registro | registro | sim | texto inteiro, trecho, fotos e visibilidade |
| Parceiro do grupo | ler registro | registro | sim, filtrado | só o texto visível; `private` mostra só a indicação |
| Parceiro | ver foto do manuscrito | foto | só se `full` | senão 404 |
| Participante | ler registro de outro grupo | registro | não | 404 |
| Participante | editar, apagar ou mudar a visibilidade de registro entregue | registro | não | 405 |
| Participante sem grupo | entregar | registro | não | 409 |
| Anônimo | qualquer rota | registro | não | 401 |

## Histórias e critérios de aceite

### US-8 — Entregar o registro do dia
**Como** participante, **quero** entregar meu texto com a foto e escolher quem lê, **para** cumprir o dia.

- **REQ-8.1** QUANDO um participante com grupo enviar texto, visibilidade e de 1 a 3 fotos suas, O sistema DEVE criar o registro, anexar as fotos e registrar a data e hora da entrega no servidor.
- **REQ-8.2** SE faltar foto, ou houver mais de 3, ou uma foto não for do autor, não for de manuscrito ou já estiver anexada, ENTÃO O sistema DEVE recusar com erro de validação e não criar nada.
- **REQ-8.3** SE o texto tiver menos de 10 caracteres úteis, mais de 20 000, ou caracteres de controle (exceto quebra de linha e tabulação), ENTÃO O sistema DEVE recusar com erro de validação.
- **REQ-8.4** QUANDO a visibilidade for `partial`, O sistema DEVE exigir `inicio` e `fim` com 0 ≤ inicio < fim ≤ tamanho do texto em pontos de código; SE a visibilidade for `full` ou `private`, ENTÃO O sistema DEVE recusar trecho informado.
- **REQ-8.5** SE o autor já tiver entregue um registro naquele dia, ENTÃO O sistema DEVE recusar com 409, inclusive em dois pedidos simultâneos.
- **REQ-8.6** SE o participante não pertencer a um grupo, ENTÃO O sistema DEVE recusar com 409.
- **REQ-8.7** O sistema DEVE recusar qualquer tentativa de editar, apagar ou mudar a visibilidade de um registro entregue (405).

### US-9 — Ler com a visibilidade respeitada
**Como** participante, **quero** ler os registros do grupo, **para** acompanhar a outra pessoa sem ver o que ela guardou.

- **REQ-9.1** QUANDO o autor ler o próprio registro, O sistema DEVE devolver texto inteiro, visibilidade, trecho, fotos e hora da entrega.
- **REQ-9.2** QUANDO o parceiro ler um registro `full`, O sistema DEVE devolver o texto inteiro como texto visível e as fotos.
- **REQ-9.3** QUANDO o parceiro ler um registro `partial`, O sistema DEVE devolver **apenas** o texto do trecho como texto visível, sem fotos, sem o texto fora do trecho e sem os offsets do trecho.
- **REQ-9.4** QUANDO o parceiro ler um registro `private`, O sistema DEVE devolver só a indicação de entrega, a hora e o aviso "Enviado, mas mantido privado pelo autor", sem texto e sem fotos.
- **REQ-9.5** QUANDO o parceiro pedir a foto de um registro `partial` ou `private`, O sistema DEVE responder 404; de um `full`, DEVE devolver a imagem.
- **REQ-9.6** SE o registro for de outro grupo, ENTÃO O sistema DEVE responder 404, também para a foto.
- **REQ-9.7** O texto escondido NÃO DEVE aparecer em nenhum ponto de nenhuma resposta (corpo, erro, cabeçalho, lista, mensagem de validação), em qualquer rota que devolva dado de registro.

### US-10 — Listar por mês
**Como** participante, **quero** ver os registros de um mês, **para** navegar pelo diário.

- **REQ-10.1** QUANDO o participante pedir os registros de um mês (`AAAA-MM`), O sistema DEVE devolver os registros do grupo daquele mês (dia em `America/Sao_Paulo`), do mais novo para o mais antigo, já filtrados pela visibilidade.
- **REQ-10.2** SE o mês estiver mal formado ou for futuro, ENTÃO O sistema DEVE recusar com erro de validação.
- **REQ-10.3** QUANDO o participante não tiver grupo, O sistema DEVE devolver lista vazia.

## Requisitos não funcionais
- **NFR-REG-1** O sistema DEVE concentrar a regra de visibilidade em um único ponto do código (`visivel_para`), usado por todas as rotas, de modo que nenhuma rota serialize o texto do registro por outro caminho.
- **NFR-REG-2** O sistema DEVE aplicar toda validação no backend, com teste de API (Art. 6).
- **NFR-REG-3** O sistema NÃO DEVE registrar em log texto, trecho, nome de foto nem corpo de pedido de registro (Art. 9).
- **NFR-REG-4** O Django Admin NÃO DEVE listar nem mostrar o texto dos registros.

## Dados pessoais (LGPD)
| Dado | Finalidade | Base legal | Retenção | Quem acessa |
|---|---|---|---|---|
| Texto do registro | o diário | execução do serviço | enquanto a conta existir | o autor; o parceiro só no que a visibilidade permite |
| Visibilidade e trecho | decidir o que o parceiro lê | execução do serviço | idem | o autor; o parceiro não vê o trecho (só o texto visível) |
| Data e hora da entrega | calendário e ordem | execução do serviço | idem | o autor e o parceiro |

## Casos de abuso
- **ABU-8** SE o parceiro tentar ler o texto escondido por qualquer rota (lista, detalhe, foto, mensagem de erro, ordenação, filtro), ENTÃO O sistema DEVE negar sem revelar o conteúdo nem o tamanho do texto escondido.
- **ABU-9** SE alguém tentar entregar dois registros no mesmo dia em pedidos simultâneos, ENTÃO O sistema DEVE aceitar um só.
- **ABU-10** SE alguém trocar o identificador de um registro ou de uma foto, ENTÃO O sistema DEVE responder 404 para o que não for do grupo.
- **ABU-11** SE alguém enviar `trecho` com valores absurdos (negativos, gigantes, invertidos, vazios ou que não são números inteiros), ENTÃO O sistema DEVE recusar com validação, sem erro 500.

## Propriedades de corretude
- **PROP-6** Para qualquer texto, visibilidade e trecho, tudo o que o parceiro recebe é função só do texto visível: nenhum ponto de código do texto fora do texto visível aparece na resposta serializada.
- **PROP-7** Para qualquer texto (com emoji, acentos compostos e quebras de linha) e qualquer trecho válido, o texto visível do parceiro é exatamente a fatia `[inicio, fim)` em pontos de código.

## Fora de escopo
- Telas (006), destaques e comentários (007, 008), calendário (009), lembretes (010).
- Rascunho no servidor; edição ou exclusão de registro; mudança de visibilidade; vários trechos; busca por texto; exportação.
- Criptografia por usuário (ADR-0010 registra o motivo).

## Esclarecimentos
Todas as perguntas do mapa para `registros` foram decididas pelo agente (ver Suposições): unidade dos offsets, trecho por intervalo, tamanho mínimo,
edição, mudança de visibilidade, quantidade por dia, `private` contar como entregue e confiança no operador.
