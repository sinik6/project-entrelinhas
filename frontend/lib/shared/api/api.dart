// Contrato da API e modelos (specs 003 e 004). O app só conversa com a API por esta interface; os testes usam uma falsa.
import 'dart:typed_data';

import 'package:entrelinhas/shared/api/api_http.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class Membro {
  const Membro({required this.nome, required this.cor, this.fotoUrl});

  factory Membro.fromJson(Map<String, dynamic> json) => Membro(
    nome: json['nome'] as String,
    cor: json['cor'] as String,
    fotoUrl: json['foto_url'] as String?,
  );

  final String nome;
  final String cor;

  /// Endereço da foto, relativo à base da API (spec 004); `null` = sem foto.
  final String? fotoUrl;
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
    this.fotoUrl,
  });

  factory Perfil.fromJson(Map<String, dynamic> json) => Perfil(
    email: json['email'] as String,
    nome: json['nome'] as String?,
    cor: json['cor'] as String?,
    completo: json['completo'] as bool,
    fotoUrl: json['foto_url'] as String?,
    grupo: json['grupo'] == null
        ? null
        : Grupo.fromJson(json['grupo'] as Map<String, dynamic>),
  );

  final String email;
  final String? nome;
  final String? cor;
  final bool completo;
  final Grupo? grupo;

  /// Foto de perfil (spec 004), relativa à base da API.
  final String? fotoUrl;
}

/// Foto recém-enviada (ainda avulsa): o app a usa em seguida, por exemplo como foto de perfil.
class FotoEnviada {
  const FotoEnviada({
    required this.id,
    required this.finalidade,
    required this.largura,
    required this.altura,
  });

  factory FotoEnviada.fromJson(Map<String, dynamic> json) => FotoEnviada(
    id: json['id'] as String,
    finalidade: json['finalidade'] as String,
    largura: json['largura'] as int,
    altura: json['altura'] as int,
  );

  final String id;
  final String finalidade;
  final int largura;
  final int altura;
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
  Future<FotoEnviada> enviarFoto({
    required Uint8List bytes,
    required String nome,
    required String tipo,
    required String finalidade,
  });
  Future<Perfil> definirFotoDePerfil(String fotoId);
  Future<void> removerFotoDePerfil();
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
