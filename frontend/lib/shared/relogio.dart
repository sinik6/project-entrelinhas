// Relógio do app (spec 006): o "hoje" e o "mês" da tela vêm daqui, para os testes poderem fixar o instante.
// Quem decide o dia de um registro é o servidor (fuso de São Paulo); o app só o usa para escolher o que mostrar.
import 'package:flutter_riverpod/flutter_riverpod.dart';

final relogioProvider = Provider<DateTime Function()>(
  (ref) =>
      () => DateTime.now().toUtc(),
);

/// Instante no horário de São Paulo (UTC−3; o Brasil não tem horário de verão desde 2019). Os campos do resultado
/// são os de relógio de lá, e só servem para formatar.
DateTime emSaoPaulo(DateTime instante) =>
    instante.toUtc().subtract(const Duration(hours: 3));

String _dois(int n) => n.toString().padLeft(2, '0');

String diaDe(DateTime instante) {
  final d = emSaoPaulo(instante);
  return '${d.year}-${_dois(d.month)}-${_dois(d.day)}';
}

String mesDe(int ano, int mes) => '$ano-${_dois(mes)}';

/// `05/11 às 20:15`, no horário de São Paulo.
String diaEHora(DateTime instante) {
  final d = emSaoPaulo(instante);
  return '${_dois(d.day)}/${_dois(d.month)} às ${_dois(d.hour)}:${_dois(d.minute)}';
}

const _meses = [
  'janeiro',
  'fevereiro',
  'março',
  'abril',
  'maio',
  'junho',
  'julho',
  'agosto',
  'setembro',
  'outubro',
  'novembro',
  'dezembro',
];

String nomeDoMes(int ano, int mes) => '${_meses[mes - 1]} de $ano';
