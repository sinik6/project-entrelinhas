// [003] NFR-A11Y-1 e NFR-RESP-1: guias de acessibilidade do Flutter nos dois temas e telas sem estouro de 360 a 1280 px.
import 'package:entrelinhas/features/hoje/modelos.dart';
import 'package:entrelinhas/shared/api/api.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'suporte/api_falsa.dart';
import 'suporte/app_de_teste.dart';
import 'suporte/hoje_de_teste.dart';
import 'suporte/seletor_falso.dart';

typedef Preparar = Future<void> Function(
  WidgetTester t,
  Size tamanho,
  Brightness brilho,
);

Future<void> telaEntrar(WidgetTester t, Size tamanho, Brightness brilho) async {
  await abrirApp(t, tamanho: tamanho, brilho: brilho);
}

Future<void> telaConvite(
  WidgetTester t,
  Size tamanho,
  Brightness brilho,
) async {
  await abrirApp(t, tamanho: tamanho, brilho: brilho);
  await irPara(t, '/convite/abc123');
}

Future<void> telaPerfil(WidgetTester t, Size tamanho, Brightness brilho) async {
  await abrirApp(
    t,
    api: ApiFalsa(sessao: perfilCompleto()),
    tamanho: tamanho,
    brilho: brilho,
  );
  await t.tap(
    find.descendant(
      of: find.byType(NavigationBar),
      matching: find.text('Perfil'),
    ),
  );
  await t.pumpAndSettle();
}

Future<void> telaGrupo(WidgetTester t, Size tamanho, Brightness brilho) async {
  final api = ApiFalsa(sessao: perfilCompleto())
    ..grupoAtual = grupoCom([const Membro(nome: 'Ana', cor: corVerde)]);
  await abrirApp(t, api: api, tamanho: tamanho, brilho: brilho);
  await t.tap(find.widgetWithText(FilledButton, 'Convidar a outra pessoa'));
  await t.pumpAndSettle();
}

Future<void> telaPerfilComFoto(
  WidgetTester t,
  Size tamanho,
  Brightness brilho,
) async {
  await abrirApp(
    t,
    api: ApiFalsa(sessao: perfilCompleto(fotoUrl: 'fotos/f1/arquivo')),
    tamanho: tamanho,
    brilho: brilho,
  );
  await t.tap(
    find.descendant(
      of: find.byType(NavigationBar),
      matching: find.text('Perfil'),
    ),
  );
  await t.pumpAndSettle();
}

Future<void> telaPerfilComFotoEscolhida(
  WidgetTester t,
  Size tamanho,
  Brightness brilho,
) async {
  await abrirApp(
    t,
    api: ApiFalsa(sessao: perfilCompleto()),
    seletor: SeletorFalso(escolha: fotoDeTeste()),
    tamanho: tamanho,
    brilho: brilho,
  );
  await t.tap(
    find.descendant(
      of: find.byType(NavigationBar),
      matching: find.text('Perfil'),
    ),
  );
  await t.pumpAndSettle();
  await t.tap(find.widgetWithText(FilledButton, 'Escolher foto'));
  await t.pumpAndSettle();
}

Future<void> telaHoje(WidgetTester t, Size tamanho, Brightness brilho) async {
  await abrirHoje(t, tamanho: tamanho, brilho: brilho);
}

Future<void> telaHojePreenchida(
  WidgetTester t,
  Size tamanho,
  Brightness brilho,
) async {
  await abrirHoje(t, tamanho: tamanho, brilho: brilho);
  await preencherTudo(t);
}

Future<void> telaHojeComTrecho(
  WidgetTester t,
  Size tamanho,
  Brightness brilho,
) async {
  await abrirHoje(t, tamanho: tamanho, brilho: brilho);
  await escrever(t, textoValido);
  await adicionarFoto(t);
  await tocarTexto(t, 'Só um trecho');
  await selecionar(t, 0, 4);
  await tocarBotao(t, 'Usar a seleção');
}

Future<void> telaHojeEntregue(
  WidgetTester t,
  Size tamanho,
  Brightness brilho,
) async {
  final api = apiDaAna()..registros.add(registroDe(id: 'meu'));
  await abrirHoje(t, api: api, tamanho: tamanho, brilho: brilho);
}

Future<void> telaDiario(WidgetTester t, Size tamanho, Brightness brilho) async {
  final api = apiDaAna()
    ..registros.addAll([
      registroDe(
        id: 'a',
        visibilidade: Visibilidade.trecho,
        texto: 'Antes do meio, meio, depois do meio.',
        trecho: const Trecho(inicio: 15, fim: 20),
      ),
      registroDe(
        id: 'b',
        nome: 'Bia',
        cor: corAmbar,
        meu: false,
        data: '2026-11-05',
        entregueEm: DateTime.utc(2026, 11, 5, 12),
        texto: 'Texto completo da Bia.',
        fotos: const ['f1'],
      ),
      registroDe(
        id: 'c',
        nome: 'Bia',
        cor: corAmbar,
        meu: false,
        data: '2026-11-04',
        entregueEm: DateTime.utc(2026, 11, 4, 12),
        visibilidade: Visibilidade.privado,
        texto: null,
        fotos: const [],
        aviso: 'Enviado, mas mantido privado pelo autor',
      ),
    ]);
  await abrirDiario(t, api: api, tamanho: tamanho, brilho: brilho);
}

Future<void> telaFotoCheia(
  WidgetTester t,
  Size tamanho,
  Brightness brilho,
) async {
  await telaDiario(t, tamanho, brilho);
  await t.tap(find.byKey(const Key('foto-f1')));
  await t.pumpAndSettle();
}

final telas = <String, Preparar>{
  'hoje': telaHoje,
  'hoje preenchida': telaHojePreenchida,
  'hoje com trecho': telaHojeComTrecho,
  'hoje já entregue': telaHojeEntregue,
  'diário': telaDiario,
  'foto em tela cheia': telaFotoCheia,
  'entrar': telaEntrar,
  'criar conta': telaConvite,
  'perfil': telaPerfil,
  'perfil com foto': telaPerfilComFoto,
  'perfil com foto escolhida': telaPerfilComFotoEscolhida,
  'grupo': telaGrupo,
};

void main() {
  for (final MapEntry(key: nome, value: preparar) in telas.entries) {
    for (final brilho in Brightness.values) {
      testWidgets(
        '[003] NFR-A11Y-1: tela "$nome" no tema ${brilho.name} cumpre as guias de acessibilidade',
        (t) async {
          final semantica = t.ensureSemantics();
          await preparar(t, celular, brilho);

          await expectLater(t, meetsGuideline(textContrastGuideline));
          await expectLater(t, meetsGuideline(androidTapTargetGuideline));
          await expectLater(t, meetsGuideline(iOSTapTargetGuideline));
          await expectLater(t, meetsGuideline(labeledTapTargetGuideline));
          semantica.dispose();
        },
      );
    }

    for (final tamanho in [celular, computador]) {
      testWidgets(
        '[003] NFR-RESP-1: tela "$nome" em ${tamanho.width.toInt()} px não estoura nem rola na horizontal',
        (t) async {
          await preparar(t, tamanho, Brightness.light);

          expect(t.takeException(), isNull);
          // Todo campo de texto de uma linha tem uma rolagem horizontal interna (a do cursor): não é a da página.
          final doCampoDeTexto = find
              .descendant(
                of: find.byType(EditableText),
                matching: find.byType(Scrollable),
              )
              .evaluate()
              .map((e) => e.widget)
              .toSet();
          for (final rolagem in t.widgetList<Scrollable>(
            find.byType(Scrollable),
          )) {
            if (doCampoDeTexto.contains(rolagem)) continue;
            expect(
              rolagem.axis,
              isNot(Axis.horizontal),
              reason: 'sem rolagem horizontal',
            );
          }
        },
      );
    }
  }
}
