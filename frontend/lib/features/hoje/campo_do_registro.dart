// Controlador do campo de texto do registro (spec 006, REQ-11.3): desenha o trecho escolhido com fundo destacado.
import 'package:flutter/material.dart';

class ControladorDoRegistro extends TextEditingController {
  ControladorDoRegistro({super.text});

  ({int inicio, int fim})? _marcado;

  /// Trecho marcado, em unidades UTF-16 do texto atual; `null` = nada marcado.
  ({int inicio, int fim})? get marcado => _marcado;

  set marcado(({int inicio, int fim})? valor) {
    if (valor == _marcado) return;
    _marcado = valor;
    notifyListeners();
  }

  @override
  TextSpan buildTextSpan({
    required BuildContext context,
    TextStyle? style,
    required bool withComposing,
  }) {
    final trecho = _marcado;
    if (trecho == null ||
        trecho.inicio < 0 ||
        trecho.fim > text.length ||
        trecho.inicio >= trecho.fim) {
      return super.buildTextSpan(
        context: context,
        style: style,
        withComposing: withComposing,
      );
    }
    final esquema = Theme.of(context).colorScheme;
    return TextSpan(
      style: style,
      children: [
        TextSpan(text: text.substring(0, trecho.inicio)),
        TextSpan(
          text: text.substring(trecho.inicio, trecho.fim),
          style: TextStyle(
            backgroundColor: esquema.primaryContainer,
            color: esquema.onPrimaryContainer,
          ),
        ),
        TextSpan(text: text.substring(trecho.fim)),
      ],
    );
  }
}
