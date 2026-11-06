// Modelos do registro diário (specs 005 e 006): a visão do autor e a do parceiro, como a API as devolve.
// O app só mostra o que a API entrega; não existe aqui nenhum campo que a visão do parceiro não tenha.

/// Trecho escolhido, em pontos de código Unicode, `[inicio, fim)` (ADR-0009).
class Trecho {
  const Trecho({required this.inicio, required this.fim});

  factory Trecho.fromJson(Map<String, dynamic> json) =>
      Trecho(inicio: json['inicio'] as int, fim: json['fim'] as int);

  final int inicio;
  final int fim;

  Map<String, int> toJson() => {'inicio': inicio, 'fim': fim};

  @override
  bool operator ==(Object other) =>
      other is Trecho && other.inicio == inicio && other.fim == fim;

  @override
  int get hashCode => Object.hash(inicio, fim);
}

class Autor {
  const Autor({required this.nome, required this.cor, this.fotoUrl});

  factory Autor.fromJson(Map<String, dynamic> json) => Autor(
    nome: json['nome'] as String,
    cor: json['cor'] as String,
    fotoUrl: json['foto_url'] as String?,
  );

  final String nome;
  final String cor;
  final String? fotoUrl;
}

abstract final class Visibilidade {
  static const todos = 'full';
  static const privado = 'private';
  static const trecho = 'partial';
}

class Registro {
  const Registro({
    required this.id,
    required this.data,
    required this.entregueEm,
    required this.visibilidade,
    required this.texto,
    required this.fotos,
    required this.autor,
    required this.meu,
    this.trecho,
    this.aviso,
  });

  /// Visão do autor (`meu: true`) ou do parceiro (`meu: false`), conforme a API devolveu.
  factory Registro.fromJson(Map<String, dynamic> json) {
    final meu = json['meu'] as bool;
    final trecho = json['trecho'];
    return Registro(
      id: json['id'] as String,
      data: json['data'] as String,
      entregueEm: DateTime.parse(json['entregue_em'] as String),
      visibilidade:
          (meu ? json['visibilidade'] : json['visibilidade_efetiva']) as String,
      texto: (meu ? json['texto'] : json['texto_visivel']) as String?,
      fotos: [for (final f in json['fotos'] as List<dynamic>) f as String],
      autor: Autor.fromJson(json['autor'] as Map<String, dynamic>),
      meu: meu,
      trecho: trecho is Map<String, dynamic> ? Trecho.fromJson(trecho) : null,
      aviso: json['aviso'] as String?,
    );
  }

  final String id;

  /// Dia do registro (`AAAA-MM-DD`, fuso de São Paulo), como o servidor o calculou.
  final String data;
  final DateTime entregueEm;
  final String visibilidade;

  /// Do autor: o texto inteiro. Do parceiro: só o que ele pode ler (`null` = nada).
  final String? texto;
  final List<String> fotos;
  final Autor autor;
  final bool meu;

  /// Só na visão do autor.
  final Trecho? trecho;

  /// Só na visão do parceiro, quando o registro é privado.
  final String? aviso;
}
