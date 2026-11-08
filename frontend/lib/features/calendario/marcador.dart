// Marcador de estado do dia (spec 009, REQ-17.2 e 17.3): cada estado tem forma própria, para a cor não carregar a
// informação sozinha (WCAG 1.4.1).
import 'package:entrelinhas/features/calendario/modelos.dart';
import 'package:flutter/material.dart';

enum FormaDoMarcador {
  /// Sem marcador (a pessoa ainda não estava no grupo).
  nenhuma,

  /// Círculo preenchido: escreveu.
  cheio,

  /// Círculo vazado com "×": o dia passou sem registro.
  vazadoComX,

  /// Círculo tracejado: hoje, ainda dá tempo.
  tracejado,
}

class MarcadorDeEstado extends StatelessWidget {
  const MarcadorDeEstado({
    required this.estado,
    required this.cor,
    this.tamanho = 14,
    super.key,
  });

  final String estado;
  final Color cor;
  final double tamanho;

  static FormaDoMarcador formaDe(String estado) => switch (estado) {
    EstadoDoDia.escreveu => FormaDoMarcador.cheio,
    EstadoDoDia.falhou => FormaDoMarcador.vazadoComX,
    EstadoDoDia.pendente => FormaDoMarcador.tracejado,
    _ => FormaDoMarcador.nenhuma,
  };

  @override
  Widget build(BuildContext context) {
    final forma = formaDe(estado);
    return ExcludeSemantics(
      child: SizedBox(
        width: tamanho,
        height: tamanho,
        child: CustomPaint(painter: _Pintor(forma, cor)),
      ),
    );
  }
}

class _Pintor extends CustomPainter {
  _Pintor(this.forma, this.cor);

  final FormaDoMarcador forma;
  final Color cor;

  @override
  void paint(Canvas canvas, Size size) {
    final centro = size.center(Offset.zero);
    final raio = size.shortestSide / 2 - 1;
    final traco = Paint()
      ..color = cor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.6;
    switch (forma) {
      case FormaDoMarcador.nenhuma:
        return;
      case FormaDoMarcador.cheio:
        canvas.drawCircle(centro, raio, Paint()..color = cor);
      case FormaDoMarcador.vazadoComX:
        canvas.drawCircle(centro, raio, traco);
        final d = raio * 0.5;
        canvas
          ..drawLine(centro + Offset(-d, -d), centro + Offset(d, d), traco)
          ..drawLine(centro + Offset(-d, d), centro + Offset(d, -d), traco);
      case FormaDoMarcador.tracejado:
        const pedacos = 8;
        for (var i = 0; i < pedacos; i++) {
          final inicio = i * 2 * 3.141592653589793 / pedacos;
          canvas.drawArc(
            Rect.fromCircle(center: centro, radius: raio),
            inicio,
            2 * 3.141592653589793 / pedacos * 0.55,
            false,
            traco,
          );
        }
    }
  }

  @override
  bool shouldRepaint(_Pintor antigo) =>
      antigo.forma != forma || antigo.cor != cor;
}
