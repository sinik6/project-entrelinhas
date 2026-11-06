// [006] US-12 (REQ-12.1 a 12.7), ABU-13, NFR-TELA-2, CTL-43: ler o diário do grupo, por mês, nas três visões.
import 'package:entrelinhas/features/hoje/modelos.dart';
import 'package:entrelinhas/shared/api/api.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'suporte/api_falsa.dart';
import 'suporte/app_de_teste.dart';
import 'suporte/hoje_de_teste.dart';

ApiFalsa apiComRegistros(List<Registro> registros) =>
    apiDaAna()..registros.addAll(registros);

/// Trechos do texto desenhados com fundo destacado (o trecho marcado, na visão do autor).
List<String> trechosMarcados(WidgetTester t, String id) {
  final texto = t.widget<Text>(find.byKey(Key('texto-$id')));
  final achados = <String>[];
  texto.textSpan!.visitChildren((span) {
    if (span is TextSpan && span.style?.backgroundColor != null) {
      achados.add(span.text ?? '');
    }
    return true;
  });
  return achados;
}

Finder botao(String dica) =>
    find.byWidgetPredicate((w) => w is IconButton && w.tooltip == dica);

String textoCompleto(WidgetTester t, String id) =>
    t.widget<Text>(find.byKey(Key('texto-$id'))).textSpan!.toPlainText();

void main() {
  testWidgets(
    '[006] REQ-12.1: abre no mês atual, do mais novo para o mais antigo',
    (t) async {
      final api = apiComRegistros([
        registroDe(
          id: 'velho',
          data: '2026-11-02',
          entregueEm: DateTime.utc(2026, 11, 2, 12),
          texto: 'Registro mais antigo do mês.',
        ),
        registroDe(id: 'novo', texto: 'Registro mais novo do mês.'),
        registroDe(
          id: 'outubro',
          data: '2026-10-30',
          entregueEm: DateTime.utc(2026, 10, 30, 12),
          texto: 'Registro de outubro.',
        ),
      ]);
      await abrirDiario(t, api: api);

      expect(api.chamadas, contains('listarRegistros:2026-11'));
      expect(find.text('novembro de 2026'), findsOneWidget);
      expect(find.text('Registro de outubro.'), findsNothing);
      final topo = t.getTopLeft(find.byKey(const Key('registro-novo'))).dy;
      final base = t.getTopLeft(find.byKey(const Key('registro-velho'))).dy;
      expect(topo, lessThan(base));
    },
  );

  testWidgets(
    '[006] REQ-12.1: vai ao mês anterior e volta; não passa do mês atual',
    (t) async {
      final api = apiComRegistros([
        registroDe(id: 'nov', texto: 'Registro de novembro.'),
        registroDe(
          id: 'out',
          data: '2026-10-30',
          entregueEm: DateTime.utc(2026, 10, 30, 12),
          texto: 'Registro de outubro.',
        ),
      ]);
      await abrirDiario(t, api: api);

      final proximo = botao('Mês seguinte');
      expect(t.widget<IconButton>(proximo).onPressed, isNull);

      await t.tap(botao('Mês anterior'));
      await t.pumpAndSettle();
      expect(find.text('outubro de 2026'), findsOneWidget);
      expect(find.text('Registro de outubro.'), findsOneWidget);
      expect(find.text('Registro de novembro.'), findsNothing);
      expect(api.chamadas, contains('listarRegistros:2026-10'));
      expect(t.widget<IconButton>(proximo).onPressed, isNotNull);

      await t.tap(proximo);
      await t.pumpAndSettle();
      expect(find.text('novembro de 2026'), findsOneWidget);
      expect(find.text('Registro de novembro.'), findsOneWidget);
      expect(t.widget<IconButton>(proximo).onPressed, isNull);
    },
  );

  testWidgets('[006] REQ-12.1: virada de ano ao voltar de janeiro', (t) async {
    final api = apiDaAna();
    await abrirApp0(t, api, DateTime.utc(2027, 1, 10, 15));
    await irPara(t, '/diario');

    await t.tap(botao('Mês anterior'));
    await t.pumpAndSettle();

    expect(find.text('dezembro de 2026'), findsOneWidget);
    expect(api.chamadas, contains('listarRegistros:2026-12'));
  });

  testWidgets(
    '[006] REQ-12.2: cada registro mostra quem escreveu (nome e cor), o dia e a hora da entrega',
    (t) async {
      final api = apiComRegistros([
        registroDe(
          id: 'b',
          nome: 'Bia',
          cor: corAmbar,
          meu: false,
          entregueEm: DateTime.utc(2026, 11, 5, 23, 15), // 20:15 em São Paulo
          data: '2026-11-05',
          texto: 'Da Bia, em dia de chuva.',
          fotos: const [],
        ),
      ]);
      await abrirDiario(t, api: api);

      final cartao = find.byKey(const Key('registro-b'));
      expect(
        find.descendant(of: cartao, matching: find.text('Bia')),
        findsOneWidget,
      );
      expect(
        find.descendant(of: cartao, matching: find.text('05/11 às 20:15')),
        findsOneWidget,
      );
      final faixa = t.widget<Container>(find.byKey(const Key('faixa-b')));
      expect(
        (faixa.decoration! as BoxDecoration).color,
        const Color(0xFFB45309),
      );
    },
  );

  testWidgets(
    '[006] REQ-12.3: registro da outra pessoa em "todo o grupo" mostra texto e fotos',
    (t) async {
      final api = apiComRegistros([
        registroDe(
          id: 'b',
          nome: 'Bia',
          meu: false,
          texto: 'Texto completo da Bia.',
          fotos: const ['f1', 'f2'],
        ),
      ]);
      await abrirDiario(t, api: api);

      expect(find.text('Texto completo da Bia.'), findsOneWidget);
      expect(find.byKey(const Key('foto-f1')), findsOneWidget);
      expect(find.byKey(const Key('foto-f2')), findsOneWidget);
      expect(find.textContaining('Mostrando só o trecho'), findsNothing);
    },
  );

  testWidgets(
    '[006] REQ-12.3: em trecho, mostra só o trecho e a nota com o nome',
    (t) async {
      final api = apiComRegistros([
        registroDe(
          id: 'b',
          nome: 'Bia',
          meu: false,
          visibilidade: Visibilidade.trecho,
          texto: 'só este pedaço',
          fotos: const [],
        ),
      ]);
      await abrirDiario(t, api: api);

      expect(find.text('só este pedaço'), findsOneWidget);
      expect(
        find.text('Mostrando só o trecho que Bia escolheu'),
        findsOneWidget,
      );
    },
  );

  testWidgets(
    '[006] REQ-12.3: em privado, mostra só o aviso, sem texto nem fotos',
    (t) async {
      final api = apiComRegistros([
        registroDe(
          id: 'b',
          nome: 'Bia',
          meu: false,
          visibilidade: Visibilidade.privado,
          texto: null,
          fotos: const [],
          aviso: 'Enviado, mas mantido privado pelo autor',
        ),
      ]);
      await abrirDiario(t, api: api);

      expect(
        find.text('Enviado, mas mantido privado pelo autor'),
        findsOneWidget,
      );
      expect(find.byKey(const Key('texto-b')), findsNothing);
      expect(find.byKey(const Key('foto-f1')), findsNothing);
    },
  );

  testWidgets(
    '[006] REQ-12.4: o próprio registro mostra o texto inteiro, quem pode ler e o trecho marcado',
    (t) async {
      final api = apiComRegistros([
        registroDe(
          id: 'a',
          visibilidade: Visibilidade.trecho,
          texto: 'Antes do meio, meio, depois do meio.',
          trecho: const Trecho(inicio: 15, fim: 20), // o segundo "meio,"
          fotos: const [],
        ),
      ]);
      await abrirDiario(t, api: api);

      expect(textoCompleto(t, 'a'), 'Antes do meio, meio, depois do meio.');
      expect(trechosMarcados(t, 'a'), ['meio,']);
      expect(find.text('Quem lê: só um trecho'), findsOneWidget);
    },
  );

  testWidgets(
    '[006] REQ-12.4: o trecho marcado converte pontos de código para o texto com emoji',
    (t) async {
      final api = apiComRegistros([
        registroDe(
          id: 'a',
          visibilidade: Visibilidade.trecho,
          texto: 'Oi 😀 tudo bem hoje, 😀 certo.',
          trecho: const Trecho(inicio: 5, fim: 18),
          fotos: const [],
        ),
      ]);
      await abrirDiario(t, api: api);

      expect(trechosMarcados(t, 'a'), ['tudo bem hoje']);
    },
  );

  testWidgets(
    '[006] REQ-12.3: na visão do parceiro nada é marcado, mesmo que um trecho apareça por engano',
    (t) async {
      final api = apiComRegistros([
        registroDe(
          id: 'b',
          nome: 'Bia',
          meu: false,
          visibilidade: Visibilidade.trecho,
          texto: 'só este pedaço',
          trecho: const Trecho(inicio: 1, fim: 4),
          fotos: const [],
        ),
      ]);
      await abrirDiario(t, api: api);

      expect(trechosMarcados(t, 'b'), isEmpty);
      expect(find.text('Quem lê: só um trecho'), findsNothing);
    },
  );

  testWidgets(
    '[006] REQ-12.4: diz quem pode ler em "todo o grupo" e "só você"',
    (t) async {
      final api = apiComRegistros([
        registroDe(id: 'a', fotos: const []),
        registroDe(
          id: 'p',
          data: '2026-11-03',
          entregueEm: DateTime.utc(2026, 11, 3, 12),
          visibilidade: Visibilidade.privado,
          texto: 'Só para mim, de verdade.',
          fotos: const [],
        ),
      ]);
      await abrirDiario(t, api: api);

      expect(find.text('Quem lê: todo o grupo'), findsOneWidget);
      expect(find.text('Quem lê: só você'), findsOneWidget);
      expect(trechosMarcados(t, 'a'), isEmpty);
    },
  );

  testWidgets(
    '[006] REQ-12.5: tocar na foto abre em tela cheia, com texto alternativo e botão de fechar',
    (t) async {
      final api = apiComRegistros([
        registroDe(id: 'b', nome: 'Bia', meu: false, fotos: const ['f1']),
      ]);
      await abrirDiario(t, api: api);
      final semantica = t.ensureSemantics();

      expect(
        t.getSemantics(find.byKey(const Key('foto-f1'))).label,
        contains('Foto do manuscrito de Bia'),
      );

      await t.tap(find.byKey(const Key('foto-f1')));
      await t.pumpAndSettle();

      expect(find.byKey(const Key('foto-tela-cheia')), findsOneWidget);
      expect(find.byType(InteractiveViewer), findsOneWidget);
      expect(
        t.getSemantics(find.byKey(const Key('foto-tela-cheia'))).label,
        contains('Foto do manuscrito de Bia'),
      );

      await t.tap(find.byTooltip('Fechar'));
      await t.pumpAndSettle();
      expect(find.byKey(const Key('foto-tela-cheia')), findsNothing);
      semantica.dispose();
    },
  );

  testWidgets(
    '[006] REQ-12.6: mês sem registro mostra "Nenhum registro neste mês."',
    (t) async {
      await abrirDiario(t, api: apiDaAna());

      expect(find.text('Nenhum registro neste mês.'), findsOneWidget);
    },
  );

  testWidgets(
    '[006] REQ-12.7: erro do servidor aparece em português com "Tentar de novo"',
    (t) async {
      final api = apiDaAna()..falhaAoListar = const ErroApi(500);
      await abrirDiario(t, api: api);

      expect(
        find.text('O servidor teve um problema. Tente de novo em instantes.'),
        findsOneWidget,
      );
      expect(find.textContaining('500'), findsNothing);

      api
        ..falhaAoListar = null
        ..registros.add(
          registroDe(id: 'a', texto: 'Agora carregou, tudo bem.'),
        );
      await tocarBotao(t, 'Tentar de novo');

      expect(find.text('Agora carregou, tudo bem.'), findsOneWidget);
    },
  );

  testWidgets('[006] REQ-12.7: sem conexão, mensagem própria', (t) async {
    final api = apiDaAna()..falhaAoListar = const ErroApi(0);
    await abrirDiario(t, api: api);

    expect(
      find.text('Sem conexão com o servidor. Tente de novo.'),
      findsOneWidget,
    );
  });

  testWidgets('[006] REQ-12.7: sessão que acabou leva à tela de entrar', (
    t,
  ) async {
    final api = apiDaAna()..falhaAoListar = const ErroApi(401);
    await abrirDiario(t, api: api);

    expect(find.text('Sua sessão acabou. Entre de novo.'), findsOneWidget);
  });

  testWidgets(
    '[006] ABU-13: texto com marcação aparece literalmente, como texto',
    (t) async {
      const perigoso =
          '<script>alert(1)</script> <b>oi</b> &lt;i&gt; <img src=x onerror=alert(2)>';
      final api = apiComRegistros([
        registroDe(id: 'a', texto: perigoso, fotos: const []),
        registroDe(
          id: 'b',
          nome: 'Bia',
          meu: false,
          data: '2026-11-04',
          entregueEm: DateTime.utc(2026, 11, 4, 12),
          texto: perigoso,
          fotos: const [],
        ),
      ]);
      await abrirDiario(t, api: api);

      expect(textoCompleto(t, 'a'), perigoso);
      expect(textoCompleto(t, 'b'), perigoso);
      expect(find.text(perigoso), findsNWidgets(2));
    },
  );
}

Future<void> abrirApp0(WidgetTester t, ApiFalsa api, DateTime agora) async {
  await abrirApp(t, api: api, agora: agora);
}
