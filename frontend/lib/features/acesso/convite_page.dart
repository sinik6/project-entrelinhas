import 'package:entrelinhas/features/acesso/sessao.dart';
import 'package:entrelinhas/shared/api/api.dart';
import 'package:entrelinhas/shared/api/erros.dart';
import 'package:entrelinhas/shared/ui/cores.dart';
import 'package:entrelinhas/shared/ui/pagina.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Criar a conta pelo link do convite. O código vem do fragmento da URL e só vai ao servidor no corpo do POST.
class ConvitePage extends ConsumerStatefulWidget {
  const ConvitePage({required this.codigo, super.key});

  final String codigo;

  @override
  ConsumerState<ConvitePage> createState() => _ConvitePageState();
}

class _ConvitePageState extends ConsumerState<ConvitePage> {
  final _nome = TextEditingController();
  final _email = TextEditingController();
  final _senha = TextEditingController();
  final _cor = TextEditingController();
  Object? _erro;
  bool _ocupado = false;

  @override
  void dispose() {
    for (final c in [_nome, _email, _senha, _cor]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _criar() async {
    setState(() {
      _ocupado = true;
      _erro = null;
    });
    try {
      await ref
          .read(sessaoProvider.notifier)
          .aceitarConvite(
            codigo: widget.codigo,
            nome: _nome.text.trim(),
            email: _email.text.trim(),
            senha: _senha.text,
            cor: _cor.text.trim(),
          );
    } on Object catch (erro) {
      if (mounted) setState(() => _erro = erro);
    } finally {
      if (mounted) setState(() => _ocupado = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final erro = _erro;
    final porCampo = erro is ErroApi && erro.status == 422;
    return Scaffold(
      body: SafeArea(
        child: Pagina(
          filhos: [
            const SizedBox(height: 24),
            titulo(context, 'Criar conta'),
            const SizedBox(height: 8),
            const Text(
              'Você foi convidado para um grupo de escrita. Crie sua conta para entrar nele.',
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _nome,
              decoration: InputDecoration(
                labelText: 'Nome',
                errorText: erroDoCampo(erro, 'nome'),
              ),
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _email,
              decoration: InputDecoration(
                labelText: 'E-mail',
                errorText: erroDoCampo(erro, 'email'),
              ),
              keyboardType: TextInputType.emailAddress,
              autofillHints: const [AutofillHints.email],
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _senha,
              decoration: InputDecoration(
                labelText: 'Senha',
                helperText: 'Use 12 ou mais caracteres.',
                errorText: erroDoCampo(erro, 'senha'),
              ),
              obscureText: true,
              autofillHints: const [AutofillHints.newPassword],
              textInputAction: TextInputAction.next,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _cor,
              decoration: InputDecoration(
                labelText: 'Cor (#RRGGBB)',
                helperText: 'Escolha uma sugestão ou digite a sua.',
                errorText: erroDoCampo(erro, 'cor'),
              ),
              autocorrect: false,
            ),
            PaletaDeCores(
              atual: _cor.text,
              aoEscolher: (hex) => setState(() => _cor.text = hex),
            ),
            if (erro != null && !porCampo)
              Mensagem(mensagemDoErro(erro), erro: true),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: _ocupado ? null : _criar,
              child: const Text('Criar conta e entrar'),
            ),
          ],
        ),
      ),
    );
  }
}
