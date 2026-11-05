// Escolha de foto (spec 004, ADR-0008). O app só enxerga esta interface; os testes usam um seletor de mentira.
import 'dart:typed_data';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';

class FotoEscolhida {
  const FotoEscolhida({
    required this.bytes,
    required this.nome,
    required this.tipo,
  });

  final Uint8List bytes;
  final String nome;
  final String tipo;
}

abstract class SeletorDeFoto {
  /// Abre o seletor do navegador. `null` quando a pessoa fecha sem escolher.
  Future<FotoEscolhida?> escolher();
}

class SeletorImagePicker implements SeletorDeFoto {
  SeletorImagePicker({ImagePicker? picker}) : _picker = picker ?? ImagePicker();

  final ImagePicker _picker;

  @override
  Future<FotoEscolhida?> escolher() async {
    final arquivo = await _picker.pickImage(source: ImageSource.gallery);
    if (arquivo == null) return null;
    return FotoEscolhida(
      bytes: await arquivo.readAsBytes(),
      nome: arquivo.name,
      tipo: arquivo.mimeType ?? 'image/jpeg',
    );
  }
}

final seletorDeFotoProvider = Provider<SeletorDeFoto>(
  (ref) => SeletorImagePicker(),
);
