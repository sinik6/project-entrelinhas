// [003] Tela de entrar (REQ-5.1, REQ-5.4, REQ-5.5).
import 'package:entrelinhas/shared/api/api.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'suporte/api_falsa.dart';
import 'suporte/app_de_teste.dart';

Future<void> preencherEEntrar(
  WidgetTester t, {
  String email = 'ana@example.com',
  String senha = 'correta-cavalo-bateria-7',
}) async {
  await t.enterText(campo('E-mail'), email);
  await t.enterText(campo('Senha'), senha);
  await t.tap(find.widgetWithText(FilledButton, 'Entrar'));
  await t.pumpAndSettle();
}

void main() {
  testWidgets('[003] REQ-5.1: sem sessão o app mostra a tela de entrar', (
    t,
  ) async {
    await abrirApp(t);

    expect(find.text('Entrar'), findsWidgets);
    expect(campo('E-mail'), findsOneWidget);
    expect(campo('Senha'), findsOneWidget);
    expect(find.widgetWithText(FilledButton, 'Entrar'), findsOneWidget);
  });

  testWidgets('[003] REQ-5.1: com sessão aberta o app vai direto ao grupo', (
    t,
  ) async {
    await abrirApp(t, api: ApiFalsa(sessao: perfilCompleto()));

    expect(find.text('Você ainda não tem um grupo.'), findsOneWidget);
    expect(find.widgetWithText(FilledButton, 'Entrar'), findsNothing);
  });

  testWidgets('[003] REQ-5.3: entrar com perfil completo mostra o grupo', (
    t,
  ) async {
    final api = await abrirApp(t);

    await preencherEEntrar(t);

    expect(api.chamadas, contains('entrar:ana@example.com'));
    expect(find.text('Você ainda não tem um grupo.'), findsOneWidget);
  });

  testWidgets(
    '[003] REQ-5.5: perfil incompleto leva ao perfil antes de qualquer outra tela',
    (t) async {
      final api = ApiFalsa()..perfilDoLogin = perfilIncompleto;
      await abrirApp(t, api: api);

      await preencherEEntrar(t, email: 'dono@example.com');

      expect(find.text('Seu perfil'), findsOneWidget);
      expect(
        find.text('Informe seu nome e escolha uma cor para continuar.'),
        findsOneWidget,
      );
      await irPara(t, '/grupo');
      expect(
        find.text('Seu perfil'),
        findsOneWidget,
        reason: 'sem perfil completo não há outra tela',
      );
    },
  );

  testWidgets('[003] REQ-5.4: e-mail ou senha errados aparecem em português', (
    t,
  ) async {
    final api = ApiFalsa()
      ..falhaAoEntrar = const ErroApi(
        400,
        detalhe: 'E-mail ou senha incorretos.',
      );
    await abrirApp(t, api: api);

    await preencherEEntrar(t);

    expect(find.text('E-mail ou senha incorretos.'), findsOneWidget);
    expect(
      find.text('Entrar'),
      findsWidgets,
      reason: 'continua na tela de entrar',
    );
  });

  testWidgets(
    '[003] REQ-5.4: sem conexão e excesso de tentativas, sem detalhe técnico',
    (t) async {
      final api = ApiFalsa()..falhaAoEntrar = const ErroApi(0);
      await abrirApp(t, api: api);

      await preencherEEntrar(t);
      expect(
        find.text('Sem conexão com o servidor. Tente de novo.'),
        findsOneWidget,
      );

      api.falhaAoEntrar = const ErroApi(429);
      await t.tap(find.widgetWithText(FilledButton, 'Entrar'));
      await t.pumpAndSettle();
      expect(
        find.text('Muitas tentativas. Espere um minuto e tente de novo.'),
        findsOneWidget,
      );
      expect(find.textContaining('Exception'), findsNothing);
      expect(find.textContaining('Dio'), findsNothing);
    },
  );
}
