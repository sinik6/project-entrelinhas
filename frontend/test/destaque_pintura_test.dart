// [008] REQ-15.3, REQ-15.7, PROP-10: pintura dos destaques sobre o texto visível (posições em pontos de código).
import 'dart:math';

import 'package:entrelinhas/features/destaques/modelos.dart';
import 'package:entrelinhas/features/destaques/pintura.dart';
import 'package:entrelinhas/features/hoje/modelos.dart';
import 'package:entrelinhas/shared/texto.dart';
import 'package:entrelinhas/shared/ui/cores.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'suporte/api_falsa.dart';

Destaque d(String id, int inicio, int fim, String texto) => destaqueDe(
  id: id,
  inicio: inicio,
  fim: fim,
  trecho: fatiaPorPontos(texto, inicio, fim),
);

void main() {
  test('[008] REQ-15.3: sem destaques o texto é um segmento só, sem marca', () {
    final s = segmentar('abcdef', const []);

    expect(s, hasLength(1));
    expect((s[0].inicio, s[0].fim, s[0].topo), (0, 6, null));
  });

  test(
    '[008] REQ-15.3: um destaque parte o texto em antes, marcado e depois',
    () {
      const t = 'abcdefghij';
      final s = segmentar(t, [d('a', 2, 5, t)]);

      expect(
        [for (final x in s) t.substring(x.inicio, x.fim)],
        ['ab', 'cde', 'fghij'],
      );
      expect([for (final x in s) x.topo?.id], [null, 'a', null]);
    },
  );

  test(
    '[008] PROP-10: posições em pontos de código viram UTF-16 certo, com emoji',
    () {
      const t = 'Oi 😀 tudo bem hoje, 😀 certo.';
      final s = segmentar(t, [d('a', 5, 18, t)]);

      final marcado = s.firstWhere((x) => x.topo != null);
      expect(t.substring(marcado.inicio, marcado.fim), 'tudo bem hoje');
    },
  );

  test('[008] REQ-15.7: onde dois destaques se sobrepõem, o mais curto fica por cima', () {
    const t = 'abcdefghijklmnop';
    final longo = d('longo', 2, 12, t);
    final curto = d('curto', 5, 8, t);
    final s = segmentar(t, [longo, curto]);

    final topos = {for (final x in s) t.substring(x.inicio, x.fim): x.topo?.id};
    expect(topos['ab'], isNull);
    expect(topos['cde'], 'longo');
    expect(topos['fgh'], 'curto');
    expect(topos['ijkl'], 'longo');
    final meio = s.firstWhere((x) => t.substring(x.inicio, x.fim) == 'fgh');
    expect(meio.cobrindo.map((e) => e.id), containsAll(['longo', 'curto']));
  });

  test(
    '[008] REQ-15.7: o toque resolve pelo menor intervalo que contém o ponto',
    () {
      const t = 'abcdefghijklmnop';
      final ds = [d('longo', 2, 12, t), d('curto', 5, 8, t)];

      expect(destaqueEm(t, ds, 6)?.id, 'curto');
      expect(destaqueEm(t, ds, 3)?.id, 'longo');
      expect(destaqueEm(t, ds, 0), isNull);
      expect(destaquesEm(t, ds, 6).map((e) => e.id), ['curto', 'longo']);
      expect(destaqueEm(t, ds, 12), isNull, reason: 'o fim é exclusivo');
    },
  );

  test(
    '[008] REQ-15.3: destaque fora do texto é ignorado em vez de quebrar',
    () {
      const t = 'abc';
      final s = segmentar(t, [destaqueDe(id: 'x', inicio: 1, fim: 99)]);

      expect(s.map((x) => x.topo), everyElement(isNull));
      expect(s.last.fim, 3);
    },
  );

  test('[008] REQ-15.3: o texto sobre o fundo translúcido tem contraste de pelo menos 4,5 em todas as cores sugeridas, nos dois temas', () {
    for (final tema in [Brightness.light, Brightness.dark]) {
      final esquema = ColorScheme.fromSeed(
        seedColor: const Color(0xFF4D7C0F),
        brightness: tema,
      );
      for (final hex in coresSugeridas) {
        final fundo = fundoDoDestaque(corDeTexto(hex), esquema.surface);
        expect(
          contraste(esquema.onSurface, fundo),
          greaterThanOrEqualTo(4.5),
          reason: '$hex no tema ${tema.name}',
        );
      }
    }
  });

  test('[008] REQ-15.3: contraste de preto com branco é 21', () {
    expect(contraste(Colors.black, Colors.white), closeTo(21, 0.01));
  });

  test('[008] PROP-10: sorteio de textos e destaques; o segmento marcado é exatamente o trecho da API', () {
    final r = Random(8008);
    const pedacos = ['a', 'é', 'é', '😀', '🇧🇷', '\n', ' ', 'zé', '日本'];
    for (var rodada = 0; rodada < 300; rodada++) {
      final t = List.generate(
        3 + r.nextInt(10),
        (_) => pedacos[r.nextInt(pedacos.length)],
      ).join();
      final n = tamanhoEmPontos(t);
      final a = r.nextInt(n);
      final b = a + 1 + r.nextInt(n - a);
      final dest = d('x', a, b, t);

      final marcados = segmentar(t, [
        dest,
      ]).where((x) => x.topo != null).toList();

      expect(marcados, hasLength(1), reason: 'rodada $rodada');
      expect(
        t.substring(marcados.single.inicio, marcados.single.fim),
        dest.trecho,
        reason: 'rodada $rodada',
      );
      expect(utf16ParaPontos(t, marcados.single.inicio), a);
    }
  });

  group('[008] REQ-15.1: texto visível do registro', () {
    test('parceiro: o texto que veio da API, sem deslocamento', () {
      final v = visivelDoRegistro(registroDe(meu: false, texto: 'só isto'))!;

      expect((v.texto, v.base), ('só isto', 0));
    });

    test('autor em full: o texto todo', () {
      final v = visivelDoRegistro(registroDe(texto: 'tudo aqui'))!;

      expect((v.texto, v.base, v.completo), ('tudo aqui', 0, 'tudo aqui'));
    });

    test('autor em partial: só o trecho, com o deslocamento em UTF-16 (emoji antes)', () {
      final v = visivelDoRegistro(
        registroDe(
          visibilidade: Visibilidade.trecho,
          texto: 'Oi 😀 tudo bem hoje, certo.',
          trecho: const Trecho(inicio: 5, fim: 18),
        ),
      )!;

      expect(v.texto, 'tudo bem hoje');
      expect(v.base, 6);
      expect(v.completo, 'Oi 😀 tudo bem hoje, certo.');
    });

    test('registro privado do parceiro não tem texto visível', () {
      expect(
        visivelDoRegistro(
          registroDe(
            meu: false,
            visibilidade: Visibilidade.privado,
            texto: null,
          ),
        ),
        isNull,
      );
    });
  });
}
