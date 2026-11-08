// Web Push de verdade, pelas APIs do navegador (`serviceWorker`, `PushManager`, `Notification`), via `dart:js_interop`.
// Sem pacote novo (ADR-0012): o SDK já traz a ponte. O service worker é o `web/sw.js` (só push; não guarda dado).
import 'dart:js_interop';
import 'dart:js_interop_unsafe';
import 'dart:typed_data';

import 'package:entrelinhas/shared/push/push_api.dart';

PushApi criarPushApi() => _PushDoNavegador();

JSObject get _navegador => globalContext['navigator']! as JSObject;

bool _tem(JSObject objeto, String nome) => objeto.has(nome);

/// base64url -> bytes (a chave pública VAPID chega assim do servidor).
Uint8List _bytes(String base64url) {
  final padrao = base64url.replaceAll('-', '+').replaceAll('_', '/');
  final completo = padrao.padRight((padrao.length + 3) ~/ 4 * 4, '=');
  final saida = <int>[];
  const alfabeto =
      'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';
  var acumulado = 0;
  var bits = 0;
  for (final c in completo.split('')) {
    if (c == '=') break;
    acumulado = (acumulado << 6) | alfabeto.indexOf(c);
    bits += 6;
    if (bits >= 8) {
      bits -= 8;
      saida.add((acumulado >> bits) & 0xFF);
    }
  }
  return Uint8List.fromList(saida);
}

String _base64url(JSAny? bruto) {
  // `toJSON()` já entrega as chaves em base64url, sem preenchimento.
  return (bruto as JSString?)?.toDart ?? '';
}

class _PushDoNavegador implements PushApi {
  bool get _iosForaDaTelaInicial {
    final agente = ((_navegador['userAgent'] as JSString?)?.toDart ?? '')
        .toLowerCase();
    final ios =
        agente.contains('iphone') ||
        agente.contains('ipad') ||
        agente.contains('ipod');
    if (!ios) return false;
    final instalado = _navegador['standalone'];
    if (instalado.isA<JSBoolean>() && (instalado as JSBoolean).toDart) {
      return false;
    }
    final consulta = globalContext.callMethod<JSObject>(
      'matchMedia'.toJS,
      '(display-mode: standalone)'.toJS,
    );
    return !((consulta['matches'] as JSBoolean?)?.toDart ?? false);
  }

  @override
  SuporteDePush get suporte {
    final completo =
        _tem(_navegador, 'serviceWorker') &&
        _tem(globalContext, 'PushManager') &&
        _tem(globalContext, 'Notification');
    if (completo) return SuporteDePush.disponivel;
    return _iosForaDaTelaInicial
        ? SuporteDePush.precisaInstalar
        : SuporteDePush.semSuporte;
  }

  PermissaoDePush _traduzir(String? valor) => switch (valor) {
    'granted' => PermissaoDePush.concedida,
    'denied' => PermissaoDePush.negada,
    _ => PermissaoDePush.naoPerguntada,
  };

  JSObject get _notificacao => globalContext['Notification']! as JSObject;

  @override
  Future<PermissaoDePush> permissao() async =>
      _traduzir((_notificacao['permission'] as JSString?)?.toDart);

  @override
  Future<PermissaoDePush> pedirPermissao() async {
    final resposta = await _notificacao
        .callMethod<JSPromise<JSString>>('requestPermission'.toJS)
        .toDart;
    return _traduzir(resposta.toDart);
  }

  JSObject get _servico => _navegador['serviceWorker']! as JSObject;

  Future<JSObject?> _registro() async {
    final r = await _servico
        .callMethod<JSPromise<JSObject?>>('getRegistration'.toJS)
        .toDart;
    return r;
  }

  AssinaturaDoNavegador? _ler(JSObject? assinatura) {
    if (assinatura == null) return null;
    final json = assinatura.callMethod<JSObject>('toJSON'.toJS);
    final chaves = json['keys'] as JSObject?;
    final endpoint = (json['endpoint'] as JSString?)?.toDart;
    if (chaves == null || endpoint == null) return null;
    return AssinaturaDoNavegador(
      endpoint: endpoint,
      p256dh: _base64url(chaves['p256dh']),
      auth: _base64url(chaves['auth']),
    );
  }

  @override
  Future<AssinaturaDoNavegador?> assinaturaAtual() async {
    final registro = await _registro();
    if (registro == null) return null;
    final gerente = registro['pushManager']! as JSObject;
    final atual = await gerente
        .callMethod<JSPromise<JSObject?>>('getSubscription'.toJS)
        .toDart;
    return _ler(atual);
  }

  @override
  Future<AssinaturaDoNavegador> assinar(String chavePublica) async {
    // `sw.js` relativo ao endereço base do app (vira /entrelinhas/sw.js na VPS).
    await _servico
        .callMethod<JSPromise<JSObject>>('register'.toJS, 'sw.js'.toJS)
        .toDart;
    final pronto = await (_servico['ready']! as JSPromise<JSObject>).toDart;
    final opcoes = JSObject()
      ..['userVisibleOnly'] = true.toJS
      ..['applicationServerKey'] = _bytes(chavePublica).toJS;
    final gerente = pronto['pushManager']! as JSObject;
    final assinatura = await gerente
        .callMethod<JSPromise<JSObject>>('subscribe'.toJS, opcoes)
        .toDart;
    final lida = _ler(assinatura);
    if (lida == null) throw StateError('Assinatura sem chaves.');
    return lida;
  }

  @override
  Future<void> cancelar() async {
    final registro = await _registro();
    if (registro == null) return;
    final gerente = registro['pushManager']! as JSObject;
    final atual = await gerente
        .callMethod<JSPromise<JSObject?>>('getSubscription'.toJS)
        .toDart;
    if (atual != null) {
      await atual.callMethod<JSPromise<JSBoolean>>('unsubscribe'.toJS).toDart;
    }
  }
}
