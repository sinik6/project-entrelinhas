import 'package:entrelinhas/features/acesso/sessao.dart';
import 'package:entrelinhas/shared/api/erros.dart';
import 'package:entrelinhas/shared/ui/pagina.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Enquanto o app descobre se há sessão. Se o servidor não responder, oferece tentar de novo.
class CarregandoPage extends ConsumerWidget {
  const CarregandoPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final sessao = ref.watch(sessaoProvider);
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: sessao.hasError
              ? Pagina(
                  filhos: [
                    Mensagem(mensagemDoErro(sessao.error!), erro: true),
                    FilledButton(
                      onPressed: () => ref.invalidate(sessaoProvider),
                      child: const Text('Tentar de novo'),
                    ),
                  ],
                )
              : Semantics(
                  label: 'Carregando',
                  child: const CircularProgressIndicator(),
                ),
        ),
      ),
    );
  }
}
