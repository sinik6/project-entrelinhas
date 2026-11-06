import 'package:entrelinhas/features/acesso/sessao.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

const _destinos = ['/hoje', '/diario', '/grupo', '/perfil'];

/// Moldura das telas de quem já entrou: barra com "Sair" e navegação entre Hoje, Diário, Grupo e Perfil.
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
        selectedIndex: _destinos.indexOf(local).clamp(0, _destinos.length - 1),
        onDestinationSelected: (i) => context.go(_destinos[i]),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.edit_outlined),
            selectedIcon: Icon(Icons.edit),
            label: 'Hoje',
          ),
          NavigationDestination(
            icon: Icon(Icons.menu_book_outlined),
            selectedIcon: Icon(Icons.menu_book),
            label: 'Diário',
          ),
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
