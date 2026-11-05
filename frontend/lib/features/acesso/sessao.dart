// Estado da sessão: quem está logado (ou ninguém) e o aviso de "sua sessão acabou".
import 'package:entrelinhas/shared/api/api.dart';
import 'package:entrelinhas/shared/api/erros.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class Sessao extends AsyncNotifier<Perfil?> {
  @override
  Future<Perfil?> build() async {
    try {
      return await ref.read(apiProvider).perfil();
    } on ErroApi catch (erro) {
      if (erro.status == 401) return null;
      rethrow;
    }
  }

  Future<void> entrar(String email, String senha) async {
    final perfil = await ref.read(apiProvider).entrar(email, senha);
    ref.read(avisoDaSessaoProvider.notifier).limpar();
    state = AsyncData(perfil);
  }

  Future<void> aceitarConvite({
    required String codigo,
    required String nome,
    required String email,
    required String senha,
    required String cor,
  }) async {
    final perfil = await ref
        .read(apiProvider)
        .aceitarConvite(
          codigo: codigo,
          nome: nome,
          email: email,
          senha: senha,
          cor: cor,
        );
    ref.read(avisoDaSessaoProvider.notifier).limpar();
    state = AsyncData(perfil);
  }

  Future<void> sair() async {
    await ref.read(apiProvider).sair();
    state = const AsyncData(null);
  }

  void atualizar(Perfil perfil) => state = AsyncData(perfil);

  /// O servidor respondeu 401 no meio do uso: volta para a tela de entrar, dizendo por quê.
  void acabou(Object erro) {
    ref.read(avisoDaSessaoProvider.notifier).definir(mensagemDoErro(erro));
    state = const AsyncData(null);
  }
}

final sessaoProvider = AsyncNotifierProvider<Sessao, Perfil?>(Sessao.new);

class AvisoDaSessao extends Notifier<String?> {
  @override
  String? build() => null;

  void definir(String mensagem) => state = mensagem;

  void limpar() => state = null;
}

final avisoDaSessaoProvider = NotifierProvider<AvisoDaSessao, String?>(
  AvisoDaSessao.new,
);
