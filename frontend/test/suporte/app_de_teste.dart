import 'package:entrelinhas/app/app.dart';
import 'package:entrelinhas/app/rotas.dart';
import 'package:entrelinhas/features/grupo/link_do_convite.dart';
import 'package:entrelinhas/shared/api/api.dart';
import 'package:entrelinhas/shared/foto/seletor_de_foto.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'api_falsa.dart';

const celular = Size(360, 740);
const computador = Size(1280, 800);

/// Abre o app inteiro (com o roteador de verdade) sobre uma API de mentira.
Future<ApiFalsa> abrirApp(
  WidgetTester tester, {
  ApiFalsa? api,
  SeletorDeFoto? seletor,
  Size tamanho = const Size(412, 900),
  Brightness brilho = Brightness.light,
}) async {
  final falsa = api ?? ApiFalsa();
  tester.view.physicalSize = tamanho;
  tester.view.devicePixelRatio = 1.0;
  tester.platformDispatcher.platformBrightnessTestValue = brilho;
  addTearDown(tester.view.reset);
  addTearDown(tester.platformDispatcher.clearPlatformBrightnessTestValue);
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        apiProvider.overrideWithValue(falsa),
        if (seletor != null) seletorDeFotoProvider.overrideWithValue(seletor),
        linkDoConviteProvider.overrideWithValue(
          (codigo) => 'https://exemplo.org/entrelinhas/#/convite/$codigo',
        ),
      ],
      child: const EntrelinhasApp(),
    ),
  );
  await tester.pumpAndSettle();
  return falsa;
}

/// Vai para uma rota do app, como se a pessoa tivesse aberto aquele endereço.
Future<void> irPara(WidgetTester tester, String rota) async {
  final container = ProviderScope.containerOf(
    tester.element(find.byType(EntrelinhasApp)),
  );
  container.read(roteadorProvider).go(rota);
  await tester.pumpAndSettle();
}

Finder campo(String rotulo) => find.widgetWithText(TextFormField, rotulo);
