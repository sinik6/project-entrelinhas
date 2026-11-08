// Modelos dos destaques e comentários (spec 007), como a API os devolve. As posições são em pontos de código do
// TEXTO VISÍVEL do registro (ADR-0009), nunca do texto integral.
import 'package:entrelinhas/features/hoje/modelos.dart';

class Comentario {
  const Comentario({
    required this.id,
    required this.texto,
    required this.autor,
    required this.meu,
    required this.criadoEm,
    this.editadoEm,
  });

  factory Comentario.fromJson(Map<String, dynamic> json) => Comentario(
    id: json['id'] as String,
    texto: json['texto'] as String,
    autor: Autor.fromJson(json['autor'] as Map<String, dynamic>),
    meu: json['meu'] as bool,
    criadoEm: DateTime.parse(json['criado_em'] as String),
    editadoEm: json['editado_em'] == null
        ? null
        : DateTime.parse(json['editado_em'] as String),
  );

  final String id;
  final String texto;
  final Autor autor;
  final bool meu;
  final DateTime criadoEm;
  final DateTime? editadoEm;
}

class Destaque {
  const Destaque({
    required this.id,
    required this.inicio,
    required this.fim,
    required this.trecho,
    required this.autor,
    required this.meu,
    required this.criadoEm,
    required this.comentarios,
  });

  factory Destaque.fromJson(Map<String, dynamic> json) => Destaque(
    id: json['id'] as String,
    inicio: json['inicio'] as int,
    fim: json['fim'] as int,
    trecho: json['trecho'] as String,
    autor: Autor.fromJson(json['autor'] as Map<String, dynamic>),
    meu: json['meu'] as bool,
    criadoEm: DateTime.parse(json['criado_em'] as String),
    comentarios: [
      for (final c in json['comentarios'] as List<dynamic>)
        Comentario.fromJson(c as Map<String, dynamic>),
    ],
  );

  final String id;
  final int inicio;
  final int fim;

  /// O que a API diz ter sido destacado (o texto visível fatiado por ela).
  final String trecho;
  final Autor autor;
  final bool meu;
  final DateTime criadoEm;
  final List<Comentario> comentarios;

  Destaque copiar({List<Comentario>? comentarios}) => Destaque(
    id: id,
    inicio: inicio,
    fim: fim,
    trecho: trecho,
    autor: autor,
    meu: meu,
    criadoEm: criadoEm,
    comentarios: comentarios ?? this.comentarios,
  );
}
