// Folha de comentários de um destaque (spec 008, REQ-15.4 a 15.8): a conversa, comentar, editar, apagar.
// O texto de comentário é desenhado como `Text`, nunca como HTML (ABU-17).
import 'package:entrelinhas/features/acesso/sessao.dart';
import 'package:entrelinhas/features/destaques/modelos.dart';
import 'package:entrelinhas/shared/api/api.dart';
import 'package:entrelinhas/shared/api/erros.dart';
import 'package:entrelinhas/shared/relogio.dart';
import 'package:entrelinhas/shared/ui/avatar.dart';
import 'package:entrelinhas/shared/ui/pagina.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class FolhaDeComentarios extends ConsumerStatefulWidget {
  const FolhaDeComentarios({
    required this.destaque,
    required this.cobrindo,
    required this.aoMudar,
    required this.aoApagar,
    super.key,
  });

  final Destaque destaque;

  /// Todos os destaques que cobrem o ponto tocado (o aberto e os outros), do mais curto para o mais longo.
  final List<Destaque> cobrindo;
  final void Function(Destaque) aoMudar;
  final void Function(String id) aoApagar;

  @override
  ConsumerState<FolhaDeComentarios> createState() => _FolhaState();
}

class _FolhaState extends ConsumerState<FolhaDeComentarios> {
  late Destaque _atual = widget.destaque;
  final _campo = TextEditingController();
  String? _editando; // id do comentário em edição
  String? _erro;
  bool _ocupado = false;

  @override
  void initState() {
    super.initState();
    _campo.addListener(() => setState(() {}));
  }

  @override
  void dispose() {
    _campo.dispose();
    super.dispose();
  }

  bool get _podeEnviar => !_ocupado && _campo.text.trim().isNotEmpty;

  /// Tudo o que muda estado passa por aqui: um pedido por vez (ABU-18) e erros em português.
  Future<void> _executar(Future<void> Function() acao) async {
    if (_ocupado) return;
    setState(() {
      _ocupado = true;
      _erro = null;
    });
    try {
      await acao();
    } on Object catch (erro) {
      if (!mounted) return;
      if (erro is ErroApi && erro.status == 401) {
        ref.read(sessaoProvider.notifier).acabou(erro);
        Navigator.of(context).pop();
        return;
      }
      setState(() => _erro = mensagemDoErro(erro));
    } finally {
      if (mounted) setState(() => _ocupado = false);
    }
  }

  void _atualizar(Destaque novo) {
    setState(() => _atual = novo);
    widget.aoMudar(novo);
  }

  Future<void> _enviar() => _executar(() async {
    final api = ref.read(apiProvider);
    final texto = _campo.text;
    final editando = _editando;
    if (editando == null) {
      final novo = await api.comentar(_atual.id, texto);
      _atualizar(_atual.copiar(comentarios: [..._atual.comentarios, novo]));
    } else {
      final novo = await api.editarComentario(editando, texto);
      _atualizar(
        _atual.copiar(
          comentarios: [
            for (final c in _atual.comentarios) c.id == editando ? novo : c,
          ],
        ),
      );
    }
    if (!mounted) return;
    setState(() => _editando = null);
    _campo.clear();
  });

  void _comecarEdicao(Comentario c) {
    setState(() => _editando = c.id);
    _campo.text = c.texto;
  }

  void _cancelarEdicao() {
    setState(() => _editando = null);
    _campo.clear();
  }

  Future<void> _apagarComentario(Comentario c) => _executar(() async {
    await ref.read(apiProvider).apagarComentario(c.id);
    _atualizar(
      _atual.copiar(
        comentarios: [
          for (final x in _atual.comentarios)
            if (x.id != c.id) x,
        ],
      ),
    );
  });

  Future<void> _apagarDestaque() async {
    if (_ocupado) return;
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Apagar destaque?'),
        content: const Text(
          'Os comentários deste destaque também serão apagados.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Voltar'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Apagar'),
          ),
        ],
      ),
    );
    if (ok != true || !mounted) return;
    await _executar(() async {
      await ref.read(apiProvider).apagarDestaque(_atual.id);
      widget.aoApagar(_atual.id);
      if (mounted) Navigator.of(context).pop();
    });
  }

  Widget _comentario(Comentario c) {
    final tema = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Avatar(nome: c.autor.nome, cor: c.autor.cor, tamanho: 32),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(c.autor.nome, style: tema.textTheme.titleSmall),
                Text(diaEHora(c.criadoEm), style: tema.textTheme.bodySmall),
                if (c.editadoEm != null)
                  Text('editado', style: tema.textTheme.bodySmall),
                const SizedBox(height: 4),
                Text(c.texto),
              ],
            ),
          ),
          if (c.meu) ...[
            IconButton(
              tooltip: 'Editar comentário',
              icon: const Icon(Icons.edit_outlined),
              onPressed: _ocupado ? null : () => _comecarEdicao(c),
            ),
            IconButton(
              tooltip: 'Apagar comentário',
              icon: const Icon(Icons.delete_outline),
              onPressed: _ocupado ? null : () => _apagarComentario(c),
            ),
          ],
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final tema = Theme.of(context);
    final outros = [
      for (final d in widget.cobrindo)
        if (d.id != _atual.id) d,
    ];
    return SafeArea(
      child: Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom,
        ),
        child: SingleChildScrollView(
          key: const Key('folha-de-comentarios'),
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              titulo(context, 'Destaque de ${_atual.autor.nome}'),
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  border: Border.all(color: tema.colorScheme.outline),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(_atual.trecho),
              ),
              if (outros.isNotEmpty) ...[
                const SizedBox(height: 12),
                Text('Outros destaques aqui', style: tema.textTheme.labelLarge),
                Wrap(
                  spacing: 8,
                  children: [
                    for (final d in outros)
                      ActionChip(
                        key: Key('outro-destaque-${d.id}'),
                        label: Text(
                          '${d.autor.nome}: ${d.trecho}',
                          overflow: TextOverflow.ellipsis,
                        ),
                        onPressed: () => setState(() {
                          _atual = d;
                          _editando = null;
                          _campo.clear();
                          _erro = null;
                        }),
                      ),
                  ],
                ),
              ],
              const SizedBox(height: 12),
              if (_atual.comentarios.isEmpty)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 8),
                  child: Text('Ainda não há comentários.'),
                )
              else
                for (final c in _atual.comentarios) _comentario(c),
              const SizedBox(height: 8),
              TextFormField(
                key: const Key('campo-comentario'),
                controller: _campo,
                enabled: !_ocupado,
                minLines: 1,
                maxLines: 4,
                maxLength: 1000,
                textCapitalization: TextCapitalization.sentences,
                decoration: InputDecoration(
                  labelText: _editando == null
                      ? 'Seu comentário'
                      : 'Editar comentário',
                ),
              ),
              Mensagem(_erro, erro: true),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  FilledButton(
                    onPressed: _podeEnviar ? _enviar : null,
                    child: Text(_editando == null ? 'Comentar' : 'Salvar'),
                  ),
                  if (_editando != null)
                    OutlinedButton(
                      onPressed: _ocupado ? null : _cancelarEdicao,
                      child: const Text('Cancelar'),
                    ),
                  if (_atual.meu)
                    OutlinedButton(
                      onPressed: _ocupado ? null : _apagarDestaque,
                      child: const Text('Apagar destaque'),
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
