// [008] REQ-15.4 a 15.8, ABU-17, ABU-18: a folha de comentários de um destaque.
import 'dart:async';

import 'package:entrelinhas/features/destaques/modelos.dart';
import 'package:entrelinhas/shared/api/api.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'suporte/api_falsa.dart';
import 'suporte/hoje_de_teste.dart';
import 'suporte/leitor_de_teste.dart';

const texto = 'Hoje foi um dia calmo e bonito.';

final doParceiro = registroDe(
  id: 'r',
  nome: 'Bia',
  meu: false,
  texto: texto,
  fotos: const [],
);

Future<ApiFalsa> abrirFolha(
  WidgetTester t, {
  List<Destaque> destaques = const [],
  String abrir = 'd1',
}) async {
  final api = await abrirLeitor(t, doParceiro, destaques: destaques);
  await t.tap(find.byKey(Key('destaque-$abrir')));
  await t.pumpAndSettle();
  return api;
}

Finder get folha => find.byKey(const Key('folha-de-comentarios'));
Finder get campoComentario => find.byKey(const Key('campo-comentario'));

Destaque meuDestaque({List<Comentario> comentarios = const []}) =>
    destaqueDe(meu: true, nome: 'Ana', cor: corVerde, comentarios: comentarios);

Comentario meuComentario({String id = 'c1', String texto = 'meu'}) =>
    comentarioDe(id: id, texto: texto, nome: 'Ana', cor: corVerde, meu: true);

void main() {
  testWidgets(
    '[008] REQ-15.4: tocar no destaque abre a folha com trecho, autor, hora e texto',
    (t) async {
      await abrirFolha(
        t,
        destaques: [
          destaqueDe(comentarios: [comentarioDe(texto: 'Gostei muito.')]),
        ],
      );

      expect(folha, findsOneWidget);
      expect(
        find.descendant(of: folha, matching: find.text('Bia')),
        findsOneWidget,
      );
      expect(
        find.descendant(of: folha, matching: find.text('Gostei muito.')),
        findsOneWidget,
      );
      expect(
        find.descendant(of: folha, matching: find.text('06/11 às 12:00')),
        findsWidgets,
      );
    },
  );

  testWidgets(
    '[008] REQ-15.4: tocar no trecho marcado do texto também abre a folha',
    (t) async {
      await abrirLeitor(t, doParceiro, destaques: [destaqueDe()]);

      await tocarNoLeitor(t, 2);

      expect(folha, findsOneWidget);
    },
  );

  testWidgets('[008] REQ-15.4: tocar fora de qualquer destaque não abre nada', (
    t,
  ) async {
    await abrirLeitor(t, doParceiro, destaques: [destaqueDe()]);

    await tocarNoLeitor(t, 20);

    expect(folha, findsNothing);
  });

  testWidgets('[008] REQ-15.4: só o dono do destaque vê "Apagar destaque"', (
    t,
  ) async {
    await abrirFolha(t, destaques: [destaqueDe()]);
    expect(find.text('Apagar destaque'), findsNothing);
  });

  testWidgets('[008] REQ-15.4: o dono do destaque vê "Apagar destaque"', (
    t,
  ) async {
    await abrirFolha(t, destaques: [meuDestaque()]);
    expect(find.text('Apagar destaque'), findsOneWidget);
  });

  testWidgets('[008] REQ-15.5: comentar aparece na folha na hora', (t) async {
    final api = await abrirFolha(t, destaques: [destaqueDe()]);

    await t.enterText(campoComentario, 'Concordo.');
    await t.pump();
    await tocarBotao(t, 'Comentar');

    expect(api.chamadas, contains('comentar'));
    expect(
      find.descendant(of: folha, matching: find.text('Concordo.')),
      findsOneWidget,
    );
    final campo = t.widget<TextField>(
      find.descendant(of: campoComentario, matching: find.byType(TextField)),
    );
    expect(campo.controller!.text, isEmpty);
  });

  testWidgets('[008] REQ-15.5: comentário vazio não é enviado', (t) async {
    final api = await abrirFolha(t, destaques: [destaqueDe()]);

    await t.enterText(campoComentario, '   ');
    await t.pump();
    final botao = find.ancestor(
      of: find.text('Comentar'),
      matching: find.bySubtype<ButtonStyleButton>(),
    );

    expect(t.widget<ButtonStyleButton>(botao.last).onPressed, isNull);
    expect(api.chamadas, isNot(contains('comentar')));
  });

  testWidgets('[008] REQ-15.5: editar o próprio comentário', (t) async {
    final api = await abrirFolha(
      t,
      destaques: [
        meuDestaque(comentarios: [meuComentario(texto: 'antes')]),
      ],
    );

    await t.tap(find.byTooltip('Editar comentário'));
    await t.pumpAndSettle();
    await t.enterText(campoComentario, 'depois');
    await t.pump();
    await tocarBotao(t, 'Salvar');

    expect(api.chamadas, contains('editarComentario:c1'));
    expect(
      find.descendant(of: folha, matching: find.text('depois')),
      findsOneWidget,
    );
    expect(
      find.descendant(of: folha, matching: find.text('antes')),
      findsNothing,
    );
    expect(find.textContaining('editado'), findsOneWidget);
  });

  testWidgets(
    '[008] REQ-15.5: comentário dos outros não tem Editar nem Apagar',
    (t) async {
      await abrirFolha(
        t,
        destaques: [
          destaqueDe(comentarios: [comentarioDe()]),
        ],
      );

      expect(find.byTooltip('Editar comentário'), findsNothing);
      expect(find.byTooltip('Apagar comentário'), findsNothing);
    },
  );

  testWidgets('[008] REQ-15.5: apagar o próprio comentário', (t) async {
    final api = await abrirFolha(
      t,
      destaques: [
        meuDestaque(comentarios: [meuComentario(texto: 'some')]),
      ],
    );

    await t.tap(find.byTooltip('Apagar comentário'));
    await t.pumpAndSettle();

    expect(api.chamadas, contains('apagarComentario:c1'));
    expect(
      find.descendant(of: folha, matching: find.text('some')),
      findsNothing,
    );
  });

  testWidgets(
    '[008] REQ-15.6: apagar o destaque avisa dos comentários e pede confirmação',
    (t) async {
      final api = await abrirFolha(
        t,
        destaques: [
          meuDestaque(comentarios: [comentarioDe()]),
        ],
      );

      await tocarBotao(t, 'Apagar destaque');

      expect(
        find.textContaining('comentários deste destaque também serão apagados'),
        findsOneWidget,
      );
      expect(api.chamadas, isNot(contains('apagarDestaque:d1')));

      await tocarBotao(t, 'Voltar');
      expect(api.chamadas, isNot(contains('apagarDestaque:d1')));

      await tocarBotao(t, 'Apagar destaque');
      await t.tap(
        find.descendant(
          of: find.byType(AlertDialog),
          matching: find.widgetWithText(FilledButton, 'Apagar'),
        ),
      );
      await t.pumpAndSettle();

      expect(api.chamadas, contains('apagarDestaque:d1'));
      expect(folha, findsNothing);
      expect(find.byKey(const Key('destaque-d1')), findsNothing);
    },
  );

  testWidgets(
    '[008] REQ-15.7: no ponto sobreposto abre o mais curto e lista os outros',
    (t) async {
      final longo = destaqueDe(
        id: 'longo',
        inicio: 0,
        fim: 20,
        trecho: texto.substring(0, 20),
        nome: 'Ana',
        cor: corVerde,
      );
      final curto = destaqueDe(
        id: 'curto',
        inicio: 5,
        fim: 8,
        trecho: texto.substring(5, 8),
      );
      await abrirLeitor(t, doParceiro, destaques: [longo, curto]);

      await tocarNoLeitor(t, 6);

      expect(
        find.descendant(of: folha, matching: find.text(texto.substring(5, 8))),
        findsWidgets,
      );
      expect(find.byKey(const Key('outro-destaque-longo')), findsOneWidget);

      await t.tap(find.byKey(const Key('outro-destaque-longo')));
      await t.pumpAndSettle();

      expect(
        find.descendant(of: folha, matching: find.text('Destaque de Ana')),
        findsOneWidget,
      );
      expect(find.byKey(const Key('outro-destaque-curto')), findsOneWidget);
    },
  );

  testWidgets('[008] ABU-17: comentário com marcação aparece literalmente', (
    t,
  ) async {
    const marcacao = '<script>alert(1)</script> <b>oi</b> &lt;';
    await abrirFolha(
      t,
      destaques: [
        destaqueDe(comentarios: [comentarioDe(texto: marcacao)]),
      ],
    );

    expect(
      find.descendant(of: folha, matching: find.text(marcacao)),
      findsOneWidget,
    );
  });

  testWidgets('[008] ABU-18: dois toques em Comentar enviam um único pedido', (
    t,
  ) async {
    final api = await abrirFolha(t, destaques: [destaqueDe()]);
    api.portaoDoComentario = Completer<void>();
    await t.enterText(campoComentario, 'uma vez só');
    await t.pump();

    final botao = find.widgetWithText(FilledButton, 'Comentar');
    await t.tap(botao);
    await t.tap(botao, warnIfMissed: false);
    await t.pump();
    api.portaoDoComentario!.complete();
    await t.pumpAndSettle();

    expect(api.chamadas.where((c) => c == 'comentar'), hasLength(1));
  });

  testWidgets(
    '[008] REQ-15.8: limite de 20 comentários aparece na folha, em português',
    (t) async {
      final api = await abrirFolha(t, destaques: [destaqueDe()]);
      api.falhaAoComentar = const ErroApi(
        409,
        detalhe: 'Este destaque já tem 20 comentários.',
      );

      await t.enterText(campoComentario, 'mais um');
      await t.pump();
      await tocarBotao(t, 'Comentar');

      expect(find.text('Este destaque já tem 20 comentários.'), findsOneWidget);
    },
  );

  testWidgets(
    '[008] REQ-15.8: 403 do servidor mostra a frase do servidor, não a do CSRF',
    (t) async {
      final api = await abrirFolha(
        t,
        destaques: [
          meuDestaque(comentarios: [meuComentario()]),
        ],
      );
      api.falhaAoComentar = const ErroApi(
        403,
        detalhe: 'Só quem escreveu pode fazer isso.',
      );
      await t.enterText(campoComentario, 'x y z');
      await t.pump();
      await tocarBotao(t, 'Comentar');

      expect(find.text('Só quem escreveu pode fazer isso.'), findsOneWidget);
      expect(find.textContaining('segurança'), findsNothing);
    },
  );

  testWidgets(
    '[008] NFR-DESTF-1: cada destaque tem alternativa em texto com autor e número de comentários',
    (t) async {
      final semantica = t.ensureSemantics();
      await abrirLeitor(
        t,
        doParceiro,
        destaques: [
          destaqueDe(
            comentarios: [
              comentarioDe(),
              comentarioDe(id: 'c2'),
            ],
          ),
          destaqueDe(id: 'd2', inicio: 9, fim: 15, trecho: 'um dia'),
        ],
      );

      expect(
        t.getSemantics(find.byKey(const Key('destaque-d1'))).label,
        contains('Destaque de Bia: 2 comentários'),
      );
      expect(
        t.getSemantics(find.byKey(const Key('destaque-d2'))).label,
        contains('Destaque de Bia: 0 comentários'),
      );
      semantica.dispose();
    },
  );
}
