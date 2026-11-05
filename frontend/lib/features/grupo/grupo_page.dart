import 'package:entrelinhas/features/acesso/sessao.dart';
import 'package:entrelinhas/features/grupo/link_do_convite.dart';
import 'package:entrelinhas/shared/api/api.dart';
import 'package:entrelinhas/shared/api/erros.dart';
import 'package:entrelinhas/shared/ui/avatar.dart';
import 'package:entrelinhas/shared/ui/pagina.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class GrupoPage extends ConsumerStatefulWidget {
  const GrupoPage({super.key});

  @override
  ConsumerState<GrupoPage> createState() => _GrupoPageState();
}

class _GrupoPageState extends ConsumerState<GrupoPage> {
  Grupo? _grupo;
  bool _carregando = true;
  ConviteGerado? _convite;
  String? _erro;
  String? _ok;
  bool _ocupado = false;

  @override
  void initState() {
    super.initState();
    _carregar();
  }

  Future<void> _carregar() async {
    try {
      final grupo = await ref.read(apiProvider).grupo();
      if (mounted) setState(() => _grupo = grupo);
    } on Object catch (erro) {
      _tratar(erro);
    } finally {
      if (mounted) setState(() => _carregando = false);
    }
  }

  void _tratar(Object erro) {
    if (!mounted) return;
    if (erro is ErroApi && erro.status == 401) {
      ref.read(sessaoProvider.notifier).acabou(erro);
    } else {
      setState(() => _erro = mensagemDoErro(erro));
    }
  }

  Future<void> _criarGrupo() async {
    setState(() {
      _ocupado = true;
      _erro = null;
    });
    try {
      final grupo = await ref.read(apiProvider).criarGrupo();
      if (mounted) setState(() => _grupo = grupo);
    } on Object catch (erro) {
      _tratar(erro);
    } finally {
      if (mounted) setState(() => _ocupado = false);
    }
  }

  Future<void> _convidar() async {
    setState(() {
      _ocupado = true;
      _erro = null;
      _ok = null;
    });
    try {
      final convite = await ref.read(apiProvider).gerarConvite();
      if (mounted) setState(() => _convite = convite);
    } on Object catch (erro) {
      _tratar(erro);
    } finally {
      if (mounted) setState(() => _ocupado = false);
    }
  }

  Future<void> _copiar(String link) async {
    await Clipboard.setData(ClipboardData(text: link));
    if (mounted) setState(() => _ok = 'Link copiado.');
  }

  String _validade(DateTime expiraEm) {
    final d = expiraEm.toLocal();
    String dois(int n) => n.toString().padLeft(2, '0');
    return 'Vale até ${dois(d.day)}/${dois(d.month)}/${d.year} às ${dois(d.hour)}:${dois(d.minute)}.';
  }

  @override
  Widget build(BuildContext context) {
    if (_carregando) {
      return Center(
        child: Semantics(
          label: 'Carregando',
          child: const CircularProgressIndicator(),
        ),
      );
    }
    final grupo = _grupo;
    final convite = _convite;
    final link = convite == null
        ? null
        : ref.watch(linkDoConviteProvider)(convite.codigo);
    return Pagina(
      filhos: [
        titulo(context, 'Seu grupo'),
        const SizedBox(height: 16),
        if (grupo == null) ...[
          const Text('Você ainda não tem um grupo.'),
          const SizedBox(height: 16),
          FilledButton(
            onPressed: _ocupado ? null : _criarGrupo,
            child: const Text('Criar grupo'),
          ),
        ] else ...[
          Text('Membros', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          for (final membro in grupo.membros)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Row(
                children: [
                  Avatar(
                    key: Key('cor-membro-${membro.nome}'),
                    nome: membro.nome,
                    cor: membro.cor,
                    fotoUrl: membro.fotoUrl,
                  ),
                  const SizedBox(width: 12),
                  Expanded(child: Text(membro.nome)),
                ],
              ),
            ),
          const SizedBox(height: 16),
          if (grupo.vaga) ...[
            FilledButton(
              onPressed: _ocupado ? null : _convidar,
              child: const Text('Convidar a outra pessoa'),
            ),
          ],
          if (link != null) ...[
            const SizedBox(height: 24),
            Text(
              'Link do convite',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            SelectableText(link),
            const SizedBox(height: 8),
            Text(_validade(convite!.expiraEm)),
            const SizedBox(height: 8),
            OutlinedButton(
              onPressed: () => _copiar(link),
              child: const Text('Copiar link'),
            ),
            const SizedBox(height: 8),
            const Text(
              'Mande o link só para a pessoa que vai escrever com você. Ele vale uma vez.',
            ),
          ],
        ],
        Mensagem(_erro, erro: true),
        Mensagem(_ok),
      ],
    );
  }
}
