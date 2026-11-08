// Apoio dos testes de destaques (spec 008): abrir o leitor de um registro e selecionar texto nele.
import 'package:entrelinhas/features/destaques/modelos.dart';
import 'package:entrelinhas/features/hoje/modelos.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'api_falsa.dart';
import 'hoje_de_teste.dart';

const leitorTexto = Key('leitor-texto');

/// Abre o Diário com o registro dado e entra no leitor ("Ler e destacar").
Future<ApiFalsa> abrirLeitor(
  WidgetTester t,
  Registro registro, {
  List<Destaque> destaques = const [],
  ApiFalsa? api,
  Size tamanho = const Size(412, 900),
  Brightness brilho = Brightness.light,
}) async {
  final falsa = api ?? apiDaAna();
  falsa.registros.add(registro);
  falsa.destaques[registro.id] = List.of(destaques);
  await abrirDiario(t, api: falsa, tamanho: tamanho, brilho: brilho);
  await tocarBotao(t, 'Ler e destacar');
  return falsa;
}

TextField _campo(WidgetTester t) => t.widget<TextField>(
  find.descendant(
    of: find.byKey(leitorTexto),
    matching: find.byType(TextField),
  ),
);

TextEditingController controladorDoLeitor(WidgetTester t) =>
    _campo(t).controller!;

Future<void> selecionarNoLeitor(WidgetTester t, int inicio, int fim) async {
  controladorDoLeitor(t).selection = TextSelection(
    baseOffset: inicio,
    extentOffset: fim,
  );
  await t.pump();
}

/// Um toque num ponto do texto: o cursor vai para ali e o `onTap` do campo roda.
Future<void> tocarNoLeitor(WidgetTester t, int offset) async {
  controladorDoLeitor(t).selection = TextSelection.collapsed(offset: offset);
  _campo(t).onTap!();
  await t.pumpAndSettle();
}
