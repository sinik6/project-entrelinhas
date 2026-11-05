// Rotas por fragmento (`#/convite/<código>`): o código do convite nunca vai ao servidor nem a logs (ADR-0006).
import 'package:entrelinhas/app/casca.dart';
import 'package:entrelinhas/features/acesso/carregando_page.dart';
import 'package:entrelinhas/features/acesso/convite_page.dart';
import 'package:entrelinhas/features/acesso/entrar_page.dart';
import 'package:entrelinhas/features/acesso/sessao.dart';
import 'package:entrelinhas/features/grupo/grupo_page.dart';
import 'package:entrelinhas/features/perfil/perfil_page.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

final roteadorProvider = Provider<GoRouter>((ref) {
  final mudou = ValueNotifier<int>(0);
  ref.listen(sessaoProvider, (_, _) => mudou.value++);

  String? decidir(String destino) {
    final sessao = ref.read(sessaoProvider);
    final conviteAberto = destino.startsWith('/convite/');
    if (sessao.isLoading || sessao.hasError) {
      // O link de convite não precisa de sessão: não perde o endereço enquanto ela carrega.
      return destino == '/carregando' || conviteAberto ? null : '/carregando';
    }
    final perfil = sessao.value;
    final publica = destino == '/entrar' || conviteAberto;
    if (perfil == null) return publica ? null : '/entrar';
    if (!perfil.completo) {
      return destino == '/perfil' ? null : '/perfil'; // REQ-5.5
    }
    return publica || destino == '/carregando' || destino == '/'
        ? '/grupo'
        : null;
  }

  final roteador = GoRouter(
    initialLocation: '/carregando',
    refreshListenable: mudou,
    redirect: (context, estado) => decidir(estado.matchedLocation),
    routes: [
      GoRoute(
        path: '/carregando',
        builder: (context, estado) => const CarregandoPage(),
      ),
      GoRoute(
        path: '/entrar',
        builder: (context, estado) => const EntrarPage(),
      ),
      GoRoute(
        path: '/convite/:codigo',
        builder: (context, estado) =>
            ConvitePage(codigo: estado.pathParameters['codigo']!),
      ),
      ShellRoute(
        builder: (context, estado, filho) => Casca(filho: filho),
        routes: [
          GoRoute(
            path: '/grupo',
            builder: (context, estado) => const GrupoPage(),
          ),
          GoRoute(
            path: '/perfil',
            builder: (context, estado) => const PerfilPage(),
          ),
        ],
      ),
    ],
  );
  ref.onDispose(() {
    roteador.dispose();
    mudou.dispose();
  });
  return roteador;
});
