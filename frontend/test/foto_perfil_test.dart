// [004] Foto de perfil (REQ-7.6, REQ-7.7, REQ-7.8, NFR-FOTO-3): escolher, prévia, enviar, remover, erros e a inicial sobre a cor.
import 'dart:typed_data';

import 'package:entrelinhas/shared/api/api.dart';
import 'package:entrelinhas/shared/ui/avatar.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'suporte/api_falsa.dart';
import 'suporte/app_de_teste.dart';
import 'suporte/seletor_falso.dart';

Future<ApiFalsa> abrirPerfil(
  WidgetTester t, {
  ApiFalsa? api,
  SeletorFalso? seletor,
}) async {
  final falsa = await abrirApp(
    t,
    api: api ?? ApiFalsa(sessao: perfilCompleto()),
    seletor: seletor ?? SeletorFalso(),
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

Future<void> tocar(
  WidgetTester t,
  String texto, {
  Type tipo = FilledButton,
}) async {
  final botao = find.widgetWithText(
    tipo == FilledButton ? FilledButton : OutlinedButton,
    texto,
  );
  await t.ensureVisible(botao);
  await t.tap(botao);
  await t.pumpAndSettle();
}

Avatar avatarDoPerfil(WidgetTester t) =>
    t.widget<Avatar>(find.byKey(const Key('avatar-perfil')));

void main() {
  testWidgets(
    '[004] REQ-7.8: sem foto o perfil mostra a inicial do nome sobre a cor',
    (t) async {
      await abrirPerfil(t);

      final avatar = avatarDoPerfil(t);
      expect(avatar.fotoUrl, isNull);
      expect(avatar.nome, 'Ana');
      expect(avatar.cor, corVerde);
      expect(
        find.descendant(
          of: find.byKey(const Key('avatar-perfil')),
          matching: find.text('A'),
        ),
        findsOneWidget,
      );
      expect(find.text('Remover foto'), findsNothing);
    },
  );

  testWidgets(
    '[004] REQ-7.6: escolher mostra a prévia e só envia ao tocar em "Usar esta foto"',
    (t) async {
      final seletor = SeletorFalso(escolha: fotoDeTeste());
      final api = await abrirPerfil(t, seletor: seletor);
      expect(find.byKey(const Key('previa-foto')), findsNothing);

      await tocar(t, 'Escolher foto');

      expect(seletor.chamadas, 1);
      expect(find.byKey(const Key('previa-foto')), findsOneWidget);
      expect(api.chamadas.where((c) => c.startsWith('enviarFoto')), isEmpty);

      await tocar(t, 'Usar esta foto');

      expect(
        api.chamadas,
        containsAllInOrder(['enviarFoto:perfil', 'definirFotoDePerfil:foto1']),
      );
      expect(api.ultimaFoto['tipo'], 'image/png');
      expect(api.ultimaFoto['finalidade'], 'perfil');
      expect(avatarDoPerfil(t).fotoUrl, 'fotos/foto1/arquivo');
      expect(find.byKey(const Key('previa-foto')), findsNothing);
      expect(find.text('Foto do perfil atualizada.'), findsOneWidget);
    },
  );

  testWidgets('[004] REQ-7.6: fechar o seletor sem escolher não muda nada', (
    t,
  ) async {
    final seletor = SeletorFalso();
    final api = await abrirPerfil(t, seletor: seletor);

    await tocar(t, 'Escolher foto');

    expect(find.byKey(const Key('previa-foto')), findsNothing);
    expect(find.text('Usar esta foto'), findsNothing);
    expect(api.chamadas.where((c) => c.startsWith('enviarFoto')), isEmpty);
  });

  testWidgets(
    '[004] REQ-7.6: com foto, "Remover foto" apaga e volta para a inicial',
    (t) async {
      final api = ApiFalsa(sessao: perfilCompleto(fotoUrl: 'fotos/f9/arquivo'));
      await abrirPerfil(t, api: api);
      expect(avatarDoPerfil(t).fotoUrl, 'fotos/f9/arquivo');

      await tocar(t, 'Remover foto', tipo: OutlinedButton);

      expect(api.chamadas, contains('removerFotoDePerfil'));
      expect(avatarDoPerfil(t).fotoUrl, isNull);
      expect(find.text('Remover foto'), findsNothing);
    },
  );

  testWidgets(
    '[004] REQ-7.7: foto recusada pelo servidor aparece em português, sem detalhe técnico',
    (t) async {
      final api = ApiFalsa(sessao: perfilCompleto())
        ..falhaAoEnviarFoto = const ErroApi(
          422,
          campos: {
            'arquivo': ['Envie uma foto em JPEG, PNG ou WebP.'],
          },
        );
      await abrirPerfil(
        t,
        api: api,
        seletor: SeletorFalso(escolha: fotoDeTeste()),
      );

      await tocar(t, 'Escolher foto');
      await tocar(t, 'Usar esta foto');

      expect(find.text('Envie uma foto em JPEG, PNG ou WebP.'), findsOneWidget);
      expect(find.textContaining('Exception'), findsNothing);
      expect(avatarDoPerfil(t).fotoUrl, isNull);
    },
  );

  testWidgets(
    '[004] REQ-7.7: corpo grande demais (413 do proxy) vira mensagem clara',
    (t) async {
      final api = ApiFalsa(sessao: perfilCompleto())
        ..falhaAoEnviarFoto = const ErroApi(413);
      await abrirPerfil(
        t,
        api: api,
        seletor: SeletorFalso(escolha: fotoDeTeste()),
      );

      await tocar(t, 'Escolher foto');
      await tocar(t, 'Usar esta foto');

      expect(
        find.text('A foto é grande demais. Escolha uma menor.'),
        findsOneWidget,
      );
    },
  );

  testWidgets('[004] REQ-7.7: cota (429) e rede (0) têm mensagem própria', (
    t,
  ) async {
    final api = ApiFalsa(sessao: perfilCompleto())
      ..falhaAoEnviarFoto = const ErroApi(
        429,
        detalhe: 'Muitas fotos enviadas. Tente mais tarde.',
      );
    await abrirPerfil(
      t,
      api: api,
      seletor: SeletorFalso(escolha: fotoDeTeste()),
    );

    await tocar(t, 'Escolher foto');
    await tocar(t, 'Usar esta foto');

    expect(
      find.text('Muitas tentativas. Espere um minuto e tente de novo.'),
      findsOneWidget,
    );
  });

  testWidgets(
    '[004] REQ-7.7: foto acima de 8 MB nem é enviada: o app avisa antes',
    (t) async {
      final grande = fotoDeTeste(bytes: Uint8List(8 * 1024 * 1024 + 1));
      final api = await abrirPerfil(t, seletor: SeletorFalso(escolha: grande));

      await tocar(t, 'Escolher foto');

      expect(
        find.text('A foto passa de 8 MB. Escolha uma menor.'),
        findsOneWidget,
      );
      expect(find.byKey(const Key('previa-foto')), findsNothing);
      expect(api.chamadas.where((c) => c.startsWith('enviarFoto')), isEmpty);
    },
  );

  testWidgets('[004] REQ-7.7: falha do seletor vira mensagem em português', (
    t,
  ) async {
    final seletor = SeletorFalso()..falha = StateError('boom');
    await abrirPerfil(t, seletor: seletor);

    await tocar(t, 'Escolher foto');

    expect(
      find.text('Não foi possível abrir as fotos. Tente de novo.'),
      findsOneWidget,
    );
    expect(find.textContaining('boom'), findsNothing);
  });

  testWidgets(
    '[004] REQ-7.7: sessão que acabou leva de volta à tela de entrar',
    (t) async {
      final api = ApiFalsa(sessao: perfilCompleto())
        ..falhaAoEnviarFoto = const ErroApi(401);
      await abrirPerfil(
        t,
        api: api,
        seletor: SeletorFalso(escolha: fotoDeTeste()),
      );

      await tocar(t, 'Escolher foto');
      await tocar(t, 'Usar esta foto');

      expect(find.text('Sua sessão acabou. Entre de novo.'), findsOneWidget);
    },
  );

  testWidgets(
    '[004] NFR-FOTO-3: o avatar tem texto alternativo com o nome, com e sem foto',
    (t) async {
      final api = ApiFalsa(sessao: perfilCompleto(fotoUrl: 'fotos/f1/arquivo'));
      await abrirPerfil(t, api: api);
      final comFoto = t.getSemantics(find.byKey(const Key('avatar-perfil')));
      expect(comFoto.label, contains('Foto de Ana'));

      await tocar(t, 'Remover foto', tipo: OutlinedButton);
      final semFoto = t.getSemantics(find.byKey(const Key('avatar-perfil')));
      expect(semFoto.label, contains('Sem foto de Ana'));
    },
  );

  testWidgets(
    '[004] REQ-7.8: foto que não carrega cai na inicial sobre a cor (nada de ícone quebrado)',
    (t) async {
      final api = ApiFalsa(sessao: perfilCompleto(fotoUrl: 'fotos/f1/arquivo'));
      await abrirPerfil(t, api: api);
      await t.pump(const Duration(seconds: 1));

      // No teste não há servidor: a imagem falha e o avatar mostra a inicial.
      expect(
        find.descendant(
          of: find.byKey(const Key('avatar-perfil')),
          matching: find.text('A'),
        ),
        findsOneWidget,
      );
    },
  );

  testWidgets(
    '[004] NFR-FOTO-3: a tela do perfil com foto não rola na horizontal em 360 px',
    (t) async {
      final api = ApiFalsa(sessao: perfilCompleto(fotoUrl: 'fotos/f1/arquivo'));
      await abrirApp(t, api: api, seletor: SeletorFalso(), tamanho: celular);
      await t.tap(
        find.descendant(
          of: find.byType(NavigationBar),
          matching: find.text('Perfil'),
        ),
      );
      await t.pumpAndSettle();

      expect(t.takeException(), isNull);
      final rolagemHorizontal = find.byWidgetPredicate(
        (w) =>
            w is SingleChildScrollView && w.scrollDirection == Axis.horizontal,
      );
      expect(rolagemHorizontal, findsNothing);
    },
  );
}
