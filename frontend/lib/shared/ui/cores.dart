import 'package:flutter/material.dart';

/// Cores sugeridas: todas passam na regra do servidor (contraste de 3 para 1 nos dois temas) e duas
/// quaisquer delas têm diferença de cor acima do mínimo, então nunca batem na trava do parceiro.
const coresSugeridas = <String>[
  '#B45309',
  '#4D7C0F',
  '#0E7490',
  '#9333EA',
  '#BE185D',
  '#DC2626',
  '#2563EB',
  '#059669',
];

Color corDeTexto(String hex) =>
    Color(int.parse('FF${hex.substring(1)}', radix: 16));

/// Escolha de cor por sugestão (cada uma com área de toque de 48 px e rótulo para leitor de tela).
class PaletaDeCores extends StatelessWidget {
  const PaletaDeCores({required this.aoEscolher, this.atual, super.key});

  final ValueChanged<String> aoEscolher;
  final String? atual;

  @override
  Widget build(BuildContext context) {
    final esquema = Theme.of(context).colorScheme;
    return Wrap(
      children: [
        for (final hex in coresSugeridas)
          Semantics(
            button: true,
            selected: atual?.toUpperCase() == hex,
            label: 'Usar a cor $hex',
            excludeSemantics: true,
            child: InkWell(
              customBorder: const CircleBorder(),
              onTap: () => aoEscolher(hex),
              child: SizedBox(
                width: 48,
                height: 48,
                child: Center(
                  child: Container(
                    width: 32,
                    height: 32,
                    decoration: BoxDecoration(
                      color: corDeTexto(hex),
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: atual?.toUpperCase() == hex
                            ? esquema.onSurface
                            : Colors.transparent,
                        width: 3,
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
      ],
    );
  }
}
