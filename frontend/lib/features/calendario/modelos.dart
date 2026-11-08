// Modelos do calendário (spec 009): o estado de cada dia, derivado dos registros pela API. Sem horários nem texto.
import 'package:entrelinhas/features/hoje/modelos.dart';

abstract final class EstadoDoDia {
  static const escreveu = 'escreveu';
  static const falhou = 'falhou';
  static const pendente = 'pendente';
  static const fora = 'fora';
}

class DiaDoCalendario {
  const DiaDoCalendario({
    required this.data,
    required this.estados,
    required this.juntos,
  });

  factory DiaDoCalendario.fromJson(Map<String, dynamic> json) =>
      DiaDoCalendario(
        data: DateTime.parse(json['data'] as String),
        estados: [
          for (final e in json['estados'] as List<dynamic>) e as String,
        ],
        juntos: json['juntos'] as bool,
      );

  final DateTime data;

  /// Alinhado a `Calendario.membros`.
  final List<String> estados;
  final bool juntos;

  String get chave =>
      '${data.year}-${data.month.toString().padLeft(2, '0')}-${data.day.toString().padLeft(2, '0')}';
}

class Calendario {
  const Calendario({
    required this.mes,
    required this.hoje,
    required this.membros,
    required this.dias,
  });

  factory Calendario.fromJson(Map<String, dynamic> json) => Calendario(
    mes: json['mes'] as String,
    hoje: DateTime.parse(json['hoje'] as String),
    membros: [
      for (final m in json['membros'] as List<dynamic>)
        Autor.fromJson(m as Map<String, dynamic>),
    ],
    dias: [
      for (final d in json['dias'] as List<dynamic>)
        DiaDoCalendario.fromJson(d as Map<String, dynamic>),
    ],
  );

  final String mes;
  final DateTime hoje;
  final List<Autor> membros;
  final List<DiaDoCalendario> dias;
}
