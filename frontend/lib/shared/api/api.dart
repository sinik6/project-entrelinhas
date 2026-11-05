// Contrato da API e modelos (spec 003). O app só conversa com a API por esta interface; os testes usam uma falsa.
import 'package:entrelinhas/shared/api/api_http.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class Membro {
  const Membro({required this.nome, required this.cor});

  factory Membro.fromJson(Map<String, dynamic> json) =>
      Membro(nome: json['nome'] as String, cor: json['cor'] as String);

  final String nome;
  final String cor;
}

class Grupo {
  const Grupo({
    required this.id,
    required this.tipo,
    required this.limiteMembros,
    required this.membros,
    required this.vaga,
  });

  factory Grupo.fromJson(Map<String, dynamic> json) => Grupo(
    id: json['id'] as String,
    tipo: json['tipo'] as String,
    limiteMembros: json['limite_membros'] as int,
    membros: [
      for (final m in json['membros'] as List<dynamic>)
        Membro.fromJson(m as Map<String, dynamic>),
    ],
    vaga: json['vaga'] as bool,
  );

  final String id;
  final String tipo;
  final int limiteMembros;
  final List<Membro> membros;
  final bool vaga;
}

class Perfil {
  const Perfil({
    required this.email,
    required this.completo,
    this.nome,
    this.cor,
    this.grupo,
  });

  factory Perfil.fromJson(Map<String, dynamic> json) => Perfil(
    email: json['email'] as String,
    nome: json['nome'] as String?,
    cor: json['cor'] as String?,
    completo: json['completo'] as bool,
    grupo: json['grupo'] == null
        ? null
        : Grupo.fromJson(json['grupo'] as Map<String, dynamic>),
  );

  final String email;
  final String? nome;
  final String? cor;
  final bool completo;
  final Grupo? grupo;
}

class ConviteGerado {
  const ConviteGerado({required this.codigo, required this.expiraEm});

  factory ConviteGerado.fromJson(Map<String, dynamic> json) => ConviteGerado(
    codigo: json['codigo'] as String,
    expiraEm: DateTime.parse(json['expira_em'] as String),
  );

  final String codigo;
  final DateTime expiraEm;
}

/// Erro devolvido pela API. `status` 0 = sem conexão.
class ErroApi implements Exception {
  const ErroApi(this.status, {this.detalhe, this.campos = const {}});

  final int status;
  final String? detalhe;
  final Map<String, List<String>> campos;
}

abstract class Api {
  Future<Perfil> entrar(String email, String senha);
  Future<void> sair();
  Future<Perfil> perfil();
  Future<Perfil> atualizarPerfil({String? nome, String? cor});
  Future<void> trocarSenha(String atual, String nova);
  Future<Grupo?> grupo();
  Future<Grupo> criarGrupo();
  Future<ConviteGerado> gerarConvite();
  Future<Perfil> aceitarConvite({
    required String codigo,
    required String nome,
    required String email,
    required String senha,
    required String cor,
  });
}

final apiProvider = Provider<Api>((ref) => ApiHttp());
