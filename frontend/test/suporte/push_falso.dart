// Web Push de mentira para os testes (spec 010): sem navegador, sem serviço de push; o teste decide as respostas.
import 'dart:async';

import 'package:entrelinhas/shared/push/push_api.dart';

class PushFalso implements PushApi {
  PushFalso({
    this.suporteDoNavegador = SuporteDePush.disponivel,
    this.permissaoAtual = PermissaoDePush.naoPerguntada,
    this.assinatura,
  });

  SuporteDePush suporteDoNavegador;
  PermissaoDePush permissaoAtual;

  /// A assinatura que o aparelho já tem (ou `null`).
  AssinaturaDoNavegador? assinatura;

  /// O que acontece quando a pessoa responde ao pedido de permissão.
  PermissaoDePush respostaDoPedido = PermissaoDePush.concedida;
  Object? falhaAoAssinar;

  /// Enquanto não for completado, `assinar` fica pendente (para provar o toque repetido).
  Completer<void>? portaoDeAssinar;

  final chamadas = <String>[];
  String? ultimaChave;

  @override
  SuporteDePush get suporte => suporteDoNavegador;

  @override
  Future<PermissaoDePush> permissao() async => permissaoAtual;

  @override
  Future<PermissaoDePush> pedirPermissao() async {
    chamadas.add('pedirPermissao');
    permissaoAtual = respostaDoPedido;
    return permissaoAtual;
  }

  @override
  Future<AssinaturaDoNavegador?> assinaturaAtual() async => assinatura;

  @override
  Future<AssinaturaDoNavegador> assinar(String chavePublica) async {
    chamadas.add('assinar');
    ultimaChave = chavePublica;
    await portaoDeAssinar?.future;
    if (falhaAoAssinar != null) throw falhaAoAssinar!;
    return assinatura = const AssinaturaDoNavegador(
      endpoint: 'https://fcm.googleapis.com/fcm/send/aparelho-1',
      p256dh: 'BP256',
      auth: 'AUTH',
    );
  }

  @override
  Future<void> cancelar() async {
    chamadas.add('cancelar');
    assinatura = null;
  }
}
