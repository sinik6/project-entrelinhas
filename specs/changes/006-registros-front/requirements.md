---
id: 006-registros-front
titulo: Registros diários — telas de escrita e leitura
status: em-revisao
tamanho: P2
risco: medio
capacidades: [registros]
autor: jpjamal
criado: 2026-11-05
---

# Requisitos — Registros diários (telas)

## Contexto e objetivo
Com o backend da 005 no ar, as duas pessoas precisam **escrever o dia (texto + foto + quem lê) e ler o diário** pelo app. O risco está no front: escolher o
trecho `partial` com os offsets certos (o que o parceiro lerá), não perder nem gravar no aparelho o texto íntimo e não permitir uma entrega irreversível por
engano. Sem API nova; usa a 004 e a 005.

> **Decisões tomadas pelo agente por delegação do usuário** (2026-11-05); entram em revisão no G1, com a alternativa descartada.

## Suposições
| Suposição | Status |
|---|---|
| A navegação inferior passa a ter **Hoje · Diário · Grupo · Perfil** (a 009 acrescenta Calendário) | decidida pelo agente |
| **Não há escolha padrão de visibilidade**: a pessoa precisa escolher e só então pode entregar | decidida pelo agente (alternativa descartada: padrão `private`/`full`; um padrão errado é vazamento ou entrega vazia) |
| O trecho `partial` é escolhido **selecionando o texto no próprio campo** e tocando "Usar a seleção"; a tela mostra a **prévia exata** do que a outra pessoa lerá | decidida pelo agente |
| O rascunho vive **só na memória do app** (some ao recarregar); nada do texto vai para o armazenamento do navegador | decidida pelo agente (texto íntimo em aparelho compartilhado; alternativa descartada: `localStorage`) |
| A entrega pede **confirmação** ("depois de entregar não dá para editar") | decidida pelo agente |
| A conversão de posições UTF-16 (Dart) para pontos de código (API) fica numa função compartilhada e testada; a seleção é ajustada a limites de grafema com o pacote `characters` (ADR-0011) | decidida pelo agente |
| Fotos: escolha de 1 a 3 pelo `image_picker` (ADR-0008); visualizador em tela cheia com zoom | decidida pelo agente |

## Métricas de sucesso
- Escrever, fotografar e entregar leva menos de 2 minutos no celular, sem rolagem horizontal.
- Nenhum teste encontra, na prévia ou na leitura do parceiro, um caractere fora do trecho escolhido.

## Glossário
| Termo | Significado |
|---|---|
| Hoje | tela de escrita do dia, ou do registro já entregue |
| Diário | lista dos registros do grupo, por mês |
| Prévia | o texto exato que a outra pessoa lerá, mostrado antes de entregar |

## Papéis e autorização
| Papel | Ação | Recurso | Permitido? | Condição |
|---|---|---|---|---|
| Participante com grupo | escrever e entregar | tela Hoje | sim | uma vez por dia |
| Participante sem grupo | abrir Hoje ou Diário | telas | não | o app leva ao Grupo |
| Participante | ler o diário | tela Diário | sim | o que a API devolver para ele |

## Histórias e critérios de aceite

### US-11 — Escrever e entregar
**Como** participante, **quero** escrever, fotografar e escolher quem lê, **para** entregar o dia.

- **REQ-11.1** QUANDO o participante com grupo abrir Hoje sem ter entregue, O app DEVE mostrar o campo de texto, a escolha de 1 a 3 fotos e a escolha de visibilidade (todo o grupo lê, só eu, só um trecho), sem nenhuma opção marcada.
- **REQ-11.2** ENQUANTO faltar texto com 10 caracteres úteis, ou foto, ou visibilidade, ou (em "só um trecho") o trecho, O app DEVE manter o botão Entregar desabilitado e dizer o que falta.
- **REQ-11.3** QUANDO o participante escolher "só um trecho", selecionar parte do texto e tocar "Usar a seleção", O app DEVE mostrar a prévia com o texto exato que a outra pessoa lerá e marcar o trecho no campo.
- **REQ-11.4** O app DEVE enviar o trecho em pontos de código, convertendo da posição UTF-16 do campo e ajustando a seleção para dentro, até os limites de grafema (nunca para fora).
- **REQ-11.5** QUANDO o participante tocar em Entregar, O app DEVE pedir confirmação com o resumo (quem lê, quantas fotos) e o aviso de que o registro não pode ser editado nem apagado.
- **REQ-11.6** QUANDO o participante confirmar, O app DEVE enviar as fotos, depois o registro, e mostrar "Registro entregue" e o registro do dia.
- **REQ-11.7** SE o envio de uma foto ou do registro falhar, ENTÃO O app DEVE mostrar a mensagem em português, manter o texto e as escolhas, e permitir tentar de novo sem reenviar as fotos que já subiram.
- **REQ-11.8** SE o servidor responder que o dia já foi entregue, ENTÃO O app DEVE mostrar o registro de hoje e a mensagem.
- **REQ-11.9** O app NÃO DEVE gravar o texto, o trecho nem as fotos no armazenamento do navegador ou do aparelho.

### US-12 — Ler o diário
**Como** participante, **quero** ler os registros do grupo, **para** acompanhar a outra pessoa e rever os meus.

- **REQ-12.1** QUANDO o participante abrir o Diário, O app DEVE mostrar os registros do mês atual do mais novo para o mais antigo e permitir ir ao mês anterior e voltar, sem passar do mês atual.
- **REQ-12.2** O app DEVE mostrar, em cada registro, nome e cor de quem escreveu, o dia e a hora da entrega.
- **REQ-12.3** QUANDO o registro for da outra pessoa, O app DEVE mostrar o texto visível e as fotos que a API devolver; em trecho, a nota "Mostrando só o trecho que {nome} escolheu"; em privado, "Enviado, mas mantido privado pelo autor".
- **REQ-12.4** QUANDO o registro for do próprio participante, O app DEVE mostrar o texto inteiro, marcar o trecho escolhido e dizer quem pode ler.
- **REQ-12.5** QUANDO o participante tocar numa foto, O app DEVE abri-la em tela cheia com zoom, com texto alternativo ("Foto do manuscrito de {nome}").
- **REQ-12.6** SE não houver registro no mês, ENTÃO O app DEVE mostrar a mensagem "Nenhum registro neste mês."
- **REQ-12.7** SE o servidor recusar um pedido ou a sessão tiver acabado, ENTÃO O app DEVE mostrar a mensagem em português ou levar à tela de entrar, sem detalhe técnico.

## Requisitos não funcionais
- **NFR-TELA-1** O app DEVE atender WCAG 2.2 AA e funcionar sem rolagem horizontal de 360 px a 1280 px, nos temas claro e escuro.
- **NFR-TELA-2** O app NÃO DEVE interpretar o texto de registro como HTML nem como marcação; só o desenha como texto.
- **NFR-TELA-3** O app DEVE funcionar com o teclado: toda ação alcançável sem mouse.

## Dados pessoais (LGPD)
Sem dado novo. O texto e as fotos são tratados como na 005; o app só os mostra e não os guarda (REQ-11.9).

## Casos de abuso
- **ABU-12** SE a pessoa tocar duas vezes em Entregar (ou o clique repetir por rede lenta), ENTÃO O app DEVE enviar um único pedido de registro.
- **ABU-13** SE um texto de registro contiver marcação (`<script>`, `<b>`, `&lt;`), ENTÃO O app DEVE mostrá-lo literalmente, como texto.

## Propriedades de corretude
- **PROP-8** Para qualquer texto (emoji, acento composto, quebra de linha, bandeira) e qualquer seleção, converter para pontos de código e voltar devolve a mesma posição, e o trecho enviado, fatiado em pontos de código, é igual ao texto da prévia.

## Fora de escopo
Destaques e comentários (008); calendário (009); lembretes (010); edição, exclusão e rascunho persistente; compartilhar ou exportar texto.

## Esclarecimentos
Decididos pelo agente (ver Suposições): sem visibilidade padrão, prévia exata, rascunho só em memória, confirmação, grafemas.
