// Mensagens para a pessoa (REQ-5.4): sempre em português e nunca com detalhe técnico.
import 'package:entrelinhas/shared/api/api.dart';

String mensagemDoErro(Object erro) {
  if (erro is! ErroApi) return 'Algo deu errado. Tente de novo.';
  switch (erro.status) {
    case 0:
      return 'Sem conexão com o servidor. Tente de novo.';
    case 401:
      return 'Sua sessão acabou. Entre de novo.';
    case 403:
      return 'Não foi possível confirmar a segurança do pedido. Recarregue a página e tente de novo.';
    case 413:
      return 'A foto é grande demais. Escolha uma menor.';
    case 429:
      return 'Muitas tentativas. Espere um minuto e tente de novo.';
    case 400 || 409:
      return erro.detalhe ?? 'Não foi possível concluir.';
    case 422:
      return erro.campos.values.expand((m) => m).firstOrNull ??
          'Confira os dados.';
  }
  return 'O servidor teve um problema. Tente de novo em instantes.';
}

/// Erros por campo vindos do servidor (422), ou `null` quando o campo está certo.
String? erroDoCampo(Object? erro, String campo) {
  if (erro is! ErroApi) return null;
  final mensagens = erro.campos[campo];
  return mensagens == null || mensagens.isEmpty ? null : mensagens.join(' ');
}
