import 'package:entrelinhas/features/acesso/sessao.dart';
import 'package:entrelinhas/shared/api/erros.dart';
import 'package:entrelinhas/shared/ui/pagina.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class EntrarPage extends ConsumerStatefulWidget {
  const EntrarPage({super.key});

  @override
  ConsumerState<EntrarPage> createState() => _EntrarPageState();
}

class _EntrarPageState extends ConsumerState<EntrarPage> {
  final _email = TextEditingController();
  final _senha = TextEditingController();
  String? _erro;
  bool _ocupado = false;

  @override
  void dispose() {
    _email.dispose();
    _senha.dispose();
    super.dispose();
  }

  Future<void> _entrar() async {
    setState(() {
      _ocupado = true;
      _erro = null;
    });
    try {
      await ref
          .read(sessaoProvider.notifier)
          .entrar(_email.text.trim(), _senha.text);
    } on Object catch (erro) {
      if (mounted) setState(() => _erro = mensagemDoErro(erro));
    } finally {
      if (mounted) setState(() => _ocupado = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final aviso = ref.watch(avisoDaSessaoProvider);
    return Scaffold(
      body: SafeArea(
        child: Pagina(
          filhos: [
            const SizedBox(height: 24),
            titulo(context, 'Entrar'),
            const SizedBox(height: 16),
            Mensagem(aviso),
            TextFormField(
              controller: _email,
              decoration: const InputDecoration(labelText: 'E-mail'),
              keyboardType: TextInputType.emailAddress,
              autofillHints: const [AutofillHints.email],
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _senha,
              decoration: const InputDecoration(labelText: 'Senha'),
              obscureText: true,
              autofillHints: const [AutofillHints.password],
              onFieldSubmitted: (_) => _ocupado ? null : _entrar(),
            ),
            Mensagem(_erro, erro: true),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: _ocupado ? null : _entrar,
              child: const Text('Entrar'),
            ),
            const SizedBox(height: 24),
            const Text(
              'Recebeu um convite? Abra o link que a outra pessoa mandou.',
            ),
          ],
        ),
      ),
    );
  }
}
