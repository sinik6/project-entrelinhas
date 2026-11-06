// [006] ABU-12, CTL-44: toque repetido (ou clique repetido por rede lenta) cria um único pedido de registro.
import 'dart:async';

import 'package:entrelinhas/shared/api/api.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'suporte/hoje_de_teste.dart';

void main() {
  testWidgets(
    '[006] ABU-12: dois toques em Entregar abrem uma confirmação só',
    (t) async {
      await abrirHoje(t);
      await preencherTudo(t);

      await t.ensureVisible(botaoEntregar);
      await t.tap(botaoEntregar);
      await t.tap(botaoEntregar, warnIfMissed: false);
      await t.pumpAndSettle();

      expect(find.byType(AlertDialog), findsOneWidget);
    },
  );

  testWidgets(
    '[006] ABU-12: dois toques seguidos em confirmar enviam um único registro',
    (t) async {
      final api = await abrirHoje(t);
      api.portaoDaEntrega = Completer<void>();
      await preencherTudo(t);
      await tocarBotao(t, 'Entregar');

      await t.tap(confirmarEntrega);
      await t.tap(confirmarEntrega, warnIfMissed: false);
      await t.pump();
      await t.pump(const Duration(milliseconds: 50));

      api.portaoDaEntrega!.complete();
      await t.pumpAndSettle();

      expect(api.chamadas.where((c) => c == 'entregarRegistro'), hasLength(1));
      expect(api.fotosEnviadas, 1);
      expect(find.text('Registro entregue'), findsOneWidget);
    },
  );

  testWidgets(
    '[006] ABU-12: enquanto o envio está pendente, Entregar não responde',
    (t) async {
      final api = await abrirHoje(t);
      api.portaoDaEntrega = Completer<void>();
      await preencherTudo(t);
      await tocarBotao(t, 'Entregar');
      await t.tap(confirmarEntrega);
      await t.pump();
      await t.pump(const Duration(milliseconds: 500));

      // a tela está em "enviando": nada de abrir outra confirmação nem de mexer no rascunho
      expect(find.byType(AlertDialog), findsNothing);
      final botao = find.byKey(const Key('botao-entregar'));
      if (botao.evaluate().isNotEmpty) {
        expect(entregarHabilitado(t), isFalse);
      }
      expect(find.textContaining('Enviando'), findsOneWidget);

      api.portaoDaEntrega!.complete();
      await t.pumpAndSettle();
      expect(api.chamadas.where((c) => c == 'entregarRegistro'), hasLength(1));
    },
  );

  testWidgets(
    '[006] ABU-12: dois toques em "Tentar de novo" enviam um único registro',
    (t) async {
      final api = await abrirHoje(t);
      api.falhaAoEntregar = const ErroApi(500);
      await preencherTudo(t);
      await tocarBotao(t, 'Entregar');
      await t.tap(confirmarEntrega);
      await t.pumpAndSettle();
      expect(api.chamadas.where((c) => c == 'entregarRegistro'), hasLength(1));

      api
        ..falhaAoEntregar = null
        ..portaoDaEntrega = Completer<void>();
      final tentar = find.widgetWithText(OutlinedButton, 'Tentar de novo');
      await t.ensureVisible(tentar);
      await t.tap(tentar);
      await t.tap(tentar, warnIfMissed: false);
      await t.pump();
      api.portaoDaEntrega!.complete();
      await t.pumpAndSettle();

      expect(api.chamadas.where((c) => c == 'entregarRegistro'), hasLength(2));
    },
  );
}
