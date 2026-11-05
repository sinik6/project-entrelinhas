import 'package:flutter/material.dart';

/// Tema claro e escuro a partir de uma só cor-semente (NFR-A11Y-1: contraste conferido nos testes).
ThemeData tema(Brightness brilho) {
  final esquema = ColorScheme.fromSeed(
    seedColor: const Color(0xFF0E7490),
    brightness: brilho,
  );
  return ThemeData(
    useMaterial3: true,
    colorScheme: esquema,
    inputDecorationTheme: const InputDecorationTheme(
      border: OutlineInputBorder(),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(minimumSize: const Size(48, 48)),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(minimumSize: const Size(48, 48)),
    ),
    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(minimumSize: const Size(48, 48)),
    ),
  );
}
