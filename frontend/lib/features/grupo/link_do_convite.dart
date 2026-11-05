import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Monta o link do convite com o código **no fragmento** (`#/convite/<código>`), que o navegador nunca envia
/// ao servidor, ao Traefik ou a logs. Em teste é substituído por um link fixo.
final linkDoConviteProvider = Provider<String Function(String codigo)>((ref) {
  return (codigo) {
    final base = Uri.base;
    return '${base.origin}${base.path}#/convite/$codigo';
  };
});
