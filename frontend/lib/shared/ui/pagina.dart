import 'package:flutter/material.dart';

/// Conteúdo centralizado, com largura máxima e rolagem só na vertical (NFR-RESP-1: de 360 a 1280 px).
class Pagina extends StatelessWidget {
  const Pagina({required this.filhos, super.key});

  final List<Widget> filhos;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.topCenter,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 480),
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: filhos,
          ),
        ),
      ),
    );
  }
}

/// Mensagem de erro ou de confirmação, anunciada pelo leitor de tela quando aparece.
class Mensagem extends StatelessWidget {
  const Mensagem(this.texto, {this.erro = false, super.key});

  final String? texto;
  final bool erro;

  @override
  Widget build(BuildContext context) {
    final t = texto;
    if (t == null) return const SizedBox.shrink();
    final esquema = Theme.of(context).colorScheme;
    return Semantics(
      liveRegion: true,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 8),
        child: Text(
          t,
          style: TextStyle(color: erro ? esquema.error : esquema.onSurface),
        ),
      ),
    );
  }
}

Widget titulo(BuildContext context, String texto) => Semantics(
  header: true,
  child: Text(texto, style: Theme.of(context).textTheme.headlineSmall),
);
