// Rotas por fragmento (`#/convite/<código>`): o código do convite nunca vai ao servidor nem a logs (ADR-0006).
import 'package:entrelinhas/app/casca.dart';
import 'package:entrelinhas/features/acesso/carregando_page.dart';
import 'package:entrelinhas/features/acesso/convite_page.dart';
import 'package:entrelinhas/features/acesso/entrar_page.dart';
import 'package:entrelinhas/features/acesso/recuperacao.dart';
import 'package:entrelinhas/features/acesso/sessao.dart';
import 'package:entrelinhas/features/calendario/calendario_page.dart';
import 'package:entrelinhas/features/diario/diario_page.dart';
import 'package:entrelinhas/features/grupo/grupo_page.dart';
import 'package:entrelinhas/features/hoje/hoje_page.dart';
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
    // O link de recuperação (spec 011) também não precisa de sessão.
    final recuperacaoAberta =
        destino == '/recuperar' || destino.startsWith('/redefinir');
    if (sessao.isLoading || sessao.hasError) {
      // Os links de convite e de recuperação não precisam de sessão: não perdem o endereço enquanto ela carrega.
      return destino == '/carregando' || conviteAberto || recuperacaoAberta
          ? null
          : '/carregando';
    }
    final perfil = sessao.value;
    final publica = destino == '/entrar' || conviteAberto || recuperacaoAberta;
    if (perfil == null) return publica ? null : '/entrar';
    if (!perfil.completo) {
      return destino == '/perfil' ? null : '/perfil'; // REQ-5.5
    }
    final temGrupo = perfil.grupo != null;
    // Hoje e Diário só existem para quem tem grupo (REQ-11.1): sem grupo, o app leva ao Grupo.
    if (!temGrupo &&
        (destino == '/hoje' ||
            destino == '/diario' ||
            destino == '/calendario')) {
      return '/grupo';
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
        path: '/recuperar',
        builder: (context, estado) => const RecuperarPage(),
      ),
      GoRoute(
        path: '/redefinir/:uid/:token',
        builder: (context, estado) => ReceberLinkPage(
          uid: estado.pathParameters['uid']!,
          token: estado.pathParameters['token']!,
        ),
      ),
      GoRoute(
        path: '/redefinir',
        builder: (context, estado) => const RedefinirPage(),
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
            path: '/hoje',
            builder: (context, estado) => const HojePage(),
          ),
          GoRoute(
            path: '/diario',
            builder: (context, estado) => const DiarioPage(),
          ),
          GoRoute(
            path: '/calendario',
            builder: (context, estado) => const CalendarioPage(),
          ),
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
