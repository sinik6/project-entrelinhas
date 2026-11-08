// Cartão de um registro (spec 006, REQ-12.2 a 12.5): a visão do autor ou a do parceiro, exatamente como a API devolveu.
// O texto é desenhado como `Text`, nunca como HTML ou marcação (NFR-TELA-2, ABU-13).
import 'package:entrelinhas/features/destaques/leitor_page.dart';
import 'package:entrelinhas/features/destaques/pintura.dart';
import 'package:entrelinhas/features/diario/foto_tela_cheia.dart';
import 'package:entrelinhas/features/hoje/modelos.dart';
import 'package:entrelinhas/shared/relogio.dart';
import 'package:entrelinhas/shared/texto.dart';
import 'package:entrelinhas/shared/ui/avatar.dart';
import 'package:entrelinhas/shared/ui/cores.dart';
import 'package:flutter/material.dart';

const avisoDePrivado = 'Enviado, mas mantido privado pelo autor';

String quemLe(String visibilidade) => switch (visibilidade) {
  Visibilidade.todos => 'todo o grupo',
  Visibilidade.privado => 'só você',
  _ => 'só um trecho',
};

class CartaoDeRegistro extends StatelessWidget {
  const CartaoDeRegistro({required this.registro, super.key});

  final Registro registro;

  /// O texto, com o trecho escolhido marcado quando é o próprio autor olhando (pontos de código -> UTF-16).
  InlineSpan _texto(BuildContext context, String texto) {
    final trecho = registro.trecho;
    if (!registro.meu ||
        trecho == null ||
        trecho.inicio < 0 ||
        trecho.inicio >= trecho.fim ||
        trecho.fim > tamanhoEmPontos(texto)) {
      return TextSpan(text: texto);
    }
    final esquema = Theme.of(context).colorScheme;
    final inicio = pontosParaUtf16(texto, trecho.inicio);
    final fim = pontosParaUtf16(texto, trecho.fim);
    return TextSpan(
      children: [
        TextSpan(text: texto.substring(0, inicio)),
        TextSpan(
          text: texto.substring(inicio, fim),
          style: TextStyle(
            backgroundColor: esquema.primaryContainer,
            color: esquema.onPrimaryContainer,
          ),
        ),
        TextSpan(text: texto.substring(fim)),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final r = registro;
    final tema = Theme.of(context);
    final texto = r.texto;
    return Card(
      key: Key('registro-${r.id}'),
      clipBehavior: Clip.antiAlias,
      child: IntrinsicHeight(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              key: Key('faixa-${r.id}'),
              width: 6,
              decoration: BoxDecoration(color: corDeTexto(r.autor.cor)),
            ),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Avatar(
                          nome: r.autor.nome,
                          cor: r.autor.cor,
                          fotoUrl: r.autor.fotoUrl,
                          tamanho: 36,
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                r.autor.nome,
                                style: tema.textTheme.titleMedium,
                              ),
                              Text(
                                diaEHora(r.entregueEm),
                                style: tema.textTheme.bodySmall,
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    if (texto != null)
                      Text.rich(
                        _texto(context, texto),
                        key: Key('texto-${r.id}'),
                      )
                    else
                      Text(r.aviso ?? avisoDePrivado),
                    if (visivelDoRegistro(r) != null) ...[
                      const SizedBox(height: 8),
                      Align(
                        alignment: Alignment.centerLeft,
                        child: OutlinedButton(
                          onPressed: () => abrirLeitorDoRegistro(context, r),
                          child: const Text('Ler e destacar'),
                        ),
                      ),
                    ],
                    if (!r.meu &&
                        texto != null &&
                        r.visibilidade == Visibilidade.trecho) ...[
                      const SizedBox(height: 8),
                      Text(
                        'Mostrando só o trecho que ${r.autor.nome} escolheu',
                        style: tema.textTheme.bodySmall,
                      ),
                    ],
                    if (r.meu) ...[
                      const SizedBox(height: 8),
                      Text(
                        'Quem lê: ${quemLe(r.visibilidade)}',
                        style: tema.textTheme.bodySmall,
                      ),
                    ],
                    if (r.fotos.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          for (final id in r.fotos)
                            MiniaturaDaFoto(fotoId: id, autor: r.autor.nome),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
