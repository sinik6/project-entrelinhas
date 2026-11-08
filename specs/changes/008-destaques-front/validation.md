---
id: 008-destaques-front
status: rascunho
veredito: parcial
---

# Validação — Destaques e comentários (telas)

Evidência do que foi **realmente executado** (2026-11-08). Implementado e testado em teste de widget; **não foi aberto no navegador**, nada no ar, sem auditoria independente, sem arquivamento, nada commitado.

## Ambiente
- Flutter só no contêiner (`entrelinhas-flutter-sdk:local`); `flutter analyze` limpo; **241 testes** passam (os das mudanças anteriores e os da 008).

## Mudança de desenho em relação ao `design.md` (decidida pelo agente)
O `design.md` previa `SelectableText.rich` com menu de seleção próprio. Foi feito um **leitor em tela cheia** ("Ler e destacar", em cada cartão com texto visível): um campo só de leitura
(`TextField` com controlador que pinta os destaques) e uma **barra com "Destacar" e "Destacar e comentar"** sempre visível, habilitada quando há seleção válida. Motivos: o menu nativo
varia entre navegadores (risco do §15 do design), a barra é alcançável por teclado e leitor de tela, e a seleção programática é testável. Os destaques também aparecem numa **lista** abaixo do texto
(cada um com a frase "Destaque de {nome}: {n} comentários"), que é a alternativa em texto de NFR-DESTF-1. O toque no trecho marcado também abre a folha.

## Critério → evidência
| ID | Como foi provado | Resultado |
|---|---|---|
| REQ-15.1, REQ-15.9 | `destaque_selecao_test.dart`: privado não oferece; ações desabilitadas sem seleção; autor em `partial` só destaca dentro do trecho (seleção só no escondido → aviso e desabilitado; seleção que entra no visível é cortada) | ✔ em teste |
| REQ-15.2, PROP-10 | `destaque_selecao_test.dart`: `5..18` em pontos de código num texto com emoji, seleção invertida, começo no meio de um emoji encolhe para dentro; `destaque_pintura_test.dart`: 300 sorteios (emoji, acento composto, bandeira, quebra, japonês) em que o segmento marcado é exatamente o `trecho` da API e a posição volta ao ponto de código certo | ✔ em teste |
| REQ-15.3 | `destaque_pintura_test.dart`: fundo translúcido (alfa 0,22) com **contraste ≥ 4,5 em todas as 8 cores sugeridas, nos dois temas**; sublinhado no mesmo tom (a cor não carrega sozinha) | ✔ em teste |
| REQ-15.4, REQ-15.5 | `destaque_folha_test.dart`: abrir pelo item da lista e pelo toque no texto, trecho/autor/hora/texto, comentar, editar ("editado"), apagar o próprio, os dos outros sem Editar/Apagar, "Apagar destaque" só para o dono | ✔ em teste |
| REQ-15.6 | `destaque_folha_test.dart`: aviso "os comentários deste destaque também serão apagados", Voltar não apaga, Apagar apaga e fecha | ✔ em teste |
| REQ-15.7 | `destaque_pintura_test.dart` (o mais curto por cima; toque resolve pelo menor intervalo; fim exclusivo) e `destaque_folha_test.dart` (abre o curto e lista o outro; trocar pelo chip) | ✔ em teste |
| REQ-15.8 | limite de 50 e de 20, 403 com a frase do servidor (e não a do CSRF: `erros.dart` passou a usar o `detalhe` do 403), 401 → entrar | ✔ em teste |
| ABU-17 | comentário com `<script>`, `<b>`, `&lt;` aparece literalmente | ✔ em teste |
| ABU-18 | dois toques em Destacar e em Comentar enviam um pedido só | ✔ em teste |
| NFR-DESTF-1, NFR-DESTF-3 | `acessibilidade_test.dart`: 3 telas novas (leitor, leitor com destaques, folha) nos dois temas (contraste, alvos de toque, rótulos) e em 360 e 1280 px sem rolagem horizontal; frase de cada destaque conferida em `destaque_folha_test.dart`. Os botões são botões do Material (teclado por padrão) | ✔ em teste (sem teste de navegação só por teclado) |
| Cliente HTTP | `api_http_test.dart`: rotas, corpo, CSRF, 403 com frase | ✔ em teste |

## Mutação (roteiro em `frontend/tool/mutacao_destaques.py`)
10 mutantes: o mais longo por cima (pintura e toque), fundo opaco demais, autor em `partial` sem o deslocamento, destaque enviado em UTF-16, sem trava de pedido repetido (leitor e folha),
apagar destaque sem confirmação, "Apagar destaque" e Editar para todos. **10 de 10 mortos.** Um 11º (afrouxar o `clamp` da seleção no leitor) sobreviveu por ser **equivalente**
(`trechoDaSelecao` já corta ao texto) e foi retirado do roteiro.

## Não provado
- **Nada no navegador e nada no ar:** a barra de ações, a seleção por arrasto/toque e a folha só foram vistas em teste de widget (seleção feita pelo controlador, toque simulado pelo `onTap`). O comportamento da seleção em campo só de leitura no Chrome Android e no Safari iOS é o risco do design e continua aberto.
- Os destaques **não aparecem pintados nos cartões do Diário**, só no leitor (decisão de escopo para não carregar destaques de todos os cartões).
- Sem teclado puro nem leitor de tela reais; sem auditoria independente.

## Veredito
**Parcial.** Implementado, 241 testes e 10/10 mutantes mortos; faltam o teste no navegador, o deploy, a auditoria independente e o arquivamento.
