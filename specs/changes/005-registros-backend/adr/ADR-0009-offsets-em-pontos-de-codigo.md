# ADR-0009 — Offsets em pontos de código Unicode

- Status: aceito (usuário, 2026-11-05: "Ir para a 005" ao pedir a implementação; proposto pelo agente por delegação)
- Data: 2026-11-05
- Mudança de origem: 005-registros-backend (vale também para 007 e 008)

## Contexto
O trecho `partial` (005) e os destaques (007) são intervalos dentro de um texto. O mapa deixou em aberto a unidade: caractere Unicode ou unidade UTF-16 do JavaScript.
O front agora é Flutter/Dart, cujas `String` também são UTF-16: um emoji ocupa 2 unidades lá e 1 ponto de código no Python.

## Decisão
1. Todo offset da API é em **pontos de código Unicode**, contados no texto exatamente como foi enviado (sem normalização).
2. O servidor valida e fatia com a indexação nativa do Python.
3. O front converte de e para UTF-16 em uma só função compartilhada (`unidades_utf16` ↔ `pontos_de_codigo`), com teste de emoji, acento composto e quebra de linha (006).
4. O texto é guardado como veio; nada de NFC no servidor, porque normalizar deslocaria os offsets.

## Consequências
- O corte pode cair no meio de um grafema (emoji com modificador). O front deve alinhar a seleção a limites de grafema ao escolher o trecho; o servidor não rejeita.
- Um offset nunca revela tamanho do texto escondido: para o parceiro, os offsets são sempre relativos ao **texto visível** (007).

## Alternativas descartadas
- **UTF-16 na API:** casa com o JavaScript, mas o Python não indexa assim; cada fatia exigiria recodificar.
- **Grafemas:** o certo para o usuário, mas exige biblioteca nos dois lados e regra de versão do Unicode.

## Anotação da 007 (destaques)
Os offsets de um destaque são em pontos de código do **texto visível** do registro (`texto_visivel_para`): em `full`, o texto todo; em `partial`, só o trecho, para todos, inclusive o autor. Não são offsets do texto integral.
