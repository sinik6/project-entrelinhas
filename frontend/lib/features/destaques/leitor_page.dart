// Leitor de um registro com destaques (spec 008, US-15): seleciona o texto visível, destaca, comenta e abre a conversa.
// O texto é desenhado como texto (nunca HTML) e nada é guardado no aparelho.
import 'package:entrelinhas/features/acesso/sessao.dart';
import 'package:entrelinhas/features/destaques/folha_de_comentarios.dart';
import 'package:entrelinhas/features/destaques/modelos.dart';
import 'package:entrelinhas/features/destaques/pintura.dart';
import 'package:entrelinhas/features/hoje/modelos.dart';
import 'package:entrelinhas/shared/api/api.dart';
import 'package:entrelinhas/shared/api/erros.dart';
import 'package:entrelinhas/shared/relogio.dart';
import 'package:entrelinhas/shared/texto.dart';
import 'package:entrelinhas/shared/ui/cores.dart';
import 'package:entrelinhas/shared/ui/pagina.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Abre o leitor do registro por cima da tela atual.
Future<void> abrirLeitorDoRegistro(BuildContext context, Registro registro) =>
    Navigator.of(context, rootNavigator: true).push(
      MaterialPageRoute<void>(
        fullscreenDialog: true,
        builder: (_) => LeitorPage(registro: registro),
      ),
    );

/// Controlador só de leitura: pinta cada destaque com fundo translúcido na cor de quem o fez mais sublinhado.
class ControladorDeLeitura extends TextEditingController {
  ControladorDeLeitura({required TextoVisivel visivel})
    : _visivel = visivel,
      super(text: visivel.completo);

  final TextoVisivel _visivel;
  List<Destaque> _destaques = const [];

  List<Destaque> get destaques => _destaques;

  set destaques(List<Destaque> valor) {
    _destaques = valor;
    notifyListeners();
  }

  @override
  TextSpan buildTextSpan({
    required BuildContext context,
    TextStyle? style,
    required bool withComposing,
  }) {
    final base = _visivel.base;
    final fundo = Theme.of(context).colorScheme.surface;
    final completo = _visivel.completo;
    final visivel = _visivel.texto;
    final filhos = <InlineSpan>[
      if (base > 0) TextSpan(text: completo.substring(0, base)),
      for (final s in segmentar(visivel, _destaques))
        TextSpan(
          text: visivel.substring(s.inicio, s.fim),
          style: s.topo == null
              ? null
              : TextStyle(
                  backgroundColor: fundoDoDestaque(
                    corDeTexto(s.topo!.autor.cor),
                    fundo,
                  ),
                  decoration: TextDecoration.underline,
                  decorationColor: corDeTexto(s.topo!.autor.cor),
                  decorationThickness: 2,
                ),
        ),
      if (base + visivel.length < completo.length)
        TextSpan(text: completo.substring(base + visivel.length)),
    ];
    return TextSpan(style: style, children: filhos);
  }
}

class LeitorPage extends ConsumerStatefulWidget {
  const LeitorPage({required this.registro, super.key});

  final Registro registro;

  @override
  ConsumerState<LeitorPage> createState() => _LeitorPageState();
}

class _LeitorPageState extends ConsumerState<LeitorPage> {
  late final TextoVisivel _visivel = visivelDoRegistro(widget.registro)!;
  late final ControladorDeLeitura _controlador = ControladorDeLeitura(
    visivel: _visivel,
  );
  List<Destaque> _destaques = [];
  bool _carregando = true;
  String? _erroDeCarga;
  String? _erro;
  bool _ocupado = false;

  @override
  void initState() {
    super.initState();
    _controlador.addListener(() => setState(() {}));
    _carregar();
  }

  @override
  void dispose() {
    _controlador.dispose();
    super.dispose();
  }

  // ---------- carregar ----------

  Future<void> _carregar() async {
    setState(() {
      _carregando = true;
      _erroDeCarga = null;
    });
    try {
      final lista = await ref
          .read(apiProvider)
          .listarDestaques(widget.registro.id);
      if (!mounted) return;
      setState(() {
        _destaques = lista;
        _controlador.destaques = lista;
        _carregando = false;
      });
    } on Object catch (erro) {
      if (!mounted) return;
      if (erro is ErroApi && erro.status == 401) {
        ref.read(sessaoProvider.notifier).acabou(erro);
        return;
      }
      setState(() {
        _erroDeCarga = mensagemDoErro(erro);
        _carregando = false;
      });
    }
  }

  void _trocarLista(List<Destaque> nova) {
    setState(() {
      _destaques = nova;
      _controlador.destaques = nova;
    });
  }

  // ---------- seleção ----------

  /// A seleção cortada ao texto visível e ajustada a grafemas; `null` se não sobra nada. O segundo valor diz se a
  /// seleção existia mas ficou toda fora do texto visível.
  (TrechoSelecionado?, bool) _selecao() {
    final s = _controlador.selection;
    if (!s.isValid || s.isCollapsed) return (null, false);
    final inicio = (s.start < s.end ? s.start : s.end) - _visivel.base;
    final fim = (s.start < s.end ? s.end : s.start) - _visivel.base;
    final tamanho = _visivel.texto.length;
    final dentro = trechoDaSelecao(
      _visivel.texto,
      inicio.clamp(0, tamanho),
      fim.clamp(0, tamanho),
    );
    final fora = inicio >= tamanho || fim <= 0;
    return (dentro, dentro == null && fora);
  }

  // ---------- criar ----------

  Future<void> _destacar({String? comentario}) async {
    final (trecho, _) = _selecao();
    if (trecho == null || _ocupado) return;
    setState(() {
      _ocupado = true;
      _erro = null;
    });
    try {
      final novo = await ref
          .read(apiProvider)
          .criarDestaque(
            widget.registro.id,
            inicio: trecho.inicioPontos,
            fim: trecho.fimPontos,
            comentario: comentario,
          );
      if (!mounted) return;
      _trocarLista([..._destaques, novo]);
      _controlador.selection = const TextSelection.collapsed(offset: 0);
    } on Object catch (erro) {
      if (!mounted) return;
      if (erro is ErroApi && erro.status == 401) {
        ref.read(sessaoProvider.notifier).acabou(erro);
        return;
      }
      setState(() => _erro = mensagemDoErro(erro));
    } finally {
      if (mounted) setState(() => _ocupado = false);
    }
  }

  Future<void> _destacarEComentar() async {
    if (_selecao().$1 == null || _ocupado) return;
    final comentario = await showDialog<String>(
      context: context,
      builder: (_) => const _PedidoDeComentario(),
    );
    if (comentario == null || !mounted) return;
    await _destacar(comentario: comentario);
  }

  // ---------- abrir a conversa ----------

  void _abrir(List<Destaque> cobrindo) {
    if (cobrindo.isEmpty) return;
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => FolhaDeComentarios(
        destaque: cobrindo.first,
        cobrindo: cobrindo,
        aoMudar: (novo) => _trocarLista([
          for (final d in _destaques) d.id == novo.id ? novo : d,
        ]),
        aoApagar: (id) => _trocarLista([
          for (final d in _destaques)
            if (d.id != id) d,
        ]),
      ),
    );
  }

  /// O toque no texto: o cursor foi para um ponto; se há destaque ali, abre o mais curto.
  void _aoTocar() {
    final s = _controlador.selection;
    if (!s.isValid || !s.isCollapsed) return;
    final ponto = s.baseOffset - _visivel.base;
    if (ponto < 0 || ponto >= _visivel.texto.length) return;
    _abrir(destaquesEm(_visivel.texto, _destaques, ponto));
  }

  // ---------- tela ----------

  String _rotulo(Destaque d) {
    final n = d.comentarios.length;
    final comentarios = n == 1 ? '1 comentário' : '$n comentários';
    return 'Destaque de ${d.autor.nome}: $comentarios';
  }

  Widget _itemDaLista(Destaque d) {
    final tema = Theme.of(context);
    return Semantics(
      container: true,
      button: true,
      label: _rotulo(d),
      excludeSemantics: true,
      child: InkWell(
        key: Key('destaque-${d.id}'),
        onTap: () => _abrir([
          d,
          ...destaquesEm(
            _visivel.texto,
            _destaques,
            pontosParaUtf16(_visivel.texto, d.inicio),
          ).where((x) => x.id != d.id),
        ]),
        child: ConstrainedBox(
          constraints: const BoxConstraints(minHeight: 48),
          child: Row(
            children: [
              Container(
                width: 6,
                height: 32,
                decoration: BoxDecoration(
                  color: corDeTexto(d.autor.cor),
                  borderRadius: BorderRadius.circular(3),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      d.trecho,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    Text(
                      '${d.autor.nome} · ${d.comentarios.length} comentário(s)',
                      style: tema.textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final (trecho, foraDoVisivel) = _selecao();
    final r = widget.registro;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Destaques'),
        leading: IconButton(
          tooltip: 'Fechar',
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: SafeArea(
        child: Align(
          alignment: Alignment.topCenter,
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 600),
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    '${r.autor.nome} · ${diaEHora(r.entregueEm)}',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 12),
                  Container(
                    key: const Key('leitor-texto'),
                    child: TextField(
                      controller: _controlador,
                      readOnly: true,
                      minLines: 3,
                      maxLines: null,
                      onTap: _aoTocar,
                      decoration: const InputDecoration(
                        labelText: 'Texto do registro',
                        alignLabelWithHint: true,
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Mensagem(
                    trecho != null
                        ? null
                        : foraDoVisivel
                        ? 'Selecione um trecho dentro do texto visível.'
                        : 'Selecione um trecho do texto para destacar.',
                  ),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      FilledButton(
                        onPressed: trecho == null || _ocupado
                            ? null
                            : _destacar,
                        child: const Text('Destacar'),
                      ),
                      FilledButton.tonal(
                        onPressed: trecho == null || _ocupado
                            ? null
                            : _destacarEComentar,
                        child: const Text('Destacar e comentar'),
                      ),
                    ],
                  ),
                  Mensagem(_erro, erro: true),
                  const SizedBox(height: 24),
                  titulo(context, 'Destaques'),
                  const SizedBox(height: 8),
                  if (_carregando)
                    Center(
                      child: Semantics(
                        label: 'Carregando',
                        child: const CircularProgressIndicator(),
                      ),
                    )
                  else if (_erroDeCarga != null) ...[
                    Mensagem(_erroDeCarga, erro: true),
                    Align(
                      alignment: Alignment.centerLeft,
                      child: OutlinedButton(
                        onPressed: _carregar,
                        child: const Text('Tentar de novo'),
                      ),
                    ),
                  ] else if (_destaques.isEmpty)
                    const Mensagem('Ainda não há destaques neste registro.')
                  else
                    for (final d in _destaques) _itemDaLista(d),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Pede o comentário do destaque ("Destacar e comentar").
class _PedidoDeComentario extends StatefulWidget {
  const _PedidoDeComentario();

  @override
  State<_PedidoDeComentario> createState() => _PedidoDeComentarioState();
}

class _PedidoDeComentarioState extends State<_PedidoDeComentario> {
  final _campo = TextEditingController();
  bool _respondido = false;

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

  void _responder(String? valor) {
    if (_respondido) return;
    _respondido = true;
    Navigator.of(context).pop(valor);
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Comentar o destaque'),
      content: TextField(
        key: const Key('campo-comentario-novo'),
        controller: _campo,
        autofocus: true,
        minLines: 1,
        maxLines: 4,
        maxLength: 1000,
        decoration: const InputDecoration(labelText: 'Seu comentário'),
      ),
      actions: [
        TextButton(
          onPressed: () => _responder(null),
          child: const Text('Voltar'),
        ),
        FilledButton(
          onPressed: _campo.text.trim().isEmpty
              ? null
              : () => _responder(_campo.text),
          child: const Text('Salvar destaque'),
        ),
      ],
    );
  }
}
