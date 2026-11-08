// Ponte com o navegador para o Web Push (spec 010, ADR-0012). O app só enxerga esta interface; os testes usam uma falsa.
// Nada daqui guarda dado do diário: só a assinatura do aparelho, que vai ao servidor.
import 'package:entrelinhas/shared/push/push_api_stub.dart'
    if (dart.library.js_interop) 'package:entrelinhas/shared/push/push_api_web.dart'
    as plataforma;
import 'package:flutter_riverpod/flutter_riverpod.dart';

enum SuporteDePush {
  /// O navegador não sabe fazer Web Push.
  semSuporte,

  /// iPhone/iPad fora da tela inicial: o push só funciona com o app instalado (iOS 16.4 ou mais novo).
  precisaInstalar,

  disponivel,
}

enum PermissaoDePush { naoPerguntada, concedida, negada }

/// O que o navegador entrega ao assinar (o formato que o servidor valida: spec 010, REQ-18.3).
class AssinaturaDoNavegador {
  const AssinaturaDoNavegador({
    required this.endpoint,
    required this.p256dh,
    required this.auth,
  });

  final String endpoint;
  final String p256dh;
  final String auth;
}

abstract class PushApi {
  SuporteDePush get suporte;

  Future<PermissaoDePush> permissao();

  /// Pede a permissão ao navegador (só depois de um gesto da pessoa).
  Future<PermissaoDePush> pedirPermissao();

  /// A assinatura deste aparelho, se já houver uma.
  Future<AssinaturaDoNavegador?> assinaturaAtual();

  /// Registra o service worker, assina com a chave pública do servidor (base64url) e devolve a assinatura.
  Future<AssinaturaDoNavegador> assinar(String chavePublica);

  /// Cancela a assinatura no navegador.
  Future<void> cancelar();
}

final pushApiProvider = Provider<PushApi>((ref) => plataforma.criarPushApi());
