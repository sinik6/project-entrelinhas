// [008] REQ-15.1, REQ-15.2, REQ-15.8, REQ-15.9, ABU-18: selecionar no leitor e criar o destaque.
import 'dart:async';

import 'package:entrelinhas/features/hoje/modelos.dart';
import 'package:entrelinhas/shared/api/api.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'suporte/api_falsa.dart';
import 'suporte/hoje_de_teste.dart';
import 'suporte/leitor_de_teste.dart';

const texto = 'Oi 😀 tudo bem hoje, 😀 certo.';

Registro doParceiro({
  String? t = texto,
  String visibilidade = Visibilidade.todos,
}) => registroDe(
  id: 'r',
  nome: 'Bia',
  meu: false,
  texto: t,
  visibilidade: visibilidade,
  fotos: const [],
);

bool habilitado(WidgetTester t, String rotulo) {
  final botao = find.ancestor(
    of: find.text(rotulo),
    matching: find.bySubtype<ButtonStyleButton>(),
  );
  return t.widget<ButtonStyleButton>(botao.first).onPressed != null;
}

void main() {
  testWidgets(
    '[008] REQ-15.9: registro privado do parceiro não oferece destacar',
    (t) async {
      final api = apiDaAna()
        ..registros.add(
          doParceiro(t: null, visibilidade: Visibilidade.privado),
        );
      await abrirDiario(t, api: api);

      expect(find.text('Ler e destacar'), findsNothing);
    },
  );

  testWidgets(
    '[008] REQ-15.1: sem seleção as ações ficam desabilitadas e a tela explica',
    (t) async {
      await abrirLeitor(t, doParceiro());

      expect(find.byKey(leitorTexto), findsOneWidget);
      expect(habilitado(t, 'Destacar'), isFalse);
      expect(habilitado(t, 'Destacar e comentar'), isFalse);
      expect(
        find.text('Selecione um trecho do texto para destacar.'),
        findsOneWidget,
      );
    },
  );

  testWidgets('[008] REQ-15.1: com seleção válida as duas ações habilitam', (
    t,
  ) async {
    await abrirLeitor(t, doParceiro());

    await selecionarNoLeitor(t, 6, 19);

    expect(habilitado(t, 'Destacar'), isTrue);
    expect(habilitado(t, 'Destacar e comentar'), isTrue);
  });

  testWidgets(
    '[008] REQ-15.2: o destaque vai em pontos de código e aparece na lista',
    (t) async {
      final api = await abrirLeitor(t, doParceiro());

      await selecionarNoLeitor(t, 6, 19); // "tudo bem hoje", depois de "Oi 😀 "
      await tocarBotao(t, 'Destacar');

      expect(api.ultimoDestaque['inicio'], 5);
      expect(api.ultimoDestaque['fim'], 18);
      expect(api.ultimoDestaque['comentario'], isNull);
      expect(api.ultimoDestaque['registro'], 'r');
      expect(find.byKey(const Key('destaque-dn1')), findsOneWidget);
    },
  );

  testWidgets(
    '[008] REQ-15.2: seleção que começa no meio de um emoji encolhe para dentro',
    (t) async {
      final api = await abrirLeitor(t, doParceiro());

      await selecionarNoLeitor(
        t,
        4,
        19,
      ); // começa entre as metades do 😀 (3..5)
      await tocarBotao(t, 'Destacar');

      expect(api.ultimoDestaque['inicio'], 4, reason: 'depois do emoji');
      expect(api.ultimoDestaque['fim'], 18);
    },
  );

  testWidgets(
    '[008] REQ-15.2: "Destacar e comentar" pede o comentário e manda tudo num pedido',
    (t) async {
      final api = await abrirLeitor(t, doParceiro());
      await selecionarNoLeitor(t, 6, 19);

      await tocarBotao(t, 'Destacar e comentar');
      await t.enterText(
        find.byKey(const Key('campo-comentario-novo')),
        'Adorei essa parte.',
      );
      await t.pump();
      await tocarBotao(t, 'Salvar destaque');

      expect(api.ultimoDestaque['comentario'], 'Adorei essa parte.');
      expect(api.chamadas.where((c) => c == 'criarDestaque'), hasLength(1));
      expect(find.byKey(const Key('destaque-dn1')), findsOneWidget);
    },
  );

  testWidgets(
    '[008] REQ-15.1: autor em partial só destaca dentro do trecho visível',
    (t) async {
      final meu = registroDe(
        id: 'r',
        visibilidade: Visibilidade.trecho,
        texto: 'ESCONDIDO visível aqui ESCONDIDO',
        trecho: const Trecho(inicio: 10, fim: 22),
        fotos: const [],
      );
      final api = await abrirLeitor(t, meu);

      await selecionarNoLeitor(t, 0, 9); // só o escondido
      expect(habilitado(t, 'Destacar'), isFalse);
      expect(
        find.text('Selecione um trecho dentro do texto visível.'),
        findsOneWidget,
      );

      await selecionarNoLeitor(t, 5, 17); // a parte de fora é cortada
      expect(habilitado(t, 'Destacar'), isTrue);
      await tocarBotao(t, 'Destacar');

      expect(api.ultimoDestaque['inicio'], 0, reason: 'relativo ao visível');
      expect(api.ultimoDestaque['fim'], 7);
    },
  );

  testWidgets(
    '[008] REQ-15.2: seleção invertida (arrastar para trás) vale igual',
    (t) async {
      final api = await abrirLeitor(t, doParceiro());

      await selecionarNoLeitor(t, 19, 6);
      await tocarBotao(t, 'Destacar');

      expect(api.ultimoDestaque['inicio'], 5);
      expect(api.ultimoDestaque['fim'], 18);
    },
  );

  testWidgets('[008] ABU-18: dois toques em Destacar enviam um único pedido', (
    t,
  ) async {
    final api = await abrirLeitor(t, doParceiro());
    api.portaoDoDestaque = Completer<void>();
    await selecionarNoLeitor(t, 6, 19);

    final botao = find.widgetWithText(FilledButton, 'Destacar');
    await t.tap(botao);
    await t.tap(botao, warnIfMissed: false);
    await t.pump();
    api.portaoDoDestaque!.complete();
    await t.pumpAndSettle();

    expect(api.chamadas.where((c) => c == 'criarDestaque'), hasLength(1));
  });

  testWidgets(
    '[008] REQ-15.8: limite do servidor aparece em português, sem detalhe técnico',
    (t) async {
      final api = await abrirLeitor(t, doParceiro());
      api.falhaAoDestacar = const ErroApi(
        409,
        detalhe: 'Você já fez 50 destaques neste registro.',
      );
      await selecionarNoLeitor(t, 6, 19);

      await tocarBotao(t, 'Destacar');

      expect(
        find.text('Você já fez 50 destaques neste registro.'),
        findsOneWidget,
      );
      expect(find.byKey(const Key('destaque-dn1')), findsNothing);
    },
  );

  testWidgets('[008] REQ-15.8: sessão que acabou leva à tela de entrar', (
    t,
  ) async {
    final api = await abrirLeitor(t, doParceiro());
    api.falhaAoDestacar = const ErroApi(401);
    await selecionarNoLeitor(t, 6, 19);

    await tocarBotao(t, 'Destacar');

    expect(find.text('Sua sessão acabou. Entre de novo.'), findsOneWidget);
  });
}
