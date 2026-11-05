---
id: 008-destaques-front
titulo: Destaques e comentários — telas (estilo Kindle)
status: em-revisao
tamanho: P2
risco: medio
capacidades: [destaques]
autor: jpjamal
criado: 2026-11-05
---

# Requisitos — Destaques e comentários (telas)

## Contexto e objetivo
Na leitura de um registro, a pessoa **seleciona um trecho, destaca e comenta**; os trechos destacados aparecem marcados na cor de quem os fez, e tocar neles abre os
comentários (AC-11.1 a 11.4 da origem). Sem API nova: usa a 007 e o texto visível da 005/006. O risco médio está em desenhar o destaque sobre o texto com as
posições certas (UTF-16 ↔ pontos de código, ADR-0009) e em manter a leitura acessível (cor sozinha não pode carregar a informação).

> **Decisões tomadas pelo agente por delegação do usuário** (2026-11-05); entram em revisão no G1, com a alternativa descartada.

## Suposições
| Suposição | Status |
|---|---|
| Selecionar texto na leitura abre uma barra com "Destacar" e "Destacar e comentar" (celular: pressão longa; computador: arrastar) | decidida pelo agente |
| O destaque é desenhado como **fundo na cor de quem destacou com transparência**, mais **sublinhado** do mesmo tom (a cor sozinha não basta; WCAG 1.4.1) | decidida pelo agente |
| Tocar (ou clicar) num trecho destacado abre uma **folha de comentários**: lista da conversa, campo para comentar, "Apagar destaque" para quem o criou | decidida pelo agente (alternativa descartada: popover só no hover; não existe hover no celular) |
| Onde dois destaques se sobrepõem, o toque abre o **mais curto**; um seletor lista os demais no topo da folha | decidida pelo agente |
| A tela usa **o texto visível** e as posições dele (ADR-0009); em `partial` e em `full` do parceiro, o que veio da API; no registro do próprio autor, o texto visível é o trecho ou o texto todo, e o resto do texto aparece sem destaque possível | decidida pelo agente |
| Sem pacote novo (usa `characters` do ADR-0011) | decidida pelo agente |

## Métricas de sucesso
- Destacar e comentar um trecho leva até 4 toques no celular.
- Um destaque cai exatamente no trecho selecionado, inclusive com emoji.

## Glossário
| Termo | Significado |
|---|---|
| Folha de comentários | painel que sobe da base (celular) ou abre ao lado (computador) com a conversa do destaque |
| Texto visível | o que a pessoa pode ler daquele registro |

## Papéis e autorização
| Papel | Ação | Recurso | Permitido? | Condição |
|---|---|---|---|---|
| Membro do grupo | destacar, comentar, ver | registro com texto visível | sim | o que a API 007 permitir |
| Autor do destaque ou do comentário | apagar, editar o comentário | destaque, comentário | sim | só o seu |
| Registro `private` | destacar | tela | não | o app não oferece a ação |

## Histórias e critérios de aceite

### US-15 — Destacar e comentar na leitura
**Como** membro do grupo, **quero** destacar e comentar um trecho, **para** conversar sobre o texto.

- **REQ-15.1** QUANDO o membro selecionar texto num registro com texto visível, O app DEVE oferecer "Destacar" e "Destacar e comentar" apenas se a seleção estiver dentro do texto visível.
- **REQ-15.2** QUANDO o membro confirmar o destaque, O app DEVE enviar posições em pontos de código (convertidas da seleção UTF-16 e ajustadas para dentro a limites de grafema) e mostrar o trecho marcado.
- **REQ-15.3** O app DEVE desenhar cada destaque com fundo translúcido na cor de quem o fez e sublinhado, e o texto sobre o fundo DEVE manter contraste de pelo menos 4,5 para 1.
- **REQ-15.4** QUANDO o membro tocar num trecho destacado, O app DEVE abrir a folha com os comentários (autor com nome e cor, hora, texto), o campo para comentar e, para o autor do destaque, "Apagar destaque".
- **REQ-15.5** QUANDO o membro comentar, editar o próprio comentário ou apagar o próprio comentário, O app DEVE refletir o resultado na folha.
- **REQ-15.6** QUANDO o autor apagar o destaque, O app DEVE avisar que os comentários também serão apagados e pedir confirmação.
- **REQ-15.7** SE dois destaques se sobrepuserem no ponto tocado, ENTÃO O app DEVE abrir o mais curto e listar os outros para escolha.
- **REQ-15.8** SE o servidor recusar (limite, sem texto visível, sessão acabada), ENTÃO O app DEVE mostrar a mensagem em português, sem detalhe técnico.
- **REQ-15.9** ENQUANTO o registro for `private` ou sem texto visível, O app NÃO DEVE oferecer destacar.

## Requisitos não funcionais
- **NFR-DESTF-1** O app DEVE atender WCAG 2.2 AA e funcionar sem rolagem horizontal de 360 px a 1280 px, nos temas claro e escuro; cada destaque DEVE ter alternativa em texto ("Destaque de {nome}: {n} comentários") para leitores de tela.
- **NFR-DESTF-2** O app NÃO DEVE interpretar texto de comentário ou de registro como HTML.
- **NFR-DESTF-3** Toda ação DEVE ser possível pelo teclado (selecionar, abrir a folha, comentar).

## Dados pessoais (LGPD)
Sem dado novo; os comentários seguem a 007. O app não guarda nada no aparelho.

## Casos de abuso
- **ABU-17** SE um comentário ou registro contiver marcação (`<script>`, `<b>`), ENTÃO O app DEVE mostrá-la literalmente.
- **ABU-18** SE a pessoa tocar duas vezes em Destacar ou Comentar, ENTÃO O app DEVE enviar um único pedido.

## Propriedades de corretude
- **PROP-10** Para qualquer texto visível (emoji, acento composto, quebras) e qualquer destaque devolvido pela API, o trecho desenhado na tela é exatamente o `trecho` devolvido pela API.

## Fora de escopo
Menção, reação, resposta encadeada, edição do destaque, notificação de comentário novo, destaque sobre `private`, busca por destaques.

## Esclarecimentos
Decididos pelo agente (ver Suposições): folha em vez de hover, cor mais sublinhado, sobreposição, o que o autor pode destacar do próprio texto.
