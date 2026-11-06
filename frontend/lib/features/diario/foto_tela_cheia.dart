// Foto de manuscrito: miniatura que abre em tela cheia com zoom (spec 006, REQ-12.5). A foto vem da API (spec 004/005),
// que só a entrega a quem pode vê-la; o app não guarda nada dela.
import 'package:entrelinhas/shared/ui/avatar.dart';
import 'package:flutter/material.dart';

String _urlDaFotoDoRegistro(String id) => urlDaFoto('fotos/$id/arquivo');

String _rotulo(String autor) => 'Foto do manuscrito de $autor';

class MiniaturaDaFoto extends StatelessWidget {
  const MiniaturaDaFoto({required this.fotoId, required this.autor, super.key});

  final String fotoId;
  final String autor;

  @override
  Widget build(BuildContext context) {
    final esquema = Theme.of(context).colorScheme;
    return Semantics(
      key: Key('foto-$fotoId'),
      container: true,
      button: true,
      image: true,
      label: _rotulo(autor),
      excludeSemantics: true,
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: () => showDialog<void>(
          context: context,
          builder: (_) => FotoTelaCheia(fotoId: fotoId, autor: autor),
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: SizedBox(
            width: 88,
            height: 88,
            child: Image.network(
              _urlDaFotoDoRegistro(fotoId),
              fit: BoxFit.cover,
              errorBuilder: (_, _, _) => ColoredBox(
                color: esquema.surfaceContainerHighest,
                child: Icon(
                  Icons.image_outlined,
                  color: esquema.onSurfaceVariant,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class FotoTelaCheia extends StatelessWidget {
  const FotoTelaCheia({required this.fotoId, required this.autor, super.key});

  final String fotoId;
  final String autor;

  @override
  Widget build(BuildContext context) {
    return Dialog.fullscreen(
      backgroundColor: Colors.black,
      child: Stack(
        children: [
          Positioned.fill(
            child: Semantics(
              key: const Key('foto-tela-cheia'),
              container: true,
              image: true,
              label: _rotulo(autor),
              child: InteractiveViewer(
                minScale: 1,
                maxScale: 5,
                child: Image.network(
                  _urlDaFotoDoRegistro(fotoId),
                  fit: BoxFit.contain,
                  errorBuilder: (_, _, _) => const Center(
                    child: Text(
                      'Não foi possível carregar a foto.',
                      style: TextStyle(color: Colors.white),
                    ),
                  ),
                ),
              ),
            ),
          ),
          Positioned(
            top: 8,
            right: 8,
            child: IconButton.filledTonal(
              tooltip: 'Fechar',
              icon: const Icon(Icons.close),
              onPressed: () => Navigator.of(context).pop(),
            ),
          ),
        ],
      ),
    );
  }
}
