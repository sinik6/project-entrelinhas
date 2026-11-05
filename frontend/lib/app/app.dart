import 'package:entrelinhas/app/rotas.dart';
import 'package:entrelinhas/app/tema.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class EntrelinhasApp extends ConsumerWidget {
  const EntrelinhasApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp.router(
      title: 'Entrelinhas',
      debugShowCheckedModeBanner: false,
      theme: tema(Brightness.light),
      darkTheme: tema(Brightness.dark),
      themeMode: ThemeMode.system,
      routerConfig: ref.watch(roteadorProvider),
    );
  }
}
