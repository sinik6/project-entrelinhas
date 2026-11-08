// Recuperação de senha por e-mail (spec 011, US-22): pedir o link, abrir o link e escolher a senha nova.
// O token do link vive só na memória e sai da barra de endereço assim que a tela de senha nova abre (REQ-22.6).
import 'package:entrelinhas/features/acesso/sessao.dart';
import 'package:entrelinhas/shared/api/api.dart';
import 'package:entrelinhas/shared/api/erros.dart';
import 'package:entrelinhas/shared/ui/pagina.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

const mensagemDoPedido =
    'Se este e-mail tiver conta, enviamos um link. Vale por 1 hora.';
const mensagemDoLinkInvalido = 'Link inválido ou vencido.';
const mensagemDeSenhaTrocada = 'Senha trocada. Entre com a nova senha.';

/// O que o link do e-mail trouxe. Só em memória: nunca vai para o armazenamento do navegador.
class LinkDeRedefinicao {
  const LinkDeRedefinicao({required this.uid, required this.token});

  final String uid;
  final String token;
}

class LinkDeRedefinicaoNotifier extends Notifier<LinkDeRedefinicao?> {
  @override
  LinkDeRedefinicao? build() => null;

  void definir(LinkDeRedefinicao link) => state = link;

  void limpar() => state = null;
}

final linkDeRedefinicaoProvider =
    NotifierProvider<LinkDeRedefinicaoNotifier, LinkDeRedefinicao?>(
      LinkDeRedefinicaoNotifier.new,
    );

// ---------- pedir o link ----------

class RecuperarPage extends ConsumerStatefulWidget {
  const RecuperarPage({super.key});

  @override
  ConsumerState<RecuperarPage> createState() => _RecuperarPageState();
}

class _RecuperarPageState extends ConsumerState<RecuperarPage> {
  final _email = TextEditingController();
  String? _erro;
  String? _confirmacao;
  bool _ocupado = false;

  @override
  void dispose() {
    _email.dispose();
    super.dispose();
  }

  Future<void> _enviar() async {
    if (_ocupado) return;
    final email = _email.text.trim();
    if (email.isEmpty) {
      setState(() {
        _erro = 'Informe o seu e-mail.';
        _confirmacao = null;
      });
      return;
    }
    setState(() {
      _ocupado = true;
      _erro = null;
      _confirmacao = null;
    });
    try {
      await ref.read(apiProvider).pedirRecuperacao(email);
      // Sempre a mesma frase: o app nunca diz se o e-mail tem conta (ABU-24).
      if (mounted) setState(() => _confirmacao = mensagemDoPedido);
    } on Object catch (erro) {
      if (mounted) setState(() => _erro = mensagemDoErro(erro));
    } finally {
      if (mounted) setState(() => _ocupado = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Pagina(
          filhos: [
            const SizedBox(height: 24),
            titulo(context, 'Recuperar senha'),
            const SizedBox(height: 16),
            const Text(
              'Informe o e-mail da sua conta. Se ele tiver conta, você recebe um link para escolher uma senha nova.',
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _email,
              decoration: const InputDecoration(labelText: 'E-mail'),
              keyboardType: TextInputType.emailAddress,
              autofillHints: const [AutofillHints.email],
              onFieldSubmitted: (_) => _enviar(),
            ),
            Mensagem(_erro, erro: true),
            Mensagem(_confirmacao),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: _ocupado ? null : _enviar,
              child: const Text('Enviar link'),
            ),
            const SizedBox(height: 16),
            TextButton(
              onPressed: () => context.go('/entrar'),
              child: const Text('Voltar para entrar'),
            ),
          ],
        ),
      ),
    );
  }
}

// ---------- abrir o link ----------

/// Rota do link do e-mail (`#/redefinir/<uid>/<token>`): guarda o que veio na memória e troca a rota por uma sem o token.
class ReceberLinkPage extends ConsumerStatefulWidget {
  const ReceberLinkPage({required this.uid, required this.token, super.key});

  final String uid;
  final String token;

  @override
  ConsumerState<ReceberLinkPage> createState() => _ReceberLinkPageState();
}

class _ReceberLinkPageState extends ConsumerState<ReceberLinkPage> {
  @override
  void initState() {
    super.initState();
    // Providers não podem mudar durante a construção da árvore: espera o primeiro quadro.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      ref
          .read(linkDeRedefinicaoProvider.notifier)
          .definir(LinkDeRedefinicao(uid: widget.uid, token: widget.token));
      context.go('/redefinir');
    });
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    body: Center(
      child: Semantics(
        label: 'Carregando',
        child: const CircularProgressIndicator(),
      ),
    ),
  );
}

// ---------- senha nova ----------

class RedefinirPage extends ConsumerStatefulWidget {
  const RedefinirPage({super.key});

  @override
  ConsumerState<RedefinirPage> createState() => _RedefinirPageState();
}

class _RedefinirPageState extends ConsumerState<RedefinirPage> {
  final _nova = TextEditingController();
  final _confirmar = TextEditingController();
  Object? _erro;
  String? _aviso;
  bool _ocupado = false;
  bool _mostrar = false;
  bool _linkRuim = false;

  @override
  void dispose() {
    _nova.dispose();
    _confirmar.dispose();
    super.dispose();
  }

  Future<void> _trocar() async {
    if (_ocupado) return;
    final link = ref.read(linkDeRedefinicaoProvider);
    if (link == null) {
      setState(() => _linkRuim = true);
      return;
    }
    if (_nova.text.isEmpty) {
      setState(() {
        _erro = null;
        _aviso = 'Informe a senha nova.';
      });
      return;
    }
    if (_nova.text != _confirmar.text) {
      setState(() {
        _erro = null;
        _aviso = 'As senhas não são iguais.';
      });
      return;
    }
    setState(() {
      _ocupado = true;
      _erro = null;
      _aviso = null;
    });
    try {
      await ref
          .read(apiProvider)
          .redefinirSenha(
            uid: link.uid,
            token: link.token,
            novaSenha: _nova.text,
          );
      if (!mounted) return;
      ref.read(linkDeRedefinicaoProvider.notifier).limpar();
      // Não entra sozinho: volta à tela de entrar, com o aviso.
      ref.read(avisoDaSessaoProvider.notifier).definir(mensagemDeSenhaTrocada);
      context.go('/entrar');
    } on Object catch (erro) {
      if (!mounted) return;
      if (erro is ErroApi && erro.status == 400) {
        // Vencido, já usado ou inválido: a mesma tela, sem detalhe.
        ref.read(linkDeRedefinicaoProvider.notifier).limpar();
        setState(() => _linkRuim = true);
        return;
      }
      setState(() => _erro = erro);
    } finally {
      if (mounted) setState(() => _ocupado = false);
    }
  }

  Widget _campoDeSenha(
    TextEditingController controlador,
    String rotulo, {
    String? erro,
  }) {
    return TextFormField(
      controller: controlador,
      obscureText: !_mostrar,
      enabled: !_ocupado,
      autofillHints: const [AutofillHints.newPassword],
      decoration: InputDecoration(
        labelText: rotulo,
        errorText: erro,
        suffixIcon: IconButton(
          tooltip: _mostrar ? 'Ocultar a senha' : 'Mostrar a senha',
          icon: Icon(_mostrar ? Icons.visibility_off : Icons.visibility),
          onPressed: () => setState(() => _mostrar = !_mostrar),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final semLink = ref.watch(linkDeRedefinicaoProvider) == null;
    if (_linkRuim || semLink) {
      return Scaffold(
        body: SafeArea(
          child: Pagina(
            filhos: [
              const SizedBox(height: 24),
              titulo(context, 'Senha nova'),
              const SizedBox(height: 16),
              const Mensagem(mensagemDoLinkInvalido, erro: true),
              const SizedBox(height: 16),
              FilledButton(
                onPressed: () {
                  ref.read(linkDeRedefinicaoProvider.notifier).limpar();
                  context.go('/recuperar');
                },
                child: const Text('Pedir outro link'),
              ),
            ],
          ),
        ),
      );
    }
    final erro = _erro;
    return Scaffold(
      body: SafeArea(
        child: Pagina(
          filhos: [
            const SizedBox(height: 24),
            titulo(context, 'Escolher a senha nova'),
            const SizedBox(height: 16),
            const Text('Use 12 ou mais caracteres. Evite senhas comuns.'),
            const SizedBox(height: 16),
            _campoDeSenha(
              _nova,
              'Nova senha',
              erro: erroDoCampo(erro, 'nova_senha'),
            ),
            const SizedBox(height: 16),
            _campoDeSenha(_confirmar, 'Confirmar nova senha'),
            Mensagem(_aviso, erro: true),
            if (erro is ErroApi &&
                (erro.status != 422 || !erro.campos.containsKey('nova_senha')))
              Mensagem(mensagemDoErro(erro), erro: true),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: _ocupado ? null : _trocar,
              child: const Text('Trocar senha'),
            ),
          ],
        ),
      ),
    );
  }
}
