// [003] Perfil e troca de senha (REQ-5.3, REQ-5.4).
import 'package:entrelinhas/shared/api/api.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'suporte/api_falsa.dart';
import 'suporte/app_de_teste.dart';

Future<ApiFalsa> abrirPerfil(WidgetTester t, {ApiFalsa? api}) async {
  final falsa = await abrirApp(
    t,
    api: api ?? ApiFalsa(sessao: perfilCompleto()),
  );
  await t.tap(
    find.descendant(
      of: find.byType(NavigationBar),
      matching: find.text('Perfil'),
    ),
  );
  await t.pumpAndSettle();
  return falsa;
}

Future<void> tocar(WidgetTester t, String texto) async {
  final botao = find.widgetWithText(FilledButton, texto);
  await t.ensureVisible(botao);
  await t.tap(botao);
  await t.pumpAndSettle();
}

void main() {
  testWidgets('[003] REQ-5.3: o perfil mostra nome e cor da pessoa', (t) async {
    await abrirPerfil(t);

    expect(find.text('Seu perfil'), findsOneWidget);
    expect(
      find.descendant(of: campo('Nome'), matching: find.text('Ana')),
      findsOneWidget,
    );
    expect(
      find.descendant(
        of: campo('Cor (#RRGGBB)'),
        matching: find.text(corVerde),
      ),
      findsOneWidget,
    );
  });

  testWidgets('[003] REQ-5.3: salvar manda nome e cor e confirma', (t) async {
    final api = await abrirPerfil(t);

    await t.enterText(campo('Nome'), 'Ana Maria');
    await t.enterText(campo('Cor (#RRGGBB)'), corAmbar);
    await tocar(t, 'Salvar');

    expect(api.ultimoPerfilEnviado, {'nome': 'Ana Maria', 'cor': corAmbar});
    expect(find.text('Perfil salvo.'), findsOneWidget);
  });

  testWidgets('[003] REQ-5.4: a cor recusada pelo servidor aparece no campo', (
    t,
  ) async {
    final api = ApiFalsa(sessao: perfilCompleto())
      ..falhaAoAtualizar = const ErroApi(
        422,
        campos: {
          'cor': [
            'Essa cor é igual ou parecida demais com a da outra pessoa do grupo.',
          ],
        },
      );
    await abrirPerfil(t, api: api);

    await t.enterText(campo('Cor (#RRGGBB)'), corAmbar);
    await tocar(t, 'Salvar');

    expect(
      find.text(
        'Essa cor é igual ou parecida demais com a da outra pessoa do grupo.',
      ),
      findsOneWidget,
    );
    expect(find.text('Perfil salvo.'), findsNothing);
  });

  testWidgets('[003] REQ-5.4: senha atual errada aparece em português', (
    t,
  ) async {
    final api = ApiFalsa(sessao: perfilCompleto())
      ..falhaAoTrocarSenha = const ErroApi(
        422,
        campos: {
          'senha_atual': ['A senha atual está incorreta.'],
        },
      );
    await abrirPerfil(t, api: api);

    await t.enterText(campo('Senha atual'), 'errada-errada-errada');
    await t.enterText(campo('Nova senha'), 'outra-senha-longa-demais-9');
    await tocar(t, 'Trocar senha');

    expect(find.text('A senha atual está incorreta.'), findsOneWidget);
    expect(find.text('Senha trocada.'), findsNothing);
  });

  testWidgets('[003] REQ-5.3: trocar a senha confirma e limpa os campos', (
    t,
  ) async {
    final api = await abrirPerfil(t);

    await t.enterText(campo('Senha atual'), 'correta-cavalo-bateria-7');
    await t.enterText(campo('Nova senha'), 'outra-senha-longa-demais-9');
    await tocar(t, 'Trocar senha');

    expect(api.chamadas, contains('trocarSenha'));
    expect(find.text('Senha trocada.'), findsOneWidget);
    expect(
      find.descendant(
        of: campo('Nova senha'),
        matching: find.text('outra-senha-longa-demais-9'),
      ),
      findsNothing,
    );
  });

  testWidgets('[003] REQ-5.1: sair volta para a tela de entrar', (t) async {
    final api = await abrirPerfil(t);

    await t.tap(find.widgetWithText(TextButton, 'Sair'));
    await t.pumpAndSettle();

    expect(api.chamadas, contains('sair'));
    expect(find.widgetWithText(FilledButton, 'Entrar'), findsOneWidget);
  });
}
