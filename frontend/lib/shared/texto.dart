// Texto do registro (spec 006, ADR-0009 e ADR-0011): conversão UTF-16 <-> pontos de código e ajuste da seleção a grafemas.
//
// O campo de texto do Flutter conta em unidades UTF-16; a API conta em pontos de código Unicode. Toda conversão passa por aqui,
// para existir um único lugar a testar (PROP-8, CTL-42).
import 'package:characters/characters.dart';
import 'package:flutter/services.dart';

/// `\r\n` e `\r` viram `\n`: a API recusa `\r` e as posições do trecho são calculadas sobre o texto já assim.
String normalizarQuebras(String texto) =>
    texto.replaceAll('\r\n', '\n').replaceAll('\r', '\n');

/// Quantidade de pontos de código (um emoji conta 1, mesmo ocupando 2 unidades UTF-16).
int tamanhoEmPontos(String texto) => texto.runes.length;

/// Caracteres que contam para o mínimo de 10 do servidor: sem espaços e quebras nas pontas.
int caracteresUteis(String texto) => tamanhoEmPontos(texto.trim());

bool _alta(int unidade) => unidade >= 0xD800 && unidade <= 0xDBFF;
bool _baixa(int unidade) => unidade >= 0xDC00 && unidade <= 0xDFFF;

/// Tamanho, em unidades UTF-16, do ponto de código que começa em `i`.
int _tamanhoDoPonto(String texto, int i) =>
    _alta(texto.codeUnitAt(i)) &&
        i + 1 < texto.length &&
        _baixa(texto.codeUnitAt(i + 1))
    ? 2
    : 1;

/// Posição UTF-16 -> posição em pontos de código. Um índice no meio de um par substituto conta como o início do ponto.
int utf16ParaPontos(String texto, int indice) {
  RangeError.checkValueInInterval(indice, 0, texto.length, 'indice');
  var pontos = 0;
  var unidades = 0;
  while (unidades < indice) {
    final tamanho = _tamanhoDoPonto(texto, unidades);
    if (unidades + tamanho > indice) break;
    unidades += tamanho;
    pontos++;
  }
  return pontos;
}

/// Posição em pontos de código -> posição UTF-16.
int pontosParaUtf16(String texto, int pontos) {
  RangeError.checkValueInInterval(pontos, 0, tamanhoEmPontos(texto), 'pontos');
  var unidades = 0;
  for (var i = 0; i < pontos; i++) {
    unidades += _tamanhoDoPonto(texto, unidades);
  }
  return unidades;
}

/// O mesmo corte que a API faz: `texto[inicio:fim]` em pontos de código.
String fatiaPorPontos(String texto, int inicio, int fim) {
  RangeError.checkValueInInterval(inicio, 0, fim, 'inicio');
  return texto.substring(
    pontosParaUtf16(texto, inicio),
    pontosParaUtf16(texto, fim),
  );
}

/// Trecho já ajustado a grafemas, nas duas contagens.
class TrechoSelecionado {
  const TrechoSelecionado({
    required this.inicioUtf16,
    required this.fimUtf16,
    required this.inicioPontos,
    required this.fimPontos,
  });

  final int inicioUtf16;
  final int fimUtf16;
  final int inicioPontos;
  final int fimPontos;
}

/// Seleção do campo -> trecho para a API.
///
/// As pontas são empurradas **para dentro**, até a fronteira de grafema mais próxima (nunca para fora): na dúvida o
/// parceiro lê menos, não mais (ADR-0011). Devolve `null` quando não sobra nada. `texto` já deve ter as quebras normalizadas.
TrechoSelecionado? trechoDaSelecao(String texto, int a, int b) {
  final baixo = (a < b ? a : b).clamp(0, texto.length);
  final alto = (a < b ? b : a).clamp(0, texto.length);
  if (baixo >= alto) return null;

  var inicio = -1;
  var fim = -1;
  var posicao = 0;
  if (baixo == 0) inicio = 0;
  for (final grafema in texto.characters) {
    posicao += grafema.length;
    if (inicio < 0 && posicao >= baixo) inicio = posicao;
    if (posicao <= alto) fim = posicao;
  }
  if (inicio < 0 || fim <= inicio) return null;
  return TrechoSelecionado(
    inicioUtf16: inicio,
    fimUtf16: fim,
    inicioPontos: utf16ParaPontos(texto, inicio),
    fimPontos: utf16ParaPontos(texto, fim),
  );
}

/// Tira o `\r` do campo na hora da digitação ou da colagem e leva o cursor junto, para o texto e as posições
/// nunca divergirem (REQ-11.4).
class FormatadorDeQuebras extends TextInputFormatter {
  const FormatadorDeQuebras();

  @override
  TextEditingValue formatEditUpdate(
    TextEditingValue antigo,
    TextEditingValue novo,
  ) {
    final texto = novo.text;
    if (!texto.contains('\r')) return novo;

    int mapear(int i) {
      if (i < 0) return i;
      final prefixo = texto.substring(0, i);
      var n = normalizarQuebras(prefixo).length;
      // cursor entre o \r e o \n: fica antes da quebra
      if (prefixo.endsWith('\r') && i < texto.length && texto[i] == '\n') n--;
      return n;
    }

    final selecao = novo.selection;
    return TextEditingValue(
      text: normalizarQuebras(texto),
      selection: TextSelection(
        baseOffset: mapear(selecao.baseOffset),
        extentOffset: mapear(selecao.extentOffset),
        affinity: selecao.affinity,
        isDirectional: selecao.isDirectional,
      ),
    );
  }
}
