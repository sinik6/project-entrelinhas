// [010] US-18 (REQ-18.2, 18.6, 18.7, 18.8, NFR-LEMB-4): a seção "Lembrete diário" em Perfil, com o Web Push de mentira.
import 'dart:async';

import 'package:entrelinhas/shared/api/api.dart';
import 'package:entrelinhas/shared/push/push_api.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'suporte/api_falsa.dart';
import 'suporte/app_de_teste.dart';
import 'suporte/push_falso.dart';

const chave = Key('chave-do-lembrete');

Future<ApiFalsa> abrirPerfil(
  WidgetTester t, {
  required PushFalso push,
  ApiFalsa? api,
  Size tamanho = const Size(412, 900),
  Brightness brilho = Brightness.light,
}) async {
  final falsa = api ?? ApiFalsa(sessao: perfilCompleto());
  await abrirApp(t, api: falsa, push: push, tamanho: tamanho, brilho: brilho);
  await irPara(t, '/perfil');
  await t.ensureVisible(find.text('Lembrete diário'));
  await t.pumpAndSettle();
  return falsa;
}

SwitchListTile interruptor(WidgetTester t) =>
    t.widget<SwitchListTile>(find.byKey(chave));

Future<void> alternar(WidgetTester t) async {
  await t.ensureVisible(find.byKey(chave));
  await t.tap(find.byKey(chave));
  await t.pumpAndSettle();
}

void main() {
  testWidgets(
    '[010] REQ-18.7: servidor sem chaves VAPID (503) esconde a seção',
    (t) async {
      final api = ApiFalsa(sessao: perfilCompleto())..chaveDeLembretes = null;
      await abrirApp(t, api: api, push: PushFalso());
      await irPara(t, '/perfil');

      expect(find.text('Lembrete diário'), findsNothing);
      expect(find.byKey(chave), findsNothing);
    },
  );

  testWidgets('[010] REQ-18.8: começa desligado e explica o que faz', (
    t,
  ) async {
    await abrirPerfil(t, push: PushFalso());

    expect(interruptor(t).value, isFalse);
    expect(interruptor(t).onChanged, isNotNull);
    expect(find.text('Lembrete diário às 21h30'), findsOneWidget);
    expect(find.textContaining('Desligado'), findsOneWidget);
  });

  testWidgets(
    '[010] REQ-18.2: ligar pede a permissão, assina com a chave do servidor e manda a assinatura',
    (t) async {
      final push = PushFalso();
      final api = await abrirPerfil(t, push: push);

      await alternar(t);

      expect(push.chamadas, ['pedirPermissao', 'assinar']);
      expect(push.ultimaChave, 'CHAVE-PUBLICA');
      expect(api.assinaturasGuardadas, hasLength(1));
      expect(
        api.assinaturasGuardadas.single.endpoint,
        'https://fcm.googleapis.com/fcm/send/aparelho-1',
      );
      expect(api.assinaturasGuardadas.single.p256dh, 'BP256');
      expect(api.assinaturasGuardadas.single.auth, 'AUTH');
      expect(interruptor(t).value, isTrue);
      expect(find.textContaining('Ligado neste aparelho'), findsOneWidget);
    },
  );

  testWidgets(
    '[010] REQ-18.8: com assinatura já no aparelho, abre como ligado',
    (t) async {
      final push = PushFalso(
        permissaoAtual: PermissaoDePush.concedida,
        assinatura: const AssinaturaDoNavegador(
          endpoint: 'https://fcm.googleapis.com/fcm/send/x',
          p256dh: 'a',
          auth: 'b',
        ),
      );
      await abrirPerfil(t, push: push);

      expect(interruptor(t).value, isTrue);
      expect(find.textContaining('Ligado neste aparelho'), findsOneWidget);
    },
  );

  testWidgets(
    '[010] REQ-18.6: desligar cancela no navegador e remove do servidor',
    (t) async {
      final push = PushFalso(
        permissaoAtual: PermissaoDePush.concedida,
        assinatura: const AssinaturaDoNavegador(
          endpoint: 'https://fcm.googleapis.com/fcm/send/x',
          p256dh: 'a',
          auth: 'b',
        ),
      );
      final api = await abrirPerfil(t, push: push);

      await alternar(t);

      expect(push.chamadas, contains('cancelar'));
      expect(api.assinaturasRemovidas, [
        'https://fcm.googleapis.com/fcm/send/x',
      ]);
      expect(interruptor(t).value, isFalse);
      expect(find.textContaining('Desligado'), findsOneWidget);
    },
  );

  testWidgets(
    '[010] REQ-18.7: permissão negada no pedido explica como liberar e não assina',
    (t) async {
      final push = PushFalso()..respostaDoPedido = PermissaoDePush.negada;
      final api = await abrirPerfil(t, push: push);

      await alternar(t);

      expect(push.chamadas, ['pedirPermissao']);
      expect(api.assinaturasGuardadas, isEmpty);
      expect(interruptor(t).value, isFalse);
      expect(find.textContaining('Bloqueado pelo navegador'), findsOneWidget);
      expect(find.textContaining('configurações'), findsOneWidget);
    },
  );

  testWidgets(
    '[010] REQ-18.7: já bloqueado ao abrir, o botão fica desabilitado',
    (t) async {
      await abrirPerfil(
        t,
        push: PushFalso(permissaoAtual: PermissaoDePush.negada),
      );

      expect(interruptor(t).onChanged, isNull);
      expect(find.textContaining('Bloqueado pelo navegador'), findsOneWidget);
    },
  );

  testWidgets(
    '[010] REQ-18.7: no iPhone fora da tela inicial, explica como instalar e deixa desligado',
    (t) async {
      await abrirPerfil(
        t,
        push: PushFalso(suporteDoNavegador: SuporteDePush.precisaInstalar),
      );

      expect(interruptor(t).onChanged, isNull);
      expect(find.textContaining('iPhone'), findsOneWidget);
      expect(find.textContaining('Adicionar à Tela de Início'), findsOneWidget);
    },
  );

  testWidgets(
    '[010] REQ-18.7: navegador sem suporte diz isso e deixa desligado',
    (t) async {
      await abrirPerfil(
        t,
        push: PushFalso(suporteDoNavegador: SuporteDePush.semSuporte),
      );

      expect(interruptor(t).onChanged, isNull);
      expect(
        find.text('Este navegador não permite lembretes.'),
        findsOneWidget,
      );
    },
  );

  testWidgets(
    '[010] REQ-18.2: falha ao guardar no servidor mostra a mensagem e desfaz a assinatura do navegador',
    (t) async {
      final push = PushFalso();
      final api = ApiFalsa(sessao: perfilCompleto())
        ..falhaAoGuardarAssinatura = const ErroApi(
          409,
          detalhe: 'Você já tem 5 aparelhos com lembrete.',
        );
      await abrirPerfil(t, push: push, api: api);

      await alternar(t);

      expect(
        find.text('Você já tem 5 aparelhos com lembrete.'),
        findsOneWidget,
      );
      expect(
        push.chamadas,
        contains('cancelar'),
        reason: 'sem órfã no navegador',
      );
      expect(interruptor(t).value, isFalse);
    },
  );

  testWidgets(
    '[010] REQ-18.2: falha do navegador ao assinar aparece em português, sem detalhe técnico',
    (t) async {
      final push = PushFalso()..falhaAoAssinar = StateError('boom interno');
      await abrirPerfil(t, push: push);

      await alternar(t);

      expect(
        find.textContaining('Não foi possível ligar o lembrete'),
        findsOneWidget,
      );
      expect(find.textContaining('boom'), findsNothing);
      expect(interruptor(t).value, isFalse);
    },
  );

  testWidgets('[010] REQ-18.2: dois toques seguidos assinam uma vez só', (
    t,
  ) async {
    final push = PushFalso()..portaoDeAssinar = Completer<void>();
    final api = await abrirPerfil(t, push: push);

    await t.ensureVisible(find.byKey(chave));
    await t.tap(find.byKey(chave));
    await t.tap(find.byKey(chave), warnIfMissed: false);
    await t.pump();
    push.portaoDeAssinar!.complete();
    await t.pumpAndSettle();

    expect(push.chamadas.where((c) => c == 'assinar'), hasLength(1));
    expect(api.assinaturasGuardadas, hasLength(1));
  });

  testWidgets('[010] REQ-18.2: sessão que acabou leva à tela de entrar', (
    t,
  ) async {
    final api = ApiFalsa(sessao: perfilCompleto())
      ..falhaAoGuardarAssinatura = const ErroApi(401);
    await abrirPerfil(t, push: PushFalso(), api: api);

    await alternar(t);

    expect(find.text('Sua sessão acabou. Entre de novo.'), findsOneWidget);
  });
}
