// Pintura dos destaques (spec 008): fatia o texto visível nas bordas dos destaques e decide qual aparece por cima.
// As posições dos destaques são em pontos de código do TEXTO VISÍVEL (ADR-0009); aqui viram UTF-16 para desenhar.
import 'package:entrelinhas/features/destaques/modelos.dart';
import 'package:entrelinhas/features/hoje/modelos.dart';
import 'package:entrelinhas/shared/texto.dart';
import 'package:flutter/painting.dart';

/// Pedaço do texto entre duas bordas de destaque, em UTF-16 do texto visível.
class Segmento {
  const Segmento({
    required this.inicio,
    required this.fim,
    required this.topo,
    required this.cobrindo,
  });

  final int inicio;
  final int fim;

  /// O destaque desenhado neste pedaço: o mais curto dos que o cobrem (`null` = sem destaque).
  final Destaque? topo;

  /// Todos os que o cobrem, do mais curto para o mais longo.
  final List<Destaque> cobrindo;
}

class _Faixa {
  const _Faixa(this.destaque, this.inicio, this.fim);

  final Destaque destaque;
  final int inicio;
  final int fim;

  int get tamanho => fim - inicio;
}

/// Destaques com posição válida para este texto, já em UTF-16. Os que não cabem no texto são ignorados:
/// a tela nunca quebra por causa de um dado estranho.
List<_Faixa> _faixas(String visivel, List<Destaque> destaques) {
  final total = tamanhoEmPontos(visivel);
  return [
    for (final d in destaques)
      if (d.inicio >= 0 && d.inicio < d.fim && d.fim <= total)
        _Faixa(
          d,
          pontosParaUtf16(visivel, d.inicio),
          pontosParaUtf16(visivel, d.fim),
        ),
  ];
}

int _porTamanho(_Faixa a, _Faixa b) => a.tamanho.compareTo(b.tamanho);

List<Segmento> segmentar(String visivel, List<Destaque> destaques) {
  final faixas = _faixas(visivel, destaques);
  final bordas = <int>{0, visivel.length};
  for (final f in faixas) {
    bordas
      ..add(f.inicio)
      ..add(f.fim);
  }
  final ordenadas = bordas.toList()..sort();
  final segmentos = <Segmento>[];
  for (var i = 0; i + 1 < ordenadas.length; i++) {
    final a = ordenadas[i];
    final b = ordenadas[i + 1];
    final cobrindo = faixas.where((f) => f.inicio <= a && b <= f.fim).toList()
      ..sort(_porTamanho);
    segmentos.add(
      Segmento(
        inicio: a,
        fim: b,
        topo: cobrindo.isEmpty ? null : cobrindo.first.destaque,
        cobrindo: [for (final f in cobrindo) f.destaque],
      ),
    );
  }
  return segmentos;
}

/// Destaques que cobrem o ponto (UTF-16, fim exclusivo), do mais curto para o mais longo.
List<Destaque> destaquesEm(
  String visivel,
  List<Destaque> destaques,
  int offset,
) {
  final achadas =
      _faixas(
          visivel,
          destaques,
        ).where((f) => f.inicio <= offset && offset < f.fim).toList()
        ..sort(_porTamanho);
  return [for (final f in achadas) f.destaque];
}

Destaque? destaqueEm(String visivel, List<Destaque> destaques, int offset) =>
    destaquesEm(visivel, destaques, offset).firstOrNull;

/// Fundo translúcido na cor de quem destacou, composto sobre o fundo do tema. O alfa é baixo de propósito: o texto
/// por cima precisa manter contraste de pelo menos 4,5 para 1 (WCAG 1.4.3); o sublinhado carrega a informação
/// que a cor sozinha não carrega (WCAG 1.4.1).
const alfaDoDestaque = 0.22;

Color fundoDoDestaque(Color autor, Color fundoDoTema) =>
    Color.alphaBlend(autor.withValues(alpha: alfaDoDestaque), fundoDoTema);

double contraste(Color a, Color b) {
  final la = a.computeLuminance();
  final lb = b.computeLuminance();
  final claro = la > lb ? la : lb;
  final escuro = la > lb ? lb : la;
  return (claro + 0.05) / (escuro + 0.05);
}

/// O texto que a pessoa pode destacar num registro e onde ele começa no texto mostrado.
class TextoVisivel {
  const TextoVisivel({
    required this.texto,
    required this.base,
    required this.completo,
  });

  /// O texto visível (as posições dos destaques são relativas a ele).
  final String texto;

  /// Onde o texto visível começa dentro de `completo`, em UTF-16 (0 quando é o texto todo).
  final int base;

  /// O texto como é mostrado na tela: o do autor tem o texto todo; o do parceiro, só o visível.
  final String completo;
}

/// `null` quando não há texto visível para destacar (registro privado).
TextoVisivel? visivelDoRegistro(Registro r) {
  final texto = r.texto;
  if (texto == null || r.visibilidade == Visibilidade.privado) return null;
  final trecho = r.trecho;
  if (r.meu && r.visibilidade == Visibilidade.trecho && trecho != null) {
    if (trecho.inicio < 0 ||
        trecho.inicio >= trecho.fim ||
        trecho.fim > tamanhoEmPontos(texto)) {
      return null;
    }
    final base = pontosParaUtf16(texto, trecho.inicio);
    final fim = pontosParaUtf16(texto, trecho.fim);
    return TextoVisivel(
      texto: texto.substring(base, fim),
      base: base,
      completo: texto,
    );
  }
  return TextoVisivel(texto: texto, base: 0, completo: texto);
}
