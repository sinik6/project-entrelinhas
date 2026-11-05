// [003] Criar conta pelo link do convite (REQ-5.2, REQ-5.4).
import 'package:entrelinhas/shared/api/api.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'suporte/api_falsa.dart';
import 'suporte/app_de_teste.dart';

Future<void> preencherEEnviar(WidgetTester t, {String cor = corAmbar}) async {
  await t.enterText(campo('Nome'), 'Bia');
  await t.enterText(campo('E-mail'), 'bia@example.com');
  await t.enterText(campo('Senha'), 'outra-senha-longa-demais-9');
  await t.enterText(campo('Cor (#RRGGBB)'), cor);
  await t.ensureVisible(
    find.widgetWithText(FilledButton, 'Criar conta e entrar'),
  );
  await t.tap(find.widgetWithText(FilledButton, 'Criar conta e entrar'));
  await t.pumpAndSettle();
}

void main() {
  testWidgets('[003] REQ-5.2: o link do convite abre a criação de conta', (
    t,
  ) async {
    await abrirApp(t);

    await irPara(t, '/convite/abc123');

    expect(find.text('Criar conta'), findsWidgets);
    for (final rotulo in ['Nome', 'E-mail', 'Senha', 'Cor (#RRGGBB)']) {
      expect(campo(rotulo), findsOneWidget, reason: rotulo);
    }
  });

  testWidgets(
    '[003] REQ-5.2: criar a conta manda o código do link e leva ao grupo',
    (t) async {
      final api = await abrirApp(t);
      await irPara(t, '/convite/abc123');

      await preencherEEnviar(t);

      expect(api.ultimoAceite, {
        'codigo': 'abc123',
        'nome': 'Bia',
        'email': 'bia@example.com',
        'senha': 'outra-senha-longa-demais-9',
        'cor': corAmbar,
      });
      expect(find.text('Seu grupo'), findsOneWidget);
      expect(find.text('Dono'), findsOneWidget);
      expect(find.text('Bia'), findsOneWidget);
    },
  );

  testWidgets(
    '[003] REQ-5.4: erro de cor do servidor aparece no campo, em português',
    (t) async {
      final api = ApiFalsa()
        ..falhaAoAceitar = const ErroApi(
          422,
          campos: {
            'cor': [
              'Essa cor fica ilegível no tema claro ou no escuro. Escolha outra.',
            ],
          },
        );
      await abrirApp(t, api: api);
      await irPara(t, '/convite/abc123');

      await preencherEEnviar(t, cor: '#FFFFFF');

      expect(
        find.text(
          'Essa cor fica ilegível no tema claro ou no escuro. Escolha outra.',
        ),
        findsOneWidget,
      );
      expect(
        find.text('Criar conta'),
        findsWidgets,
        reason: 'continua na tela de criar conta',
      );
    },
  );

  testWidgets(
    '[003] REQ-5.4: convite inválido usa a mensagem única do servidor',
    (t) async {
      final api = ApiFalsa()
        ..falhaAoAceitar = const ErroApi(
          400,
          detalhe: 'Não foi possível usar este convite.',
        );
      await abrirApp(t, api: api);
      await irPara(t, '/convite/abc123');

      await preencherEEnviar(t);

      expect(find.text('Não foi possível usar este convite.'), findsOneWidget);
    },
  );

  testWidgets('[003] REQ-5.2: quem já entrou não vê a tela de convite', (
    t,
  ) async {
    await abrirApp(t, api: ApiFalsa(sessao: perfilCompleto()));

    await irPara(t, '/convite/abc123');

    expect(find.text('Você ainda não tem um grupo.'), findsOneWidget);
    expect(campo('Nome'), findsNothing);
  });
}
