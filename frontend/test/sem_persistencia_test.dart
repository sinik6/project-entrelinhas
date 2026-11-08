// [006] REQ-11.9, CTL-41: o texto, o trecho e as fotos ficam só na memória do app; nada vai ao armazenamento do navegador ou do aparelho.
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'suporte/app_de_teste.dart';
import 'suporte/hoje_de_teste.dart';

/// Tudo o que, no código do app, guardaria algo no navegador ou no aparelho.
const proibidos = [
  'localStorage',
  'sessionStorage',
  'indexedDB',
  'IndexedDB',
  'shared_preferences',
  'SharedPreferences',
  'document.cookie',
  'package:web',
  'dart:html',
  'dart:js_interop',
  'dart:io',
  'path_provider',
  'hive',
  'sqflite',
  'drift',
  'isar',
  'flutter_secure_storage',
  'RestorationMixin',
  'RestorableTextEditingController',
  'restorationId',
];

void main() {
  test('[006] CTL-41: nenhum arquivo do app usa armazenamento local nem restauração de estado', () {
    final arquivos = Directory('lib')
        .listSync(recursive: true)
        .whereType<File>()
        .where((f) => f.path.endsWith('.dart'));
    expect(arquivos, isNotEmpty);

    final achados = <String>[];
    for (final arquivo in arquivos) {
      final codigo = arquivo.readAsStringSync();
      for (final proibido in proibidos) {
        // A ponte do Web Push (spec 010) precisa do `dart:js_interop`; ela não usa nenhum armazenamento (as outras
        // palavras da lista continuam valendo para ela).
        if (proibido == 'dart:js_interop' &&
            arquivo.path.endsWith('shared/push/push_api_web.dart')) {
          continue;
        }
        if (codigo.contains(proibido)) {
          achados.add('${arquivo.path}: $proibido');
        }
      }
    }

    expect(achados, isEmpty);
  });

  test('[006] CTL-41: o pubspec não traz pacote de armazenamento', () {
    final pubspec = File('pubspec.yaml').readAsStringSync();
    for (final pacote in [
      'shared_preferences',
      'hive',
      'sqflite',
      'drift',
      'isar',
      'path_provider',
      'flutter_secure_storage',
      'localstorage',
    ]) {
      expect(
        pubspec.contains(RegExp('^  $pacote:', multiLine: true)),
        isFalse,
        reason: pacote,
      );
    }
  });

  test('[006] CTL-41: o texto do registro não vai para log do console', () {
    final proibidosDeLog = RegExp(r'\b(print|debugPrint|log)\(');
    final achados = <String>[];
    for (final arquivo in Directory(
      'lib/features/hoje',
    ).listSync(recursive: true).whereType<File>()) {
      if (proibidosDeLog.hasMatch(arquivo.readAsStringSync())) {
        achados.add(arquivo.path);
      }
    }
    for (final arquivo in Directory(
      'lib/features/diario',
    ).listSync(recursive: true).whereType<File>()) {
      if (proibidosDeLog.hasMatch(arquivo.readAsStringSync())) {
        achados.add(arquivo.path);
      }
    }

    expect(achados, isEmpty);
  });

  testWidgets(
    '[006] REQ-11.9: depois de entregar, o rascunho some da memória (campo, trecho e fotos)',
    (t) async {
      final api = await abrirHoje(t);
      await preencherTudo(t);

      await tocarBotao(t, 'Entregar');
      await t.tap(confirmarEntrega);
      await t.pumpAndSettle();
      expect(find.text('Registro entregue'), findsOneWidget);

      // sai e volta: a tela de escrita não traz nada do rascunho
      await irPara(t, '/grupo');
      await irPara(t, '/hoje');

      expect(find.byKey(campoDoTexto), findsNothing);
      expect(find.byKey(const Key('foto-escolhida-0')), findsNothing);
      expect(find.byKey(const Key('registro-do-dia')), findsOneWidget);
      expect(api.registros, hasLength(1));
    },
  );

  testWidgets(
    '[006] REQ-11.9: o rascunho sobrevive à troca de aba, mas não a recarregar o app (só memória)',
    (t) async {
      await abrirHoje(t);
      await escrever(t, textoValido);
      await adicionarFoto(t);

      await irPara(t, '/perfil');
      await irPara(t, '/hoje');

      expect(controladorDoTexto(t).text, textoValido);
      expect(find.byKey(const Key('foto-escolhida-0')), findsOneWidget);

      // "recarregar": o app inteiro é descartado e aberto de novo
      await t.pumpWidget(const SizedBox());
      await abrirHoje(t);

      expect(controladorDoTexto(t).text, isEmpty);
      expect(find.byKey(const Key('foto-escolhida-0')), findsNothing);
    },
  );
}
