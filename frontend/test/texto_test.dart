// [006] PROP-8, REQ-11.4, CTL-42: conversão UTF-16 <-> pontos de código e ajuste da seleção a grafemas.
import 'dart:math';

import 'package:characters/characters.dart';
import 'package:entrelinhas/shared/texto.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

const emoji = '😀'; // 1 ponto de código, 2 unidades UTF-16
const familia =
    '👨‍👩‍👧'; // 5 pontos de código (3 emojis + 2 junções), 1 grafema
const bandeira = '🇧🇷'; // 2 pontos de código, 1 grafema
const aComposto = 'á'; // "á" decomposto: 2 pontos de código, 1 grafema
const japones = '日本語';

final textos = <String, String>{
  'ascii': 'Hoje foi um dia calmo.',
  'emoji': 'oi $emoji tudo bem $emoji',
  'familia': 'minha $familia em casa',
  'bandeira': 'viagem $bandeira $bandeira fim',
  'acento composto': 'cafe$aComposto e café',
  'quebras': 'linha um\n\nlinha dois\tcom tab\nfim',
  'japonês': '$japones e mais $japones',
};

/// Posições UTF-16 onde o texto pode ser cortado sem partir um grafema.
Set<int> fronteirasDeGrafema(String texto) {
  final posicoes = <int>{0};
  var soma = 0;
  for (final g in texto.characters) {
    soma += g.length;
    posicoes.add(soma);
  }
  return posicoes;
}

void main() {
  group('[006] REQ-11.4: quebras de linha', () {
    test('\\r\\n e \\r viram \\n; \\n fica como está', () {
      expect(normalizarQuebras('a\r\nb\rc\nd'), 'a\nb\nc\nd');
      expect(normalizarQuebras('\r\n\r\n'), '\n\n');
      expect(normalizarQuebras('sem quebra'), 'sem quebra');
    });

    test('nenhum \\r sobra', () {
      expect(normalizarQuebras('\r\r\n\n\r'), isNot(contains('\r')));
    });
  });

  group('[006] PROP-8: contagem e conversão de posições', () {
    test('emoji conta 1 ponto de código e ocupa 2 unidades UTF-16', () {
      expect(emoji.length, 2);
      expect(tamanhoEmPontos(emoji), 1);
      expect(tamanhoEmPontos(familia), 5);
      expect(tamanhoEmPontos(bandeira), 2);
      expect(tamanhoEmPontos(aComposto), 2);
      expect(tamanhoEmPontos('abc'), 3);
      expect(tamanhoEmPontos(''), 0);
    });

    test('utf16ParaPontos nos limites de ponto de código', () {
      const t = 'a${emoji}b';
      expect(utf16ParaPontos(t, 0), 0);
      expect(utf16ParaPontos(t, 1), 1);
      expect(utf16ParaPontos(t, 3), 2);
      expect(utf16ParaPontos(t, 4), 3);
    });

    test('pontosParaUtf16 é a volta', () {
      const t = 'a${emoji}b';
      expect(pontosParaUtf16(t, 0), 0);
      expect(pontosParaUtf16(t, 1), 1);
      expect(pontosParaUtf16(t, 2), 3);
      expect(pontosParaUtf16(t, 3), 4);
    });

    test(
      'índice no meio de um par substituto recua para o início do ponto',
      () {
        const t = 'a${emoji}b';
        // 2 está entre as duas metades do emoji: nunca conta como ponto inteiro a mais
        expect(utf16ParaPontos(t, 2), 1);
      },
    );

    test('fora do alcance falha em vez de devolver lixo', () {
      expect(() => utf16ParaPontos('abc', -1), throwsRangeError);
      expect(() => utf16ParaPontos('abc', 4), throwsRangeError);
      expect(() => pontosParaUtf16('abc', 4), throwsRangeError);
      expect(() => pontosParaUtf16('abc', -1), throwsRangeError);
    });

    test(
      'fatiaPorPontos corta em pontos de código, não em unidades UTF-16',
      () {
        const t = 'a${emoji}b$emoji';
        expect(fatiaPorPontos(t, 1, 2), emoji);
        expect(fatiaPorPontos(t, 0, 3), 'a${emoji}b');
        expect(fatiaPorPontos(t, 2, 4), 'b$emoji');
        expect(fatiaPorPontos(t, 0, 4), t);
      },
    );

    test('[PROP-8] ida e volta em todos os limites, nos textos de exemplo', () {
      for (final MapEntry(key: nome, value: texto) in textos.entries) {
        var i = 0;
        while (i <= texto.length) {
          final p = utf16ParaPontos(texto, i);
          expect(pontosParaUtf16(texto, p), i, reason: '$nome em $i');
          if (i == texto.length) break;
          i += String.fromCharCode(texto.runes.elementAt(p)).length;
        }
        expect(
          utf16ParaPontos(texto, texto.length),
          tamanhoEmPontos(texto),
          reason: nome,
        );
      }
    });
  });

  group('[006] REQ-11.4, CTL-42: ajuste da seleção para dentro', () {
    test('seleção que já está em fronteiras não muda', () {
      const t = 'ola mundo';
      final r = trechoDaSelecao(t, 4, 9)!;
      expect(r.inicioUtf16, 4);
      expect(r.fimUtf16, 9);
      expect(r.inicioPontos, 4);
      expect(r.fimPontos, 9);
      expect(t.substring(r.inicioUtf16, r.fimUtf16), 'mundo');
    });

    test('seleção invertida (arrastar para trás) é a mesma seleção', () {
      final r = trechoDaSelecao('ola mundo', 9, 4)!;
      expect(r.inicioUtf16, 4);
      expect(r.fimUtf16, 9);
    });

    test('seleção vazia não é trecho', () {
      expect(trechoDaSelecao('ola mundo', 3, 3), isNull);
    });

    test('começo no meio de um emoji encolhe para depois dele', () {
      const t = 'a${emoji}b';
      final r = trechoDaSelecao(t, 2, 4)!; // começa no meio do emoji
      expect(t.substring(r.inicioUtf16, r.fimUtf16), 'b');
      expect(r.inicioUtf16, 3);
    });

    test('fim no meio de um emoji encolhe para antes dele', () {
      const t = 'a${emoji}b';
      final r = trechoDaSelecao(t, 0, 2)!; // termina no meio do emoji
      expect(t.substring(r.inicioUtf16, r.fimUtf16), 'a');
    });

    test('seleção só de metade de um emoji vira vazia (nada para mostrar)', () {
      expect(trechoDaSelecao('a${emoji}b', 1, 2), isNull);
    });

    test('família: cortar no meio não deixa pedaço de grafema', () {
      final t = 'x${familia}y';
      // início dentro da família (depois do primeiro emoji), fim no fim do texto
      final r = trechoDaSelecao(t, 3, t.length)!;
      expect(t.substring(r.inicioUtf16, r.fimUtf16), 'y');
    });

    test('bandeira: meia bandeira não aparece', () {
      final t = 'x${bandeira}y';
      // seleciona só a primeira metade da bandeira (4 unidades UTF-16 → fica 1+2)
      final r = trechoDaSelecao(t, 0, 3)!;
      expect(t.substring(r.inicioUtf16, r.fimUtf16), 'x');
    });

    test('acento composto: a letra e o acento ficam juntos ou saem juntos', () {
      const t = 'ca$aComposto fe'; // "caá fe" com "á" decomposto
      final i = t.indexOf('á');
      // seleção que começa entre "a" e o acento
      final r = trechoDaSelecao(t, i + 1, t.length)!;
      expect(t.substring(r.inicioUtf16, r.fimUtf16), ' fe');
      // seleção que termina entre "a" e o acento
      final s = trechoDaSelecao(t, 0, i + 1)!;
      expect(t.substring(s.inicioUtf16, s.fimUtf16), 'ca');
    });

    test('o ajuste nunca cresce: o trecho está dentro da seleção original', () {
      for (final texto in textos.values) {
        for (var a = 0; a <= texto.length; a++) {
          for (var b = a; b <= texto.length; b++) {
            final r = trechoDaSelecao(texto, a, b);
            if (r == null) continue;
            expect(r.inicioUtf16, greaterThanOrEqualTo(a));
            expect(r.fimUtf16, lessThanOrEqualTo(b));
          }
        }
      }
    });
  });

  group('[006] PROP-8 (sorteio com semente fixa)', () {
    final pedacos = [
      'a',
      'z',
      ' ',
      '\n',
      '\t',
      'ç',
      aComposto,
      emoji,
      '👍🏽', // emoji com tom de pele: 1 grafema, 2 pontos
      familia,
      bandeira,
      japones,
    ];

    String sorteia(Random r) {
      final n = 1 + r.nextInt(14);
      return List.generate(n, (_) => pedacos[r.nextInt(pedacos.length)]).join();
    }

    test('o trecho enviado, fatiado em pontos, é igual à prévia; tudo em fronteira de grafema', () {
      final r = Random(20261105);
      var contados = 0;
      for (var rodada = 0; rodada < 600; rodada++) {
        final texto = sorteia(r);
        final a = r.nextInt(texto.length + 1);
        final b = r.nextInt(texto.length + 1);
        final trecho = trechoDaSelecao(texto, a, b);
        if (trecho == null) continue;
        contados++;

        final previa = texto.substring(trecho.inicioUtf16, trecho.fimUtf16);
        // o que a API fatiaria (em pontos de código) é exatamente a prévia
        expect(
          fatiaPorPontos(texto, trecho.inicioPontos, trecho.fimPontos),
          previa,
          reason: 'texto=${texto.runes.toList()} sel=$a..$b',
        );
        // ida e volta nas pontas
        expect(utf16ParaPontos(texto, trecho.inicioUtf16), trecho.inicioPontos);
        expect(pontosParaUtf16(texto, trecho.fimPontos), trecho.fimUtf16);
        // o trecho está dentro da seleção pedida
        final menor = min(a, b);
        final maior = max(a, b);
        expect(trecho.inicioUtf16, greaterThanOrEqualTo(menor));
        expect(trecho.fimUtf16, lessThanOrEqualTo(maior));
        // as pontas estão em fronteira de grafema do texto inteiro
        final fronteiras = fronteirasDeGrafema(texto);
        expect(fronteiras, contains(trecho.inicioUtf16), reason: 'início');
        expect(fronteiras, contains(trecho.fimUtf16), reason: 'fim');
        expect(previa.runes.length, trecho.fimPontos - trecho.inicioPontos);
        expect(previa, isNotEmpty);
      }
      // o sorteio precisa ter exercitado muitos casos reais, não só vazios
      expect(contados, greaterThan(300));
    });

    test('sem trecho com seleção que cabe inteira em um grafema partido', () {
      expect(trechoDaSelecao(familia, 1, 3), isNull);
    });
  });

  group(r'[006] REQ-11.4: formatador que tira o \r do campo', () {
    const formatador = FormatadorDeQuebras();
    TextEditingValue formatar(String texto, int base, [int? extensao]) =>
        formatador.formatEditUpdate(
          TextEditingValue.empty,
          TextEditingValue(
            text: texto,
            selection: TextSelection(
              baseOffset: base,
              extentOffset: extensao ?? base,
            ),
          ),
        );

    test(r'troca \r\n e \r por \n e leva o cursor junto', () {
      final v = formatar('a\r\nb\rc', 6);
      expect(v.text, 'a\nb\nc');
      expect(v.selection.baseOffset, 5);
      expect(v.selection.extentOffset, 5);
    });

    test(r'seleção em volta de um \r\n continua cobrindo o mesmo texto', () {
      final v = formatar('ab\r\ncd', 0, 6);
      expect(v.text, 'ab\ncd');
      expect(v.selection.start, 0);
      expect(v.selection.end, 5);
    });

    test(r'cursor entre o \r e o \n fica antes da quebra (nunca depois)', () {
      final v = formatar('ab\r\ncd', 3);
      expect(v.text, 'ab\ncd');
      expect(v.selection.baseOffset, 2);
    });

    test(r'texto sem \r passa sem mudança', () {
      final v = formatar('sem mudança\nok', 4, 8);
      expect(v.text, 'sem mudança\nok');
      expect(v.selection.start, 4);
      expect(v.selection.end, 8);
    });
  });

  group('[006] REQ-11.2: caracteres úteis', () {
    test('conta pontos de código sem os espaços e quebras das pontas', () {
      expect(caracteresUteis('  oi  '), 2);
      expect(caracteresUteis('\n\n$emoji$emoji\n'), 2);
      expect(caracteresUteis('123456789'), 9);
      expect(caracteresUteis('   '), 0);
    });
  });
}
