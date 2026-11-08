// [011] US-22 (REQ-22.1 a 22.6, NFR-REC-3): "Esqueci minha senha", o pedido, a tela de senha nova e o link inválido.
import 'dart:async';

import 'package:entrelinhas/app/rotas.dart';
import 'package:entrelinhas/features/acesso/sessao.dart';
import 'package:entrelinhas/shared/api/api.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'suporte/api_falsa.dart';
import 'suporte/app_de_teste.dart';

const confirmacao =
    'Se este e-mail tiver conta, enviamos um link. Vale por 1 hora.';
const senhaNova = 'uma-senha-nova-bem-comprida-91';

Future<ApiFalsa> abrirEmRecuperacao(
  WidgetTester t, {
  ApiFalsa? api,
  Size tamanho = const Size(412, 900),
  Brightness brilho = Brightness.light,
}) async {
  final falsa = await abrirApp(t, api: api, tamanho: tamanho, brilho: brilho);
  await t.tap(find.text('Esqueci minha senha'));
  await t.pumpAndSettle();
  return falsa;
}

Future<ApiFalsa> abrirLink(
  WidgetTester t, {
  ApiFalsa? api,
  Size tamanho = const Size(412, 900),
  Brightness brilho = Brightness.light,
}) async {
  final falsa = await abrirApp(t, api: api, tamanho: tamanho, brilho: brilho);
  await irPara(t, '/redefinir/MTA/dhq-abc123token');
  return falsa;
}

String rotaAtual(WidgetTester t) {
  final container = ProviderScope.containerOf(
    t.element(find.byType(Scaffold).first),
  );
  final roteador = container.read(roteadorProvider);
  return roteador.routerDelegate.currentConfiguration.uri.toString();
}

Future<void> preencherSenhas(
  WidgetTester t, {
  String nova = senhaNova,
  String? confirmar,
}) async {
  await t.enterText(campo('Nova senha'), nova);
  await t.enterText(campo('Confirmar nova senha'), confirmar ?? nova);
  await t.pump();
}

Finder botao(String rotulo) => find.widgetWithText(FilledButton, rotulo);

void main() {
  testWidgets(
    '[011] REQ-22.1: a tela de entrar mostra "Esqueci minha senha" e ele leva ao pedido',
    (t) async {
      await abrirApp(t);

      expect(find.text('Esqueci minha senha'), findsOneWidget);
      await t.tap(find.text('Esqueci minha senha'));
      await t.pumpAndSettle();

      expect(find.text('Recuperar senha'), findsOneWidget);
      expect(campo('E-mail'), findsOneWidget);
      expect(botao('Enviar link'), findsOneWidget);
    },
  );

  testWidgets('[011] REQ-22.2: o pedido mostra sempre a mesma confirmação', (
    t,
  ) async {
    final api = await abrirEmRecuperacao(t);

    await t.enterText(campo('E-mail'), '  Ana@Example.com ');
    await t.tap(botao('Enviar link'));
    await t.pumpAndSettle();

    expect(api.pedidosDeRecuperacao, [
      'Ana@Example.com',
    ], reason: 'sem os espaços das pontas');
    expect(find.text(confirmacao), findsOneWidget);
  });

  testWidgets(
    '[011] REQ-22.2: o app nunca diz se o e-mail existe (a confirmação não muda com o e-mail)',
    (t) async {
      final api = await abrirEmRecuperacao(t);

      for (final email in [
        'existe@example.com',
        'nao-existe@example.com',
        'lixo',
      ]) {
        await t.enterText(campo('E-mail'), email);
        await t.tap(botao('Enviar link'));
        await t.pumpAndSettle();

        expect(find.text(confirmacao), findsOneWidget, reason: email);
        expect(find.textContaining('não encontr'), findsNothing);
        expect(find.textContaining('não existe'), findsNothing);
      }
      expect(api.pedidosDeRecuperacao, hasLength(3));
    },
  );

  testWidgets('[011] REQ-22.2: e-mail vazio não vai ao servidor', (t) async {
    final api = await abrirEmRecuperacao(t);

    await t.tap(botao('Enviar link'));
    await t.pumpAndSettle();

    expect(find.text('Informe o seu e-mail.'), findsOneWidget);
    expect(api.pedidosDeRecuperacao, isEmpty);
  });

  testWidgets(
    '[011] REQ-22.2: sem conexão o app diz só isso, sem fingir confirmação',
    (t) async {
      final api = ApiFalsa()..falhaAoPedirRecuperacao = const ErroApi(0);
      await abrirEmRecuperacao(t, api: api);

      await t.enterText(campo('E-mail'), 'ana@example.com');
      await t.tap(botao('Enviar link'));
      await t.pumpAndSettle();

      expect(
        find.text('Sem conexão com o servidor. Tente de novo.'),
        findsOneWidget,
      );
      expect(find.text(confirmacao), findsNothing);
    },
  );

  testWidgets(
    '[011] REQ-22.2: muitas tentativas (429 do proxy) têm mensagem própria',
    (t) async {
      final api = ApiFalsa()..falhaAoPedirRecuperacao = const ErroApi(429);
      await abrirEmRecuperacao(t, api: api);

      await t.enterText(campo('E-mail'), 'ana@example.com');
      await t.tap(botao('Enviar link'));
      await t.pumpAndSettle();

      expect(
        find.text('Muitas tentativas. Espere um minuto e tente de novo.'),
        findsOneWidget,
      );
    },
  );

  testWidgets('[011] ABU-25: dois toques em Enviar link mandam um pedido só', (
    t,
  ) async {
    final api = await abrirEmRecuperacao(t);
    api.portaoDoPedido = Completer<void>();
    await t.enterText(campo('E-mail'), 'ana@example.com');

    await t.tap(botao('Enviar link'));
    await t.tap(botao('Enviar link'), warnIfMissed: false);
    await t.pump();
    api.portaoDoPedido!.complete();
    await t.pumpAndSettle();

    expect(api.pedidosDeRecuperacao, hasLength(1));
  });

  testWidgets(
    '[011] REQ-22.3: o link abre a tela de senha nova e tira o token da barra de endereço',
    (t) async {
      await abrirLink(t);

      expect(find.text('Nova senha'), findsWidgets);
      expect(campo('Nova senha'), findsOneWidget);
      expect(campo('Confirmar nova senha'), findsOneWidget);
      expect(rotaAtual(t), '/redefinir');
      expect(rotaAtual(t), isNot(contains('token')));
    },
  );

  testWidgets(
    '[011] REQ-22.3: concluir leva à tela de entrar com a mensagem de sucesso',
    (t) async {
      final api = await abrirLink(t);

      await preencherSenhas(t);
      await t.tap(botao('Trocar senha'));
      await t.pumpAndSettle();

      expect(api.ultimaRedefinicao, {
        'uid': 'MTA',
        'token': 'dhq-abc123token',
        'nova_senha': senhaNova,
      });
      expect(
        find.text('Senha trocada. Entre com a nova senha.'),
        findsOneWidget,
      );
      expect(find.widgetWithText(FilledButton, 'Entrar'), findsOneWidget);
      expect(rotaAtual(t), '/entrar');
    },
  );

  testWidgets('[011] REQ-22.3: o app não entra sozinho depois de redefinir', (
    t,
  ) async {
    final api = await abrirLink(t);

    await preencherSenhas(t);
    await t.tap(botao('Trocar senha'));
    await t.pumpAndSettle();

    expect(api.sessao, isNull);
    expect(api.chamadas, isNot(contains(startsWith('entrar:'))));
  });

  testWidgets('[011] REQ-22.3: senhas diferentes não vão ao servidor', (
    t,
  ) async {
    final api = await abrirLink(t);

    await preencherSenhas(t, confirmar: 'outra-coisa-bem-diferente-12');
    await t.tap(botao('Trocar senha'));
    await t.pumpAndSettle();

    expect(find.text('As senhas não são iguais.'), findsOneWidget);
    expect(api.ultimaRedefinicao, isEmpty);
  });

  testWidgets('[011] REQ-22.3: dá para mostrar e ocultar a senha', (t) async {
    await abrirLink(t);

    EditableText campoDaSenha() => t.widget<EditableText>(
      find.descendant(
        of: campo('Nova senha'),
        matching: find.byType(EditableText),
      ),
    );
    expect(campoDaSenha().obscureText, isTrue);

    await t.tap(find.byTooltip('Mostrar a senha').first);
    await t.pumpAndSettle();
    expect(campoDaSenha().obscureText, isFalse);

    await t.tap(find.byTooltip('Ocultar a senha').first);
    await t.pumpAndSettle();
    expect(campoDaSenha().obscureText, isTrue);
  });

  testWidgets(
    '[011] REQ-22.4: link inválido ou vencido (400) mostra a mensagem e o botão de pedir outro',
    (t) async {
      final api = ApiFalsa()
        ..falhaAoRedefinir = const ErroApi(
          400,
          detalhe: 'Link inválido ou vencido.',
        );
      await abrirLink(t, api: api);

      await preencherSenhas(t);
      await t.tap(botao('Trocar senha'));
      await t.pumpAndSettle();

      expect(find.text('Link inválido ou vencido.'), findsOneWidget);
      expect(botao('Pedir outro link'), findsOneWidget);

      await t.tap(botao('Pedir outro link'));
      await t.pumpAndSettle();
      expect(find.text('Recuperar senha'), findsOneWidget);
    },
  );

  testWidgets(
    '[011] REQ-22.4: abrir a tela de senha nova sem token (recarregou a página) mostra link inválido',
    (t) async {
      await abrirApp(t);

      await irPara(t, '/redefinir');

      expect(find.text('Link inválido ou vencido.'), findsOneWidget);
      expect(botao('Pedir outro link'), findsOneWidget);
    },
  );

  testWidgets(
    '[011] REQ-22.5: senha recusada pelo servidor aparece em português, sem detalhe técnico, e o link continua',
    (t) async {
      final api = ApiFalsa()
        ..falhaAoRedefinir = const ErroApi(
          422,
          campos: {
            'nova_senha': [
              'Esta senha é muito curta. Ela precisa conter pelo menos 12 caracteres.',
            ],
          },
        );
      await abrirLink(t, api: api);

      await preencherSenhas(t);
      await t.tap(botao('Trocar senha'));
      await t.pumpAndSettle();

      expect(
        find.text(
          'Esta senha é muito curta. Ela precisa conter pelo menos 12 caracteres.',
        ),
        findsOneWidget,
      );
      expect(find.textContaining('Exception'), findsNothing);
      expect(
        campo('Nova senha'),
        findsOneWidget,
        reason: 'o token continua valendo: dá para tentar de novo',
      );
    },
  );

  testWidgets('[011] ABU-26: dois toques em Trocar senha mandam um pedido só', (
    t,
  ) async {
    final api = await abrirLink(t);
    api.portaoDaRedefinicao = Completer<void>();
    await preencherSenhas(t);

    await t.tap(botao('Trocar senha'));
    await t.tap(botao('Trocar senha'), warnIfMissed: false);
    await t.pump();
    api.portaoDaRedefinicao!.complete();
    await t.pumpAndSettle();

    expect(api.chamadas.where((c) => c == 'redefinirSenha'), hasLength(1));
  });

  testWidgets('[011] REQ-22.6: o token não aparece em nenhum texto da tela', (
    t,
  ) async {
    await abrirLink(t);

    expect(find.textContaining('dhq-abc123token'), findsNothing);
    expect(find.textContaining('MTA'), findsNothing);
  });

  testWidgets(
    '[011] REQ-22.6: a mensagem de sucesso não fica na sessão depois de entrar',
    (t) async {
      final api = await abrirLink(t);
      await preencherSenhas(t);
      await t.tap(botao('Trocar senha'));
      await t.pumpAndSettle();
      expect(
        find.text('Senha trocada. Entre com a nova senha.'),
        findsOneWidget,
      );

      api.sessao = null;
      await t.enterText(campo('E-mail'), 'ana@example.com');
      await t.enterText(campo('Senha'), senhaNova);
      await t.tap(find.widgetWithText(FilledButton, 'Entrar'));
      await t.pumpAndSettle();

      final container = ProviderScope.containerOf(
        t.element(find.byType(Scaffold).first),
      );
      expect(container.read(avisoDaSessaoProvider), isNull);
    },
  );

  testWidgets(
    '[011] REQ-22.1: quem já está logado não vê as telas de recuperação',
    (t) async {
      await abrirApp(t, api: ApiFalsa(sessao: perfilCompleto()));

      await irPara(t, '/recuperar');

      expect(find.text('Recuperar senha'), findsNothing);
    },
  );
}
