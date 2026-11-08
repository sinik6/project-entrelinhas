// Fora do navegador (testes na VM, por exemplo) não há Web Push: tudo responde "sem suporte".
import 'package:entrelinhas/shared/push/push_api.dart';

PushApi criarPushApi() => _SemPush();

class _SemPush implements PushApi {
  @override
  SuporteDePush get suporte => SuporteDePush.semSuporte;

  @override
  Future<PermissaoDePush> permissao() async => PermissaoDePush.negada;

  @override
  Future<PermissaoDePush> pedirPermissao() async => PermissaoDePush.negada;

  @override
  Future<AssinaturaDoNavegador?> assinaturaAtual() async => null;

  @override
  Future<AssinaturaDoNavegador> assinar(String chavePublica) =>
      throw UnsupportedError('Web Push indisponível aqui.');

  @override
  Future<void> cancelar() async {}
}
