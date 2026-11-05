import 'package:entrelinhas/features/acesso/sessao.dart';
import 'package:entrelinhas/shared/api/api.dart';
import 'package:entrelinhas/shared/api/erros.dart';
import 'package:entrelinhas/shared/ui/cores.dart';
import 'package:entrelinhas/shared/ui/pagina.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class PerfilPage extends ConsumerStatefulWidget {
  const PerfilPage({super.key});

  @override
  ConsumerState<PerfilPage> createState() => _PerfilPageState();
}

class _PerfilPageState extends ConsumerState<PerfilPage> {
  late final TextEditingController _nome;
  late final TextEditingController _cor;
  final _senhaAtual = TextEditingController();
  final _senhaNova = TextEditingController();
  Object? _erroDoPerfil;
  Object? _erroDaSenha;
  String? _okDoPerfil;
  String? _okDaSenha;
  bool _ocupado = false;

  @override
  void initState() {
    super.initState();
    final perfil = ref.read(sessaoProvider).value;
    _nome = TextEditingController(text: perfil?.nome ?? '');
    _cor = TextEditingController(text: perfil?.cor ?? '');
  }

  @override
  void dispose() {
    for (final c in [_nome, _cor, _senhaAtual, _senhaNova]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _executar(
    Future<void> Function() acao, {
    required void Function(Object) aoFalhar,
  }) async {
    setState(() => _ocupado = true);
    try {
      await acao();
    } on ErroApi catch (erro) {
      if (!mounted) return;
      if (erro.status == 401) {
        ref.read(sessaoProvider.notifier).acabou(erro);
      } else {
        setState(() => aoFalhar(erro));
      }
    } on Object catch (erro) {
      if (mounted) setState(() => aoFalhar(erro));
    } finally {
      if (mounted) setState(() => _ocupado = false);
    }
  }

  Future<void> _salvar() => _executar(() async {
    final eraIncompleto = !(ref.read(sessaoProvider).value?.completo ?? false);
    setState(() {
      _erroDoPerfil = null;
      _okDoPerfil = null;
    });
    final novo = await ref
        .read(apiProvider)
        .atualizarPerfil(nome: _nome.text.trim(), cor: _cor.text.trim());
    ref.read(sessaoProvider.notifier).atualizar(novo);
    if (!mounted) return;
    if (eraIncompleto) {
      context.go('/grupo');
    } else {
      setState(() => _okDoPerfil = 'Perfil salvo.');
    }
  }, aoFalhar: (erro) => _erroDoPerfil = erro);

  Future<void> _trocarSenha() => _executar(() async {
    setState(() {
      _erroDaSenha = null;
      _okDaSenha = null;
    });
    await ref.read(apiProvider).trocarSenha(_senhaAtual.text, _senhaNova.text);
    _senhaAtual.clear();
    _senhaNova.clear();
    if (mounted) setState(() => _okDaSenha = 'Senha trocada.');
  }, aoFalhar: (erro) => _erroDaSenha = erro);

  @override
  Widget build(BuildContext context) {
    final perfil = ref.watch(sessaoProvider).value;
    final incompleto = perfil != null && !perfil.completo;
    final erroPerfil = _erroDoPerfil;
    final erroSenha = _erroDaSenha;
    return Pagina(
      filhos: [
        titulo(context, 'Seu perfil'),
        if (incompleto)
          const Mensagem('Informe seu nome e escolha uma cor para continuar.'),
        const SizedBox(height: 8),
        Text(
          perfil?.email ?? '',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        const SizedBox(height: 16),
        TextFormField(
          controller: _nome,
          decoration: InputDecoration(
            labelText: 'Nome',
            errorText: erroDoCampo(erroPerfil, 'nome'),
          ),
        ),
        const SizedBox(height: 16),
        TextFormField(
          controller: _cor,
          decoration: InputDecoration(
            labelText: 'Cor (#RRGGBB)',
            helperText: 'Escolha uma sugestão ou digite a sua.',
            errorText: erroDoCampo(erroPerfil, 'cor'),
          ),
          autocorrect: false,
        ),
        PaletaDeCores(
          atual: _cor.text,
          aoEscolher: (hex) => setState(() => _cor.text = hex),
        ),
        if (erroPerfil is ErroApi && erroPerfil.status != 422)
          Mensagem(mensagemDoErro(erroPerfil), erro: true),
        if (erroPerfil is ErroApi &&
            erroPerfil.status == 422 &&
            erroPerfil.campos.keys.any((c) => c != 'nome' && c != 'cor'))
          Mensagem(mensagemDoErro(erroPerfil), erro: true),
        Mensagem(_okDoPerfil),
        const SizedBox(height: 8),
        FilledButton(
          onPressed: _ocupado ? null : _salvar,
          child: const Text('Salvar'),
        ),
        const SizedBox(height: 32),
        titulo(context, 'Trocar senha'),
        const SizedBox(height: 16),
        TextFormField(
          controller: _senhaAtual,
          decoration: InputDecoration(
            labelText: 'Senha atual',
            errorText: erroDoCampo(erroSenha, 'senha_atual'),
          ),
          obscureText: true,
          autofillHints: const [AutofillHints.password],
        ),
        const SizedBox(height: 16),
        TextFormField(
          controller: _senhaNova,
          decoration: InputDecoration(
            labelText: 'Nova senha',
            helperText: 'Use 12 ou mais caracteres.',
            errorText: erroDoCampo(erroSenha, 'senha_nova'),
          ),
          obscureText: true,
          autofillHints: const [AutofillHints.newPassword],
        ),
        if (erroSenha is ErroApi && erroSenha.status != 422)
          Mensagem(mensagemDoErro(erroSenha), erro: true),
        Mensagem(_okDaSenha),
        const SizedBox(height: 8),
        FilledButton(
          onPressed: _ocupado ? null : _trocarSenha,
          child: const Text('Trocar senha'),
        ),
      ],
    );
  }
}
