// [009] US-17 (REQ-17.1 a 17.6): a grade do mês com marcadores por membro, legenda, navegação limitada e lista do dia.
import 'package:entrelinhas/features/calendario/marcador.dart';
import 'package:entrelinhas/features/calendario/modelos.dart';
import 'package:entrelinhas/shared/api/api.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'suporte/api_falsa.dart';
import 'suporte/app_de_teste.dart';
import 'suporte/hoje_de_teste.dart';

DiaDoCalendario dia(
  int d, {
  List<String> estados = const ['escreveu', 'escreveu'],
  bool juntos = false,
  int mes = 11,
}) => DiaDoCalendario(
  data: DateTime(2026, mes, d),
  estados: estados,
  juntos: juntos,
);

/// Novembro de 2026 até o dia 6: 1 juntos, 2 só a Ana, 3 falhas, 4 e 5 a Bia ainda fora, 6 pendente.
Calendario novembro() => calendarioDe([
  dia(1, juntos: true),
  dia(2, estados: ['escreveu', 'falhou']),
  dia(3, estados: ['falhou', 'falhou']),
  dia(4, estados: ['escreveu', 'fora']),
  dia(5, estados: ['escreveu', 'fora']),
  dia(6, estados: ['pendente', 'pendente']),
]);

Future<ApiFalsa> abrirCalendario(
  WidgetTester t, {
  ApiFalsa? api,
  Size tamanho = const Size(412, 900),
  Brightness brilho = Brightness.light,
}) async {
  final falsa = api ?? apiDaAna();
  if (falsa.calendarios.isEmpty && falsa.falhaAoCalendario == null) {
    falsa.calendarios['2026-11'] = novembro();
  }
  await abrirApp(t, api: falsa, tamanho: tamanho, brilho: brilho);
  await irPara(t, '/calendario');
  return falsa;
}

Finder celula(String chave) => find.byKey(Key('dia-$chave'));

MarcadorDeEstado marcador(WidgetTester t, String chave, int i) =>
    t.widget<MarcadorDeEstado>(find.byKey(Key('marcador-$chave-$i')));

void main() {
  testWidgets('[009] REQ-17.1: abre no mês atual com a grade até hoje', (
    t,
  ) async {
    final api = await abrirCalendario(t);

    expect(api.chamadas, contains('calendario:2026-11'));
    expect(find.text('novembro de 2026'), findsOneWidget);
    for (final d in ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb']) {
      expect(find.text(d), findsOneWidget);
    }
    expect(celula('2026-11-01'), findsOneWidget);
    expect(celula('2026-11-06'), findsOneWidget);
    expect(celula('2026-11-07'), findsNothing, reason: 'o futuro não aparece');
  });

  testWidgets(
    '[009] REQ-17.1: 1º de novembro de 2026 cai num domingo (primeira coluna)',
    (t) async {
      await abrirCalendario(t);

      final primeiro = t.getTopLeft(celula('2026-11-01')).dx;
      final segundo = t.getTopLeft(celula('2026-11-02')).dx;
      final domingoSeguinte = t.getTopLeft(find.text('dom')).dx;
      expect(primeiro, lessThan(segundo));
      expect((primeiro - domingoSeguinte).abs(), lessThan(40));
    },
  );

  testWidgets(
    '[009] REQ-17.2: um marcador por membro, no estado e na cor dele',
    (t) async {
      await abrirCalendario(t);

      expect(marcador(t, '2026-11-02', 0).estado, EstadoDoDia.escreveu);
      expect(marcador(t, '2026-11-02', 1).estado, EstadoDoDia.falhou);
      expect(marcador(t, '2026-11-06', 0).estado, EstadoDoDia.pendente);
      expect(marcador(t, '2026-11-02', 0).cor, const Color(0xFF4D7C0F));
      expect(marcador(t, '2026-11-02', 1).cor, const Color(0xFFB45309));
    },
  );

  testWidgets('[009] REQ-17.2: quem ainda estava fora não tem marcador', (
    t,
  ) async {
    await abrirCalendario(t);

    expect(find.byKey(const Key('marcador-2026-11-04-1')), findsNothing);
    expect(find.byKey(const Key('marcador-2026-11-04-0')), findsOneWidget);
  });

  testWidgets('[009] REQ-17.2: o selo "juntos" só aparece no dia certo', (
    t,
  ) async {
    await abrirCalendario(t);

    expect(find.byKey(const Key('selo-juntos-2026-11-01')), findsOneWidget);
    expect(find.byKey(const Key('selo-juntos-2026-11-02')), findsNothing);
  });

  test(
    '[009] REQ-17.3: cada estado tem forma própria (a cor não carrega sozinha)',
    () {
      final formas = {
        for (final e in [
          EstadoDoDia.escreveu,
          EstadoDoDia.falhou,
          EstadoDoDia.pendente,
        ])
          MarcadorDeEstado.formaDe(e),
      };

      expect(formas, hasLength(3));
      expect(
        MarcadorDeEstado.formaDe(EstadoDoDia.fora),
        FormaDoMarcador.nenhuma,
      );
    },
  );

  testWidgets(
    '[009] REQ-17.3: texto alternativo de cada dia diz o estado de cada pessoa',
    (t) async {
      final semantica = t.ensureSemantics();
      await abrirCalendario(t);

      String rotulo(String chave) => t.getSemantics(celula(chave)).label;

      expect(
        rotulo('2026-11-01'),
        'Dia 1: Ana escreveu; Bia escreveu; escreveram juntos',
      );
      expect(rotulo('2026-11-02'), 'Dia 2: Ana escreveu; Bia não escreveu');
      expect(
        rotulo('2026-11-04'),
        'Dia 4: Ana escreveu; Bia ainda não estava no grupo',
      );
      expect(
        rotulo('2026-11-06'),
        'Dia 6: Ana ainda não escreveu; Bia ainda não escreveu',
      );
      semantica.dispose();
    },
  );

  testWidgets('[009] REQ-17.5: a legenda explica cada marcador', (t) async {
    await abrirCalendario(t);

    final legenda = find.byKey(const Key('legenda'));
    for (final texto in [
      'Escreveu',
      'Não escreveu',
      'Ainda dá tempo (hoje)',
      'Escreveram juntos',
      'Em branco: antes de entrar no grupo',
    ]) {
      expect(
        find.descendant(of: legenda, matching: find.text(texto)),
        findsOneWidget,
        reason: texto,
      );
    }
  });

  testWidgets(
    '[009] REQ-17.1: não passa do mês atual e volta ao mês anterior',
    (t) async {
      final api = apiDaAna();
      api.calendarios['2026-11'] = novembro();
      api.calendarios['2026-10'] = calendarioDe([
        DiaDoCalendario(
          data: DateTime(2026, 10, 31),
          estados: const ['escreveu', 'falhou'],
          juntos: false,
        ),
      ], mes: '2026-10');
      await abrirCalendario(t, api: api);

      final proximo = find.byWidgetPredicate(
        (w) => w is IconButton && w.tooltip == 'Mês seguinte',
      );
      expect(t.widget<IconButton>(proximo).onPressed, isNull);

      await t.tap(
        find.byWidgetPredicate(
          (w) => w is IconButton && w.tooltip == 'Mês anterior',
        ),
      );
      await t.pumpAndSettle();

      expect(find.text('outubro de 2026'), findsOneWidget);
      expect(celula('2026-10-31'), findsOneWidget);
      expect(t.widget<IconButton>(proximo).onPressed, isNotNull);
    },
  );

  testWidgets(
    '[009] REQ-17.1: o mês anterior à entrada do grupo (422) fica de fora e o botão desabilita',
    (t) async {
      final api = await abrirCalendario(t);

      final anterior = find.byWidgetPredicate(
        (w) => w is IconButton && w.tooltip == 'Mês anterior',
      );
      await t.tap(anterior);
      await t.pumpAndSettle();

      expect(find.text('novembro de 2026'), findsOneWidget);
      expect(api.chamadas, contains('calendario:2026-10'));
      expect(t.widget<IconButton>(anterior).onPressed, isNull);
      expect(find.textContaining('ainda não existia'), findsNothing);
    },
  );

  testWidgets('[009] REQ-17.4: tocar num dia abre os registros daquele dia', (
    t,
  ) async {
    final api = apiDaAna()
      ..registros.addAll([
        registroDe(
          id: 'a',
          data: '2026-11-02',
          entregueEm: DateTime.utc(2026, 11, 2, 15),
          texto: 'O dia dois da Ana, inteiro.',
          fotos: const [],
        ),
        registroDe(
          id: 'b',
          nome: 'Bia',
          meu: false,
          data: '2026-11-03',
          entregueEm: DateTime.utc(2026, 11, 3, 15),
          texto: 'O dia três da Bia.',
          fotos: const [],
        ),
      ]);
    await abrirCalendario(t, api: api);

    await t.tap(celula('2026-11-02'));
    await t.pumpAndSettle();

    final folha = find.byKey(const Key('folha-do-dia'));
    expect(folha, findsOneWidget);
    expect(
      find.descendant(
        of: folha,
        matching: find.text('O dia dois da Ana, inteiro.'),
      ),
      findsOneWidget,
    );
    expect(
      find.descendant(of: folha, matching: find.text('O dia três da Bia.')),
      findsNothing,
    );
    expect(api.chamadas, contains('listarRegistros:2026-11'));
  });

  testWidgets(
    '[009] REQ-17.4: dia sem registro mostra "Nenhum registro neste dia"',
    (t) async {
      await abrirCalendario(t);

      await t.tap(celula('2026-11-03'));
      await t.pumpAndSettle();

      expect(find.text('Nenhum registro neste dia.'), findsOneWidget);
    },
  );

  testWidgets(
    '[009] REQ-17.6: erro do servidor aparece em português com "Tentar de novo"',
    (t) async {
      final api = apiDaAna()..falhaAoCalendario = const ErroApi(500);
      await abrirCalendario(t, api: api);

      expect(
        find.text('O servidor teve um problema. Tente de novo em instantes.'),
        findsOneWidget,
      );

      api
        ..falhaAoCalendario = null
        ..calendarios['2026-11'] = novembro();
      await tocarBotao(t, 'Tentar de novo');

      expect(celula('2026-11-01'), findsOneWidget);
    },
  );

  testWidgets('[009] REQ-17.6: sessão que acabou leva à tela de entrar', (
    t,
  ) async {
    final api = apiDaAna()..falhaAoCalendario = const ErroApi(401);
    await abrirCalendario(t, api: api);

    expect(find.text('Sua sessão acabou. Entre de novo.'), findsOneWidget);
  });

  testWidgets('[009] REQ-17.1: sem grupo, o Calendário leva ao Grupo', (
    t,
  ) async {
    await abrirApp(t, api: ApiFalsa(sessao: perfilCompleto()));

    await irPara(t, '/calendario');

    expect(find.byKey(const Key('pagina-do-grupo')), findsOneWidget);
  });

  testWidgets('[009] REQ-17.1: o menu tem os cinco destinos, com Calendário', (
    t,
  ) async {
    await abrirCalendario(t);

    for (final rotulo in ['Hoje', 'Diário', 'Calendário', 'Grupo', 'Perfil']) {
      expect(
        find.descendant(
          of: find.byType(NavigationBar),
          matching: find.text(rotulo),
        ),
        findsOneWidget,
        reason: rotulo,
      );
    }
  });
}
