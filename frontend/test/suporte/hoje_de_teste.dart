// Apoio dos testes das telas Hoje e Diário (spec 006): sessão com grupo, escrita no campo e atalhos de toque.
import 'package:entrelinhas/shared/api/api.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'api_falsa.dart';
import 'app_de_teste.dart';
import 'seletor_falso.dart';

const textoValido = 'Hoje foi um dia calmo e bonito.';
const campoDoTexto = Key('campo-texto');

Grupo grupoDaAnaEBia() => grupoCom([
  const Membro(nome: 'Ana', cor: corVerde),
  const Membro(nome: 'Bia', cor: corAmbar),
]);

/// Ana, com grupo de dois, logada.
ApiFalsa apiDaAna() {
  final grupo = grupoDaAnaEBia();
  return ApiFalsa(
    sessao: perfilCompleto(grupo: grupo),
    grupoAtual: grupo,
  );
}

Future<ApiFalsa> abrirHoje(
  WidgetTester t, {
  ApiFalsa? api,
  SeletorFalso? seletor,
  Size tamanho = const Size(412, 900),
  Brightness brilho = Brightness.light,
}) async {
  final falsa = await abrirApp(
    t,
    api: api ?? apiDaAna(),
    seletor: seletor ?? SeletorFalso(escolha: fotoDeTeste()),
    tamanho: tamanho,
    brilho: brilho,
  );
  await irPara(t, '/hoje');
  return falsa;
}

Future<void> abrirDiario(
  WidgetTester t, {
  required ApiFalsa api,
  Size tamanho = const Size(412, 900),
  Brightness brilho = Brightness.light,
}) async {
  await abrirApp(t, api: api, tamanho: tamanho, brilho: brilho);
  await irPara(t, '/diario');
}

Future<void> escrever(WidgetTester t, String texto) async {
  await t.enterText(find.byKey(campoDoTexto), texto);
  await t.pumpAndSettle();
}

Future<void> tocarTexto(WidgetTester t, String texto) async {
  final alvo = find.text(texto);
  await t.ensureVisible(alvo.first);
  await t.tap(alvo.first);
  await t.pumpAndSettle();
}

Future<void> tocarBotao(WidgetTester t, String texto) async {
  final botao = find
      .ancestor(
        of: find.text(texto),
        matching: find.bySubtype<ButtonStyleButton>(),
      )
      .first;
  await t.ensureVisible(botao);
  await t.tap(botao);
  await t.pumpAndSettle();
}

Future<void> adicionarFoto(WidgetTester t) => tocarBotao(t, 'Adicionar foto');

TextEditingController controladorDoTexto(WidgetTester t) => t
    .widget<TextField>(
      find.descendant(
        of: find.byKey(campoDoTexto),
        matching: find.byType(TextField),
      ),
    )
    .controller!;

/// Seleciona no campo, como se a pessoa tivesse marcado o texto com o dedo.
Future<void> selecionar(WidgetTester t, int inicio, int fim) async {
  controladorDoTexto(t).selection = TextSelection(
    baseOffset: inicio,
    extentOffset: fim,
  );
  await t.pump();
}

/// Botão "Entregar" da página (não o do diálogo).
Finder get botaoEntregar => find.byKey(const Key('botao-entregar'));

bool entregarHabilitado(WidgetTester t) =>
    t.widget<ButtonStyleButton>(botaoEntregar).onPressed != null;

Finder get confirmarEntrega => find.descendant(
  of: find.byType(AlertDialog),
  matching: find.widgetWithText(FilledButton, 'Entregar'),
);

/// Texto + 1 foto + "Todo o grupo lê": tudo o que falta para entregar.
Future<void> preencherTudo(WidgetTester t, {String texto = textoValido}) async {
  await escrever(t, texto);
  await adicionarFoto(t);
  await tocarTexto(t, 'Todo o grupo lê');
}
