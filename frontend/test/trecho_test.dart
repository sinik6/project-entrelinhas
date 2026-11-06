// [006] REQ-11.3, REQ-11.4, PROP-8, CTL-42: escolher o trecho no campo, prévia exata e trecho enviado em pontos de código.
import 'package:entrelinhas/features/hoje/campo_do_registro.dart';
import 'package:entrelinhas/features/hoje/modelos.dart';
import 'package:entrelinhas/shared/texto.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'suporte/api_falsa.dart';
import 'suporte/hoje_de_teste.dart';

const comEmoji = 'Oi 😀 tudo bem hoje, 😀 certo.';

String previa(WidgetTester t) =>
    t.widget<Text>(find.byKey(const Key('previa-trecho'))).data!;

Future<ApiFalsa> prepararTrecho(WidgetTester t, String texto) async {
  final api = await abrirHoje(t);
  await escrever(t, texto);
  await adicionarFoto(t);
  await tocarTexto(t, 'Só um trecho');
  return api;
}

Future<void> usarSelecao(WidgetTester t, int inicio, int fim) async {
  await selecionar(t, inicio, fim);
  await tocarBotao(t, 'Usar a seleção');
}

void main() {
  testWidgets(
    '[006] REQ-11.3: escolher "Só um trecho" mostra a instrução e o botão',
    (t) async {
      await prepararTrecho(t, textoValido);

      expect(find.text('Usar a seleção'), findsOneWidget);
      expect(find.textContaining('Selecione no texto'), findsWidgets);
      expect(find.byKey(const Key('previa-trecho')), findsNothing);
    },
  );

  testWidgets(
    '[006] REQ-11.3: "Usar a seleção" mostra a prévia exata e marca o trecho no campo',
    (t) async {
      await prepararTrecho(t, textoValido);
      final inicio = textoValido.indexOf('dia calmo');

      await usarSelecao(t, inicio, inicio + 'dia calmo'.length);

      expect(previa(t), 'dia calmo');
      expect(find.textContaining('lerá exatamente isto'), findsOneWidget);
      final controlador = controladorDoTexto(t) as ControladorDoRegistro;
      expect(controlador.marcado, (inicio: inicio, fim: inicio + 9));
      expect(entregarHabilitado(t), isTrue);
    },
  );

  testWidgets(
    '[006] REQ-11.4: o trecho vai em pontos de código, não em unidades UTF-16',
    (t) async {
      final api = await prepararTrecho(t, comEmoji);
      final i = comEmoji.indexOf('tudo bem hoje');

      await usarSelecao(t, i, i + 'tudo bem hoje'.length);
      expect(previa(t), 'tudo bem hoje');

      await tocarBotao(t, 'Entregar');
      await t.tap(confirmarEntrega);
      await t.pumpAndSettle();

      // "Oi 😀 " são 5 pontos de código (6 unidades UTF-16): início 5, fim 5 + 13
      expect(api.ultimaEntrega['trecho'], const Trecho(inicio: 5, fim: 18));
      expect(api.ultimaEntrega['visibilidade'], Visibilidade.trecho);
      expect(
        api.ultimaEntrega['texto'],
        comEmoji,
        reason: 'o texto inteiro vai junto',
      );
    },
  );

  testWidgets(
    '[006] PROP-8: o trecho enviado, fatiado em pontos de código, é igual à prévia',
    (t) async {
      final api = await prepararTrecho(t, comEmoji);
      final i = comEmoji.indexOf('hoje, 😀 certo');

      await usarSelecao(t, i, i + 'hoje, 😀 certo'.length);
      final mostrada = previa(t);
      await tocarBotao(t, 'Entregar');
      await t.tap(confirmarEntrega);
      await t.pumpAndSettle();

      final trecho = api.ultimaEntrega['trecho']! as Trecho;
      expect(
        fatiaPorPontos(
          api.ultimaEntrega['texto']! as String,
          trecho.inicio,
          trecho.fim,
        ),
        mostrada,
      );
    },
  );

  testWidgets(
    '[006] REQ-11.4: seleção que começa no meio de um emoji encolhe para dentro; nunca sobra meia letra',
    (t) async {
      await prepararTrecho(t, 'abcdef 😀 ghijkl');
      final emoji = 'abcdef 😀 ghijkl'.indexOf('😀');

      await usarSelecao(
        t,
        emoji + 1,
        'abcdef 😀 ghijkl'.length,
      ); // começa entre as metades

      expect(previa(t), ' ghijkl');
      expect(previa(t).runes.any((r) => r >= 0xD800 && r <= 0xDFFF), isFalse);
    },
  );

  testWidgets(
    '[006] REQ-11.4: seleção que termina no meio de um emoji também encolhe para dentro',
    (t) async {
      await prepararTrecho(t, 'abcdef 😀 ghijkl');
      final emoji = 'abcdef 😀 ghijkl'.indexOf('😀');

      await usarSelecao(t, 0, emoji + 1);

      expect(previa(t), 'abcdef ');
    },
  );

  testWidgets(
    '[006] REQ-11.3: seleção vazia não vira trecho e a tela explica',
    (t) async {
      await prepararTrecho(t, 'abcdef 😀 ghijkl');

      await usarSelecao(t, 4, 4);
      expect(find.byKey(const Key('previa-trecho')), findsNothing);
      expect(
        find.text('Selecione no texto o trecho que a outra pessoa poderá ler.'),
        findsWidgets,
      );
      expect(entregarHabilitado(t), isFalse);
    },
  );

  testWidgets(
    '[006] REQ-11.3: mudar o texto depois de escolher o trecho apaga o trecho e avisa',
    (t) async {
      await prepararTrecho(t, textoValido);
      await usarSelecao(t, 0, 4);
      expect(find.byKey(const Key('previa-trecho')), findsOneWidget);

      await escrever(t, '$textoValido mais um pouco');

      expect(find.byKey(const Key('previa-trecho')), findsNothing);
      expect(
        find.text('O texto mudou. Escolha o trecho de novo.'),
        findsOneWidget,
      );
      expect(entregarHabilitado(t), isFalse);
      expect((controladorDoTexto(t) as ControladorDoRegistro).marcado, isNull);
    },
  );

  testWidgets(
    '[006] REQ-11.3: trocar a visibilidade esconde a prévia e não envia trecho',
    (t) async {
      final api = await prepararTrecho(t, textoValido);
      await usarSelecao(t, 0, 4);

      await tocarTexto(t, 'Só eu');
      expect(find.byKey(const Key('previa-trecho')), findsNothing);
      await tocarBotao(t, 'Entregar');
      await t.tap(confirmarEntrega);
      await t.pumpAndSettle();

      expect(api.ultimaEntrega['trecho'], isNull);
      expect(api.ultimaEntrega['visibilidade'], Visibilidade.privado);
    },
  );

  testWidgets(
    '[006] REQ-11.4: o campo nunca guarda "\\r": quebra de linha chega como "\\n"',
    (t) async {
      final api = await abrirHoje(t);
      await escrever(t, 'Primeira linha\r\nsegunda linha\raqui.');
      await adicionarFoto(t);
      await tocarTexto(t, 'Todo o grupo lê');

      expect(controladorDoTexto(t).text, isNot(contains('\r')));
      await tocarBotao(t, 'Entregar');
      await t.tap(confirmarEntrega);
      await t.pumpAndSettle();

      expect(
        api.ultimaEntrega['texto'],
        'Primeira linha\nsegunda linha\naqui.',
      );
    },
  );

  testWidgets(
    '[006] REQ-11.5: a confirmação de "Só um trecho" mostra o trecho que será lido',
    (t) async {
      await prepararTrecho(t, textoValido);
      await usarSelecao(t, 0, 4);

      await tocarBotao(t, 'Entregar');

      expect(
        find.descendant(
          of: find.byType(AlertDialog),
          matching: find.textContaining('Só um trecho'),
        ),
        findsOneWidget,
      );
      expect(
        find.descendant(
          of: find.byType(AlertDialog),
          matching: find.textContaining('Hoje'),
        ),
        findsOneWidget,
      );
    },
  );
}
