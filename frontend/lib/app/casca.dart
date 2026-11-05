import 'package:entrelinhas/features/acesso/sessao.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

/// Moldura das telas de quem já entrou: barra com "Sair" e navegação entre Grupo e Perfil.
class Casca extends ConsumerWidget {
  const Casca({required this.filho, super.key});

  final Widget filho;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final local = GoRouterState.of(context).matchedLocation;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Entrelinhas'),
        actions: [
          TextButton(
            onPressed: () => ref.read(sessaoProvider.notifier).sair(),
            child: const Text('Sair'),
          ),
        ],
      ),
      body: SafeArea(child: filho),
      bottomNavigationBar: NavigationBar(
        selectedIndex: local == '/perfil' ? 1 : 0,
        onDestinationSelected: (i) => context.go(i == 0 ? '/grupo' : '/perfil'),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.group_outlined),
            selectedIcon: Icon(Icons.group),
            label: 'Grupo',
          ),
          NavigationDestination(
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person),
            label: 'Perfil',
          ),
        ],
      ),
    );
  }
}
