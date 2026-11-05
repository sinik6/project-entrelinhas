// [003] Grupo e convite (REQ-5.3, REQ-5.4).
import 'package:entrelinhas/shared/api/api.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'suporte/api_falsa.dart';
import 'suporte/app_de_teste.dart';

const ana = Membro(nome: 'Ana', cor: corVerde);
const bia = Membro(nome: 'Bia', cor: corAmbar);

void main() {
  testWidgets(
    '[003] REQ-5.3: sem grupo oferece criar e, criado, mostra a pessoa como único membro',
    (t) async {
      final api = await abrirApp(t, api: ApiFalsa(sessao: perfilCompleto()));
      expect(find.text('Você ainda não tem um grupo.'), findsOneWidget);

      await t.tap(find.widgetWithText(FilledButton, 'Criar grupo'));
      await t.pumpAndSettle();

      expect(api.chamadas, contains('criarGrupo'));
      expect(find.text('Seu grupo'), findsOneWidget);
      expect(find.text('Ana'), findsOneWidget);
    },
  );

  testWidgets('[003] REQ-5.3: mostra nome e cor de cada membro', (t) async {
    final api = ApiFalsa(sessao: perfilCompleto())
      ..grupoAtual = grupoCom([ana, bia]);
    await abrirApp(t, api: api);

    expect(find.text('Ana'), findsOneWidget);
    expect(find.text('Bia'), findsOneWidget);
    final amostra = t.widget<Container>(
      find.byKey(const Key('cor-membro-Bia')),
    );
    expect(
      (amostra.decoration! as BoxDecoration).color,
      const Color(0xFFB45309),
    );
  });

  testWidgets('[003] REQ-5.3: havendo vaga mostra o botão de convidar', (
    t,
  ) async {
    final api = ApiFalsa(sessao: perfilCompleto())
      ..grupoAtual = grupoCom([ana]);
    await abrirApp(t, api: api);

    expect(
      find.widgetWithText(FilledButton, 'Convidar a outra pessoa'),
      findsOneWidget,
    );
  });

  testWidgets('[003] REQ-5.3: sem vaga não mostra o botão de convidar', (
    t,
  ) async {
    final api = ApiFalsa(sessao: perfilCompleto())
      ..grupoAtual = grupoCom([ana, bia]);
    await abrirApp(t, api: api);

    expect(find.text('Bia'), findsOneWidget);
    expect(
      find.widgetWithText(FilledButton, 'Convidar a outra pessoa'),
      findsNothing,
    );
  });

  testWidgets(
    '[003] REQ-5.3: convidar mostra o link com o código e a validade',
    (t) async {
      final api = ApiFalsa(sessao: perfilCompleto())
        ..grupoAtual = grupoCom([ana]);
      await abrirApp(t, api: api);

      await t.tap(find.widgetWithText(FilledButton, 'Convidar a outra pessoa'));
      await t.pumpAndSettle();

      expect(api.chamadas, contains('gerarConvite'));
      expect(find.text('Link do convite'), findsOneWidget);
      expect(
        find.textContaining(
          'https://exemplo.org/entrelinhas/#/convite/CODIGO123',
        ),
        findsOneWidget,
      );
      expect(find.textContaining('Vale até'), findsOneWidget);
      expect(
        find.widgetWithText(OutlinedButton, 'Copiar link'),
        findsOneWidget,
      );
    },
  );

  testWidgets(
    '[003] REQ-5.4: grupo cheio no servidor aparece em português, sem detalhe técnico',
    (t) async {
      final api = ApiFalsa(sessao: perfilCompleto())
        ..grupoAtual = grupoCom([ana])
        ..falhaAoConvidar = const ErroApi(
          409,
          detalhe: 'O grupo já está completo.',
        );
      await abrirApp(t, api: api);

      await t.tap(find.widgetWithText(FilledButton, 'Convidar a outra pessoa'));
      await t.pumpAndSettle();

      expect(find.text('O grupo já está completo.'), findsOneWidget);
      expect(find.textContaining('Exception'), findsNothing);
    },
  );

  testWidgets(
    '[003] REQ-5.4: sessão que acabou leva de volta à tela de entrar',
    (t) async {
      final api = ApiFalsa(sessao: perfilCompleto())
        ..grupoAtual = grupoCom([ana])
        ..falhaAoConvidar = const ErroApi(401);
      await abrirApp(t, api: api);

      await t.tap(find.widgetWithText(FilledButton, 'Convidar a outra pessoa'));
      await t.pumpAndSettle();

      expect(find.text('Sua sessão acabou. Entre de novo.'), findsOneWidget);
    },
  );
}
