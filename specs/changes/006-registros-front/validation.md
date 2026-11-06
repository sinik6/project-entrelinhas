---
id: 006-registros-front
status: rascunho
veredito: parcial
---

# Validação — Registros diários (telas)

Evidência do que foi **realmente executado** (2026-11-06). A mudança está implementada, testada localmente e vista no navegador **na pilha local**
em um caminho (`partial` com emoji, duas pessoas). **Nada foi visto no ar**, não houve auditoria independente e o arquivamento não foi feito.
Nada commitado ainda.

## Ambiente
- Flutter: só no contêiner (`entrelinhas-flutter-sdk:local`); `flutter analyze` limpo; **184 testes** passam (72 das mudanças 003 e 004 e 112 da 006).
- Backend: `test_infra_web.py` ajustado (pacote `characters`, CSP com `blob:`); 7 testes passam.
- Navegador: pilha local (`docker compose up`: PostgreSQL, API, nginx com o app) no navegador do aplicativo, com duas contas de teste criadas no banco local.
  A escolha de foto foi acionada de verdade (o seletor do navegador foi simulado por um `File` gerado numa tela `canvas`, no mesmo caminho do `image_picker`).

## Critério → evidência
| ID | Como foi provado | Resultado |
|---|---|---|
| REQ-11.1 | `hoje_test.dart`: campo, fotos (no máximo 3, tirar uma, seletor fechado, acima de 8 MB), 3 opções sem nenhuma marcada, sem grupo → Grupo | ✔ em teste |
| REQ-11.2 | `hoje_test.dart` (Entregar desabilitado e a lista do que falta, 9 caracteres, só espaços, trecho faltando); `texto_test.dart` (caracteres úteis) | ✔ em teste |
| REQ-11.3 | `trecho_test.dart` (prévia exata, trecho marcado no campo, seleção vazia, texto mudou, trocar visibilidade); **navegador**: arrastar sobre "tudo bem hoje" e "Usar a seleção" mostrou "tudo bem hoje" | ✔ teste e navegador local |
| REQ-11.4, PROP-8, CTL-42 | `texto_test.dart` (emoji, família, bandeira, acento composto, quebra, japonês; ida e volta; seleção sempre **para dentro**; 600 sorteios com semente fixa: a fatia em pontos de código é igual à prévia e as pontas estão em fronteira de grafema); `trecho_test.dart` (trecho `5..18` num texto com 2 emojis; `\r` nunca chega ao campo); **navegador**: texto com 2 emojis, o parceiro recebeu `texto_visivel = "tudo bem hoje"` | ✔ teste e navegador local |
| REQ-11.5, CTL-44 | `hoje_test.dart` (resumo, aviso "não pode ser editado nem apagado", Voltar não envia); **navegador**: diálogo com "Quem lê: Só um trecho / Trecho: tudo bem hoje / Fotos: 1 foto" | ✔ teste e navegador local |
| REQ-11.6 | `hoje_test.dart` (fotos, depois registro, em ordem; progresso "Enviando fotos 1 de 2…"); `api_http_test.dart` (corpo, CSRF); **navegador**: `POST /fotos` 201, `POST /registros` 201, "Registro entregue" | ✔ teste e navegador local |
| REQ-11.7 | `hoje_test.dart`: foto que cai, tentar de novo reenvia **só** a que faltou; registro que falha não reenvia fotos; 422 sob o campo; 401 leva a entrar | ✔ em teste |
| REQ-11.8 | `hoje_test.dart`: 409 mostra o registro do dia, abrir já entregue, estado da outra pessoa (ainda não / entregou / privado), erro de carga | ✔ em teste |
| REQ-11.9, CTL-41 | `sem_persistencia_test.dart`: varredura de `lib/` (nenhum `localStorage`, `sessionStorage`, IndexedDB, `shared_preferences`, `dart:html`, `dart:io`, restauração de estado), pubspec sem pacote de armazenamento, sem `print`/log no texto, rascunho some depois de entregar e ao "recarregar"; **navegador**: recarregar a página descartou o rascunho | ✔ teste e navegador local |
| REQ-12.1 a 12.7 | `diario_test.dart`: mês atual, anterior e volta (não passa do atual, virada de ano), nome/cor/dia/hora em São Paulo, as três visões, nota do trecho, aviso de privado, trecho marcado (com emoji), foto em tela cheia com texto alternativo, mês vazio, erro, sem conexão, 401 | ✔ em teste |
| REQ-12.3 (visão real) | **navegador**, como Bia: o Diário mostrou "tudo bem hoje" e "Mostrando só o trecho que Ana escolheu", sem foto; o corpo de `GET /registros?mes=` não tinha `texto`, `trecho`, nem "calmo"/"bonito" | ✔ no navegador local |
| NFR-TELA-1, NFR-TELA-3 | `acessibilidade_test.dart`: 6 telas novas (Hoje vazia, preenchida, com trecho, já entregue, Diário, foto em tela cheia) nos dois temas (contraste, alvos de toque, rótulos) e em 360 e 1280 px sem rolagem horizontal | ✔ em teste (sem teste de navegação só por teclado; o navegador não foi conferido em 360 px) |
| NFR-TELA-2, ABU-13, CTL-43 | `diario_test.dart`: `<script>`, `<b>`, `&lt;`, `<img onerror>` aparecem literalmente, na visão do autor e na do parceiro | ✔ em teste |
| ABU-12 | `duplo_toque_test.dart`: dois toques em Entregar (uma confirmação), dois em confirmar (um registro), enviando pendente, dois em "Tentar de novo" (um registro) | ✔ em teste |
| CTL-45 | foto servida pela 004; no navegador a foto do registro voltou com 200 usando o cookie | ✔ (da 004) |

## Mutação do front (roteiro em `frontend/tool/mutacao_registros.py`)
16 mutantes em `texto.dart`, `hoje_page.dart`, `cartao_de_registro.dart` e `diario_page.dart`: seleção que cresce para fora do grafema (início e fim), conversão UTF-16 ↔ pontos
(as duas), formatador que deixa passar `\r`, trecho enviado em UTF-16, "Voltar" que entrega, sem trava de envio repetido, fotos reenviadas, trecho que sobrevive à edição,
mínimo de texto 5, foto grande no rascunho, 409 sem mostrar o dia, trecho marcado em UTF-16 no cartão, cartão do parceiro marcando trecho, Diário passando do mês atual.
Na primeira rodada **2 sobreviveram** ("sem trava de envio repetido" e "cartão do parceiro marca o trecho"); foram acrescentados o teste de dois toques em "Tentar de novo" e o do
cartão do parceiro, e os dois morreram. **16 de 16 mortos.**

## Achados do teste no navegador (corrigido e em aberto)
1. **Corrigido (defeito real da 004, que não aparecia nos testes):** a CSP do nginx tinha `connect-src 'self'`, e o `image_picker` lê a foto escolhida por um endereço `blob:`. Sem
   `blob:` a escolha de foto **falha** ("Não foi possível abrir as fotos"), no perfil e em Hoje. Corrigido para `connect-src 'self' blob:` (teste `test_ctl_19_*` ficou vermelho antes e verde depois);
   conferido no navegador local. **A 004 declarava que o seletor nativo não fora acionado: era exatamente aí que estava o defeito.**
2. **Em aberto (decisão do dono):** os emojis aparecem como quadradinhos no campo e na leitura. O Flutter web busca a fonte de emoji em `fonts.gstatic.com`, e a CSP bloqueia
   (de propósito: nenhuma origem externa). O texto e os offsets estão certos (o trecho com emoji foi entregue e lido corretamente); só o desenho falha. Opções: (a) embutir uma fonte de emoji no app
   (arquivo de 1 a 10 MB; precisa baixar a fonte e escolher a licença/peso), (b) liberar `fonts.gstatic.com` na CSP (o navegador de quem usa o app consultaria o Google), (c) aceitar os quadradinhos.
3. **Não explicado:** numa tentativa, um toque em "Entregar" do diálogo fechou a confirmação sem enviar nada; na tentativa seguinte, o mesmo toque entregou. Não reproduzi; suspeito de toque durante a
   animação de abertura do diálogo no navegador automatizado. Fica como risco baixo.

## Não provado
- **Nada no ar.**
- Visões `full` e `private` e a foto em tela cheia **não foram vistas no navegador** (só em teste de widget); só o caminho `partial` com emoji foi feito de ponta a ponta com as duas contas.
- 360 px no navegador não foi conferido (só em teste de widget); teclado puro e leitor de tela reais não foram usados.
- O seletor de fotos foi simulado (arquivo gerado); não houve foto de celular real (HEIC, rotação EXIF).
- A seleção de texto por toque no celular (Chrome Android, Safari iOS) não foi testada: o risco do `design.md` §15 continua aberto.
- Sem auditoria independente e sem `pip-audit`.
- A tela inicial depois de entrar continua sendo Grupo (REQ-5.2 da 003); Hoje é um toque adiante. Decisão de produto em aberto.

## Veredito
**Parcial.** Implementado, 184 testes e 16/16 mutantes mortos, e o caminho principal visto no navegador local; falta deploy e conferência no ar, auditoria independente,
e a decisão sobre a fonte de emoji.
