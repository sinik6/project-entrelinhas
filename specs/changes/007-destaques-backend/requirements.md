---
id: 007-destaques-backend
titulo: Destaques e comentários sobre o texto visível — backend
status: em-revisao
tamanho: P2
risco: alto
capacidades: [destaques]
autor: jpjamal
criado: 2026-11-05
---

# Requisitos — Destaques e comentários (backend)

## Contexto e objetivo
O parceiro (e o próprio autor) pode **selecionar um trecho do texto visível, destacá-lo e comentar**, no estilo Kindle (RF-11 da origem), e cada comentário aparece
na cor de quem o fez. As posições (`inicio`, `fim`) são validadas **contra o texto visível** (AC-11.5), nunca contra o texto escondido: um destaque não pode servir de
sonda para descobrir o que o autor guardou. Esta mudança é só o backend; as telas são da 008. Risco alto: comentário é dado sensível e a validação de posição é uma
superfície de vazamento.

> **Decisões tomadas pelo agente por delegação do usuário** (2026-11-05); entram em revisão no G1, com a alternativa descartada.

## Suposições
| Suposição | Status |
|---|---|
| Os offsets do destaque são em **pontos de código do texto visível** (ADR-0009): em `full` é o texto todo; em `partial`, o trecho; em `private` não há destaque | decidida pelo agente (alternativa descartada: offsets no texto integral; mesmo o autor, com offsets diferentes dos do parceiro, causaria confusão e vazaria posições) |
| Quem pode destacar: **qualquer membro do grupo que enxergue o texto visível**, inclusive o autor no próprio registro, mas só dentro do texto visível | decidida pelo agente |
| O destaque pode existir **sem comentário** (grifo puro) e receber comentários depois | decidida pelo agente |
| Cada destaque tem uma **conversa curta**: comentários de qualquer um dos dois, de 1 a 1000 caracteres, no máximo 20 por destaque | decidida pelo agente |
| **Apagar:** o destaque, só quem o criou (apaga também os comentários dele, e o app avisa); o comentário, só quem o escreveu. **Editar:** o comentário, só quem o escreveu; o destaque não se edita (apaga e cria outro) | decidida pelo agente |
| Limite de **50 destaques por pessoa por registro** | decidida pelo agente |
| O texto destacado **não é guardado**: é calculado do texto visível pelas posições (sem cópia do texto íntimo) | decidida pelo agente (a origem guardava `highlighted_text`; descartado por duplicar dado sensível) |
| Destaques se **sobrepõem** livremente | decidida pelo agente |
| A cor mostrada é a do perfil de quem destacou ou comentou, lida na hora | decidida pelo agente |

## Métricas de sucesso
- Nenhum teste consegue, por posição, tamanho ou mensagem de erro, descobrir algo do texto escondido.

## Glossário
| Termo | Significado |
|---|---|
| Destaque | intervalo `[inicio, fim)` do texto visível, marcado por alguém do grupo |
| Comentário | nota de texto presa a um destaque, na cor de quem escreveu |
| Texto visível | o que o parceiro pode ler (005): todo, o trecho ou nada |

## Papéis e autorização
| Papel | Ação | Recurso | Permitido? | Condição |
|---|---|---|---|---|
| Membro do grupo | listar destaques e comentários | registro do grupo | sim | só de registro com texto visível (`full` ou `partial`) |
| Membro do grupo | criar destaque ou comentário | registro do grupo | sim | dentro do texto visível e dos limites |
| Autor do destaque | apagar destaque | destaque | sim | só o seu |
| Autor do comentário | editar ou apagar comentário | comentário | sim | só o seu |
| Qualquer um | mexer no destaque ou comentário de outro | destaque, comentário | não | 403 só se o recurso for visível ao grupo; de outro grupo, 404 |
| Registro `private` | destacar ou listar | registro | não | 409 "sem texto visível" |
| Anônimo | qualquer rota | destaque | não | 401 |

## Histórias e critérios de aceite

### US-13 — Destacar
**Como** membro do grupo, **quero** destacar um trecho do texto visível, **para** marcar o que me tocou.

- **REQ-13.1** QUANDO um membro do grupo enviar `inicio` e `fim` válidos para um registro com texto visível, O sistema DEVE criar o destaque e devolvê-lo com o trecho destacado, calculado do texto visível.
- **REQ-13.2** SE `inicio` e `fim` não forem inteiros com 0 ≤ inicio < fim ≤ tamanho do texto visível em pontos de código, ENTÃO O sistema DEVE recusar com erro de validação cuja mensagem não informe o tamanho do texto completo.
- **REQ-13.3** SE o registro for `private` (para o parceiro e para o autor), ENTÃO O sistema DEVE recusar criar e listar destaques com 409.
- **REQ-13.4** QUANDO um destaque for criado com um comentário, O sistema DEVE guardar o comentário junto.
- **REQ-13.5** SE a pessoa já tiver 50 destaques no registro, ENTÃO O sistema DEVE recusar com 409, também em pedidos simultâneos.
- **REQ-13.6** QUANDO o autor do destaque o apagar, O sistema DEVE apagar também os comentários dele.
- **REQ-13.7** SE outra pessoa tentar apagar um destaque que não criou, ENTÃO O sistema DEVE recusar com 403.

### US-14 — Comentar e ler
**Como** membro do grupo, **quero** comentar um destaque e ver os comentários, **para** conversar sobre o texto.

- **REQ-14.1** QUANDO um membro do grupo comentar um destaque, O sistema DEVE guardar o comentário com autor e hora, dentro de 1 a 1000 caracteres úteis e sem caracteres de controle (exceto quebra de linha e tabulação).
- **REQ-14.2** SE o destaque já tiver 20 comentários, ENTÃO O sistema DEVE recusar com 409.
- **REQ-14.3** QUANDO o autor do comentário o editar, O sistema DEVE gravar o novo texto e a hora da edição; SE outra pessoa tentar editar ou apagar, ENTÃO O sistema DEVE recusar com 403.
- **REQ-14.4** QUANDO o autor do comentário o apagar, O sistema DEVE removê-lo.
- **REQ-14.5** QUANDO um membro listar os destaques de um registro, O sistema DEVE devolver cada destaque com posição, trecho destacado, autor (nome e cor), comentários (com autor e cor) e se é dele.
- **REQ-14.6** SE o registro, o destaque ou o comentário for de outro grupo, ENTÃO O sistema DEVE responder 404.
- **REQ-14.7** O texto de comentário ou do trecho destacado NÃO DEVE aparecer em log nem em mensagem de erro.

## Requisitos não funcionais
- **NFR-DEST-1** O sistema DEVE aplicar toda validação no backend, com teste de API (Art. 6).
- **NFR-DEST-2** O Django Admin NÃO DEVE mostrar destaques nem comentários.

## Dados pessoais (LGPD)
| Dado | Finalidade | Base legal | Retenção | Quem acessa |
|---|---|---|---|---|
| Posição do destaque | marcar o trecho | execução do serviço | enquanto o registro existir | o grupo |
| Texto do comentário | conversar sobre o texto | execução do serviço | até o autor apagar | o grupo |
| Autor e hora | mostrar quem e quando | execução do serviço | idem | o grupo |

## Casos de abuso
- **ABU-14** SE o parceiro tentar descobrir o texto escondido ou o tamanho dele por posições fora do visível, mensagens de erro ou listas, ENTÃO O sistema DEVE negar sem revelar nada além do texto visível.
- **ABU-15** SE alguém criar destaques ou comentários em volume (pedidos simultâneos), ENTÃO O sistema DEVE respeitar os limites de 50 e 20.
- **ABU-16** SE alguém tentar editar ou apagar o comentário ou o destaque de outra pessoa, ENTÃO O sistema DEVE recusar sem alterar nada.

## Propriedades de corretude
- **PROP-9** Para qualquer registro, visibilidade e posição válida, o trecho destacado devolvido é exatamente `texto_visivel[inicio:fim]` e nunca contém ponto de código fora do texto visível.

## Fora de escopo
Telas (008); notificação de comentário novo (lembretes não avisam comentário); menção, reação, resposta encadeada; edição do destaque; destaque sobre `private`.

## Esclarecimentos
Decididos pelo agente (ver Suposições): referência ao texto visível, autor pode destacar o próprio texto, quem edita e apaga.
