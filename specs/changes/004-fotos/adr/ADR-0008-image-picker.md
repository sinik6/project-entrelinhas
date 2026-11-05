# ADR-0008 — `image_picker` para escolher fotos no front

- Status: aceito (usuário, 2026-11-05: "Sim, 004" ao pedir a implementação; proposto pelo agente por delegação)
- Data: 2026-11-05
- Mudança de origem: 004-fotos (usado também pela 006)

## Contexto
O app Flutter web precisa deixar a pessoa escolher uma foto da galeria ou tirar uma com a câmera (manuscrito, perfil). O Flutter não traz isso no SDK.

## Decisão
Usar `image_picker` (pacote do publicador verificado `flutter.dev`, mantido pela equipe do Flutter). Versão fixada em `pubspec.lock`, conferida no pub.dev
antes de instalar. O pacote só devolve os bytes escolhidos; o envio continua pelo cliente `dio` do app.

## Consequências
- Uma dependência nova (e suas dependências transitivas de plataforma, sem efeito na web) no `pubspec.lock`, que o teste `test_ctl_20_*` passa a listar.
- No celular, a câmera abre pelo seletor do navegador (`capture`); no computador, abre o seletor de arquivos.

## Alternativas descartadas
- `file_picker`: serve a qualquer arquivo, e a foto só precisa de imagem.
- `<input type=file>` por JS interop: mais código próprio para manter e sem testes prontos.
