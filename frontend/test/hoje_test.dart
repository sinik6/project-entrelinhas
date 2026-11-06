// [006] US-11 (REQ-11.1, 11.2, 11.5 a 11.8): escrever, fotografar, escolher quem lê e entregar o dia.
import 'dart:async';
import 'dart:typed_data';

import 'package:entrelinhas/features/hoje/modelos.dart';
import 'package:entrelinhas/shared/api/api.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'suporte/api_falsa.dart';
import 'suporte/app_de_teste.dart';
import 'suporte/hoje_de_teste.dart';
import 'suporte/seletor_falso.dart';

void main() {
  testWidgets(
    '[006] REQ-11.1: sem entrega, mostra texto, fotos e 3 opções de visibilidade, nenhuma marcada',
    (t) async {
      await abrirHoje(t);

      expect(find.byKey(campoDoTexto), findsOneWidget);
      expect(find.text('Adicionar foto'), findsOneWidget);
      expect(find.text('Todo o grupo lê'), findsOneWidget);
      expect(find.text('Só eu'), findsOneWidget);
      expect(find.text('Só um trecho'), findsOneWidget);
      // nenhuma opção marcada
      final radios = t.widgetList<Radio<String>>(find.byType(Radio<String>));
      expect(radios, hasLength(3));
      final grupo = RadioGroup.maybeOf<String>(
        t.element(find.byType(Radio<String>).first),
      );
      expect(grupo?.groupValue, isNull);
      expect(entregarHabilitado(t), isFalse);
    },
  );

  testWidgets('[006] REQ-11.1: no máximo 3 fotos; dá para tirar uma', (
    t,
  ) async {
    await abrirHoje(t);

    await adicionarFoto(t);
    await adicionarFoto(t);
    await adicionarFoto(t);

    expect(find.byKey(const Key('foto-escolhida-0')), findsOneWidget);
    expect(find.byKey(const Key('foto-escolhida-2')), findsOneWidget);
    expect(find.text('Adicionar foto'), findsNothing);

    await t.tap(find.byTooltip('Tirar a foto 2'));
    await t.pumpAndSettle();

    expect(find.byKey(const Key('foto-escolhida-2')), findsNothing);
    expect(find.text('Adicionar foto'), findsOneWidget);
  });

  testWidgets(
    '[006] REQ-11.1: fechar o seletor sem escolher não adiciona foto',
    (t) async {
      await abrirHoje(t, seletor: SeletorFalso());

      await adicionarFoto(t);

      expect(find.byKey(const Key('foto-escolhida-0')), findsNothing);
    },
  );

  testWidgets(
    '[006] REQ-11.1: foto acima de 8 MB é recusada antes de entrar no rascunho',
    (t) async {
      final grande = fotoDeTeste(bytes: Uint8List(8 * 1024 * 1024 + 1));
      await abrirHoje(t, seletor: SeletorFalso(escolha: grande));

      await adicionarFoto(t);

      expect(
        find.text('A foto passa de 8 MB. Escolha uma menor.'),
        findsOneWidget,
      );
      expect(find.byKey(const Key('foto-escolhida-0')), findsNothing);
    },
  );

  testWidgets(
    '[006] REQ-11.2: Entregar fica desabilitado e a tela diz o que falta',
    (t) async {
      await abrirHoje(t);

      final falta = find.byKey(const Key('falta-para-entregar'));
      expect(
        find.descendant(of: falta, matching: find.textContaining('texto')),
        findsOneWidget,
      );
      expect(
        t
            .widget<Text>(
              find.descendant(of: falta, matching: find.byType(Text)),
            )
            .data,
        allOf(contains('10 caracteres'), contains('foto'), contains('quem lê')),
      );

      await escrever(t, 'curto');
      expect(entregarHabilitado(t), isFalse);
      await escrever(t, '123456789'); // 9 úteis
      expect(entregarHabilitado(t), isFalse);
      await escrever(t, '          x          '); // espaços não contam
      expect(entregarHabilitado(t), isFalse);

      await escrever(t, textoValido);
      expect(
        t
            .widget<Text>(
              find.descendant(of: falta, matching: find.byType(Text)),
            )
            .data,
        isNot(contains('10 caracteres')),
      );
      expect(entregarHabilitado(t), isFalse);

      await adicionarFoto(t);
      expect(entregarHabilitado(t), isFalse);

      await tocarTexto(t, 'Todo o grupo lê');
      expect(entregarHabilitado(t), isTrue);
      expect(falta, findsNothing);
    },
  );

  testWidgets(
    '[006] REQ-11.2: "Só um trecho" sem trecho escolhido continua desabilitado',
    (t) async {
      await abrirHoje(t);
      await escrever(t, textoValido);
      await adicionarFoto(t);

      await tocarTexto(t, 'Só um trecho');

      expect(entregarHabilitado(t), isFalse);
      expect(
        t
            .widget<Text>(
              find.descendant(
                of: find.byKey(const Key('falta-para-entregar')),
                matching: find.byType(Text),
              ),
            )
            .data,
        contains('trecho'),
      );
    },
  );

  testWidgets(
    '[006] REQ-11.5: Entregar pede confirmação com o resumo e o aviso de que não edita nem apaga',
    (t) async {
      final api = await abrirHoje(t);
      await preencherTudo(t);

      await tocarBotao(t, 'Entregar');

      expect(find.byType(AlertDialog), findsOneWidget);
      expect(find.textContaining('Todo o grupo lê'), findsWidgets);
      expect(find.textContaining('1 foto'), findsOneWidget);
      expect(
        find.textContaining('não pode ser editado nem apagado'),
        findsOneWidget,
      );
      expect(api.chamadas, isNot(contains('entregarRegistro')));

      await tocarBotao(t, 'Voltar');

      expect(find.byType(AlertDialog), findsNothing);
      expect(api.chamadas, isNot(contains('entregarRegistro')));
      expect(
        controladorDoTexto(t).text,
        textoValido,
        reason: 'voltar mantém o texto',
      );
    },
  );

  testWidgets(
    '[006] REQ-11.6: confirmar envia as fotos, depois o registro, e mostra o registro do dia',
    (t) async {
      final api = await abrirHoje(t);
      await escrever(t, textoValido);
      await adicionarFoto(t);
      await adicionarFoto(t);
      await tocarTexto(t, 'Só eu');

      await tocarBotao(t, 'Entregar');
      await t.tap(confirmarEntrega);
      await t.pumpAndSettle();

      expect(
        api.chamadas.where(
          (c) => c.startsWith('enviarFoto') || c == 'entregarRegistro',
        ),
        ['enviarFoto:manuscrito', 'enviarFoto:manuscrito', 'entregarRegistro'],
      );
      expect(api.ultimaEntrega['fotos'], ['foto1', 'foto2']);
      expect(api.ultimaEntrega['visibilidade'], Visibilidade.privado);
      expect(api.ultimaEntrega['texto'], textoValido);
      expect(api.ultimaEntrega['trecho'], isNull);
      expect(find.text('Registro entregue'), findsOneWidget);
      expect(find.byKey(const Key('registro-do-dia')), findsOneWidget);
      expect(find.byKey(campoDoTexto), findsNothing);
      expect(find.text(textoValido), findsOneWidget);
    },
  );

  testWidgets(
    '[006] REQ-11.6: mostra o progresso "Enviando fotos 1 de 2…" enquanto sobe',
    (t) async {
      final api = await abrirHoje(t);
      await escrever(t, textoValido);
      await adicionarFoto(t);
      await adicionarFoto(t);
      await tocarTexto(t, 'Todo o grupo lê');
      api.portaoDaEntrega = Completer<void>();

      await tocarBotao(t, 'Entregar');
      await t.tap(confirmarEntrega);
      await t.pump();
      await t.pump();

      expect(find.textContaining('Enviando'), findsOneWidget);

      api.portaoDaEntrega!.complete();
      await t.pumpAndSettle();
      expect(find.text('Registro entregue'), findsOneWidget);
    },
  );

  testWidgets(
    '[006] REQ-11.7: foto que falha mostra a mensagem, mantém tudo e a nova tentativa só reenvia o que falta',
    (t) async {
      final api = await abrirHoje(t);
      api.filaDeFalhasDeFoto.addAll([
        null,
        const ErroApi(0),
      ]); // a 1ª sobe, a 2ª cai
      await escrever(t, textoValido);
      await adicionarFoto(t);
      await adicionarFoto(t);
      await tocarTexto(t, 'Todo o grupo lê');

      await tocarBotao(t, 'Entregar');
      await t.tap(confirmarEntrega);
      await t.pumpAndSettle();

      expect(
        find.text('Sem conexão com o servidor. Tente de novo.'),
        findsOneWidget,
      );
      expect(api.chamadas, isNot(contains('entregarRegistro')));
      expect(controladorDoTexto(t).text, textoValido);
      expect(find.byKey(const Key('foto-escolhida-1')), findsOneWidget);
      expect(api.fotosEnviadas, 1);

      await tocarBotao(t, 'Tentar de novo');

      // 1 foto no primeiro ciclo + 1 (só a que faltava) agora; a primeira não subiu de novo
      expect(
        api.chamadas.where((c) => c.startsWith('enviarFoto')),
        hasLength(3),
      );
      expect(api.fotosEnviadas, 2);
      expect(api.ultimaEntrega['fotos'], ['foto1', 'foto2']);
      expect(find.text('Registro entregue'), findsOneWidget);
    },
  );

  testWidgets(
    '[006] REQ-11.7: falha do registro mantém texto e escolhas e não reenvia as fotos',
    (t) async {
      final api = await abrirHoje(t);
      api.falhaAoEntregar = const ErroApi(500);
      await preencherTudo(t);

      await tocarBotao(t, 'Entregar');
      await t.tap(confirmarEntrega);
      await t.pumpAndSettle();

      expect(
        find.text('O servidor teve um problema. Tente de novo em instantes.'),
        findsOneWidget,
      );
      expect(controladorDoTexto(t).text, textoValido);
      expect(find.byKey(const Key('foto-escolhida-0')), findsOneWidget);

      api.falhaAoEntregar = null;
      await tocarBotao(t, 'Tentar de novo');

      expect(
        api.fotosEnviadas,
        1,
        reason: 'a foto que já subiu não sobe de novo',
      );
      expect(api.chamadas.where((c) => c == 'entregarRegistro'), hasLength(2));
      expect(find.text('Registro entregue'), findsOneWidget);
    },
  );

  testWidgets(
    '[006] REQ-11.7: 422 do servidor aparece em português sob o campo, sem detalhe técnico',
    (t) async {
      final api = await abrirHoje(t);
      api.falhaAoEntregar = const ErroApi(
        422,
        campos: {
          'texto': ['Escreva pelo menos 10 caracteres.'],
        },
      );
      await preencherTudo(t);

      await tocarBotao(t, 'Entregar');
      await t.tap(confirmarEntrega);
      await t.pumpAndSettle();

      expect(find.text('Escreva pelo menos 10 caracteres.'), findsOneWidget);
      expect(find.textContaining('Exception'), findsNothing);
      expect(controladorDoTexto(t).text, textoValido);
    },
  );

  testWidgets(
    '[006] REQ-11.8: dia já entregue (409) mostra o registro de hoje e a mensagem',
    (t) async {
      final api = apiDaAna();
      await abrirHoje(t, api: api);
      // a entrega já existe no servidor, mas a tela foi aberta antes (ex.: outro aparelho)
      api.registros.add(
        registroDe(id: 'ja', texto: 'Já escrevi hoje, de outro aparelho.'),
      );
      await preencherTudo(t);

      await tocarBotao(t, 'Entregar');
      await t.tap(confirmarEntrega);
      await t.pumpAndSettle();

      expect(find.text('Você já entregou o registro de hoje.'), findsOneWidget);
      expect(find.byKey(const Key('registro-do-dia')), findsOneWidget);
      expect(find.text('Já escrevi hoje, de outro aparelho.'), findsOneWidget);
      expect(find.byKey(campoDoTexto), findsNothing);
    },
  );

  testWidgets(
    '[006] REQ-11.8: ao abrir Hoje com o dia já entregue, mostra o registro e não o campo',
    (t) async {
      final api = apiDaAna()
        ..registros.add(registroDe(id: 'meu', texto: 'Meu dia, já entregue.'));
      await abrirHoje(t, api: api);

      expect(find.byKey(const Key('registro-do-dia')), findsOneWidget);
      expect(find.text('Meu dia, já entregue.'), findsOneWidget);
      expect(find.byKey(campoDoTexto), findsNothing);
      expect(find.text('Adicionar foto'), findsNothing);
    },
  );

  testWidgets(
    '[006] REQ-11.8: sem registro da outra pessoa, diz que ela ainda não entregou',
    (t) async {
      await abrirHoje(t);

      expect(find.text('Bia ainda não entregou hoje.'), findsOneWidget);
    },
  );

  testWidgets(
    '[006] REQ-11.8: com registro da outra pessoa, diz que ela entregou',
    (t) async {
      final api = apiDaAna()
        ..registros.addAll([
          registroDe(id: 'a', texto: 'Do dia da Ana, tudo certo.'),
          registroDe(id: 'b', nome: 'Bia', meu: false, texto: 'Da Bia.'),
        ]);
      await abrirHoje(t, api: api);

      expect(find.text('Bia já entregou o registro de hoje.'), findsOneWidget);
    },
  );

  testWidgets(
    '[006] REQ-11.8: registro privado da outra pessoa aparece só como "privado"',
    (t) async {
      final api = apiDaAna()
        ..registros.addAll([
          registroDe(id: 'a', texto: 'Do dia da Ana, tudo certo.'),
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
      await abrirHoje(t, api: api);

      expect(
        find.text('Bia entregou, mas manteve o registro privado.'),
        findsOneWidget,
      );
    },
  );

  testWidgets(
    '[006] REQ-11.8: erro ao carregar o dia mostra a mensagem e "Tentar de novo"',
    (t) async {
      final api = apiDaAna()..falhaAoListar = const ErroApi(0);
      await abrirHoje(t, api: api);

      expect(
        find.text('Sem conexão com o servidor. Tente de novo.'),
        findsOneWidget,
      );

      api.falhaAoListar = null;
      await tocarBotao(t, 'Tentar de novo');

      expect(find.byKey(campoDoTexto), findsOneWidget);
    },
  );

  testWidgets('[006] REQ-11.1: sem grupo, Hoje e Diário levam ao Grupo', (
    t,
  ) async {
    final api = ApiFalsa(sessao: perfilCompleto());
    await abrirApp(t, api: api);

    await irPara(t, '/hoje');
    expect(find.text('Convidar a outra pessoa'), findsNothing);
    expect(find.byKey(campoDoTexto), findsNothing);
    expect(find.byKey(const Key('pagina-do-grupo')), findsOneWidget);

    await irPara(t, '/diario');
    expect(find.byKey(const Key('pagina-do-grupo')), findsOneWidget);
  });

  testWidgets(
    '[006] REQ-12.7: sessão que acabou ao entregar leva à tela de entrar',
    (t) async {
      final api = await abrirHoje(t);
      api.falhaAoEntregar = const ErroApi(401);
      await preencherTudo(t);

      await tocarBotao(t, 'Entregar');
      await t.tap(confirmarEntrega);
      await t.pumpAndSettle();

      expect(find.text('Sua sessão acabou. Entre de novo.'), findsOneWidget);
    },
  );
}
