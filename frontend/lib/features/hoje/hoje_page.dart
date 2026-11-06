// Hoje (spec 006, US-11): escrever o dia, fotografar, escolher quem lê e entregar. Depois de entregue, mostra o registro do dia.
//
// O rascunho vive só na memória do app (REQ-11.9): nenhum armazenamento do navegador ou do aparelho é usado.
import 'package:entrelinhas/features/acesso/sessao.dart';
import 'package:entrelinhas/features/diario/cartao_de_registro.dart';
import 'package:entrelinhas/features/hoje/campo_do_registro.dart';
import 'package:entrelinhas/features/hoje/modelos.dart';
import 'package:entrelinhas/features/hoje/rascunho.dart';
import 'package:entrelinhas/shared/api/api.dart';
import 'package:entrelinhas/shared/api/erros.dart';
import 'package:entrelinhas/shared/foto/seletor_de_foto.dart';
import 'package:entrelinhas/shared/relogio.dart';
import 'package:entrelinhas/shared/texto.dart';
import 'package:entrelinhas/shared/ui/pagina.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Mesmos limites do servidor (specs 004 e 005); o app só antecipa a mensagem, quem decide é a API.
const _limiteDaFoto = 8 * 1024 * 1024;
const _fotosMaximo = 3;
const _textoMinimo = 10;

const _instrucaoDoTrecho =
    'Selecione no texto o trecho que a outra pessoa poderá ler.';

String _rotuloDaVisibilidade(String visibilidade) => switch (visibilidade) {
  Visibilidade.todos => 'Todo o grupo lê',
  Visibilidade.privado => 'Só eu',
  _ => 'Só um trecho',
};

class HojePage extends ConsumerStatefulWidget {
  const HojePage({super.key});

  @override
  ConsumerState<HojePage> createState() => _HojePageState();
}

class _HojePageState extends ConsumerState<HojePage> {
  late final ControladorDoRegistro _texto;

  bool _carregando = true;
  String? _erroDeCarga;
  Registro? _meuHoje;
  Registro? _doParceiroHoje;

  bool _enviando = false;
  String? _progresso;
  String? _entregue;
  String? _erroDeEnvio;
  bool _podeTentarDeNovo = false;
  Object? _erroDosCampos;
  String? _erroDaFoto;

  bool _selecaoVazia = false;
  String? _avisoDoTrecho;
  bool _dialogoAberto = false;

  @override
  void initState() {
    super.initState();
    final rascunho = ref.read(rascunhoProvider);
    _texto = ControladorDoRegistro(text: rascunho.texto);
    final trecho = rascunho.trecho;
    if (trecho != null) {
      _texto.marcado = (inicio: trecho.inicioUtf16, fim: trecho.fimUtf16);
    }
    _carregar();
  }

  @override
  void dispose() {
    _texto.dispose();
    super.dispose();
  }

  // ---------- carregar o dia ----------

  Future<void> _carregar() async {
    setState(() {
      _carregando = true;
      _erroDeCarga = null;
    });
    try {
      final agora = ref.read(relogioProvider)();
      final hoje = diaDe(agora);
      final d = emSaoPaulo(agora);
      final lista = await ref
          .read(apiProvider)
          .listarRegistros(mesDe(d.year, d.month));
      if (!mounted) return;
      setState(() {
        _meuHoje = lista.where((r) => r.meu && r.data == hoje).firstOrNull;
        _doParceiroHoje = lista
            .where((r) => !r.meu && r.data == hoje)
            .firstOrNull;
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

  // ---------- fotos ----------

  Future<void> _escolherFoto() async {
    setState(() => _erroDaFoto = null);
    try {
      final foto = await ref.read(seletorDeFotoProvider).escolher();
      if (foto == null || !mounted) return;
      if (foto.bytes.length > _limiteDaFoto) {
        setState(
          () => _erroDaFoto = 'A foto passa de 8 MB. Escolha uma menor.',
        );
        return;
      }
      ref.read(rascunhoProvider.notifier).adicionarFoto(foto);
    } on Object {
      if (mounted) {
        setState(
          () => _erroDaFoto = 'Não foi possível abrir as fotos. Tente de novo.',
        );
      }
    }
  }

  // ---------- texto e trecho ----------

  void _aoMudarTexto(String texto) {
    final notificador = ref.read(rascunhoProvider.notifier);
    final tinhaTrecho = ref.read(rascunhoProvider).trecho != null;
    notificador.texto(texto);
    if (tinhaTrecho) {
      // O trecho valia para o texto de antes: não pode sobreviver a uma edição.
      notificador.trecho(null);
      _texto.marcado = null;
      setState(
        () => _avisoDoTrecho = 'O texto mudou. Escolha o trecho de novo.',
      );
    }
  }

  void _usarSelecao() {
    final selecao = _texto.selection;
    final trecho = selecao.isValid
        ? trechoDaSelecao(_texto.text, selecao.baseOffset, selecao.extentOffset)
        : null;
    final notificador = ref.read(rascunhoProvider.notifier);
    if (trecho == null) {
      notificador.trecho(null);
      _texto.marcado = null;
      setState(() {
        _selecaoVazia = true;
        _avisoDoTrecho = null;
      });
      return;
    }
    notificador.trecho(
      TrechoDoRascunho(
        inicioUtf16: trecho.inicioUtf16,
        fimUtf16: trecho.fimUtf16,
        inicioPontos: trecho.inicioPontos,
        fimPontos: trecho.fimPontos,
      ),
    );
    _texto.marcado = (inicio: trecho.inicioUtf16, fim: trecho.fimUtf16);
    setState(() {
      _selecaoVazia = false;
      _avisoDoTrecho = null;
    });
  }

  void _escolherVisibilidade(String? valor) {
    if (valor == null) return;
    ref.read(rascunhoProvider.notifier).visibilidade(valor);
    _texto.marcado = null;
    setState(() {
      _selecaoVazia = false;
      _avisoDoTrecho = null;
    });
  }

  // ---------- entrega ----------

  List<String> _faltas(Rascunho r) => [
    if (caracteresUteis(r.texto) < _textoMinimo)
      'texto com pelo menos $_textoMinimo caracteres',
    if (r.fotos.isEmpty) 'uma foto',
    if (r.visibilidade == null)
      'escolher quem lê'
    else if (r.visibilidade == Visibilidade.trecho && r.trecho == null)
      'escolher o trecho',
  ];

  String _previaDoTrecho(Rascunho r) {
    final t = r.trecho!;
    return r.texto.substring(t.inicioUtf16, t.fimUtf16);
  }

  Future<void> _confirmar() async {
    if (_dialogoAberto || _enviando) return;
    final r = ref.read(rascunhoProvider);
    if (_faltas(r).isNotEmpty) return;
    _dialogoAberto = true;
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => _ConfirmacaoDeEntrega(
        quemLe: _rotuloDaVisibilidade(r.visibilidade!),
        trecho: r.visibilidade == Visibilidade.trecho
            ? _previaDoTrecho(r)
            : null,
        fotos: r.fotos.length,
      ),
    );
    _dialogoAberto = false;
    if (ok == true && mounted) await _entregar();
  }

  Future<void> _entregar() async {
    if (_enviando) return;
    setState(() {
      _enviando = true;
      _erroDeEnvio = null;
      _podeTentarDeNovo = false;
      _erroDosCampos = null;
      _entregue = null;
      _progresso = 'Enviando…';
    });
    // Depois do primeiro `await` a tela pode ter sido fechada: só o que não depende dela é usado.
    final api = ref.read(apiProvider);
    final notificador = ref.read(rascunhoProvider.notifier);
    try {
      final total = notificador.atual.fotos.length;
      for (var i = 0; i < total; i++) {
        final foto = notificador.atual.fotos[i];
        if (foto.idEnviado != null) {
          continue; // já subiu numa tentativa anterior
        }
        if (mounted) {
          setState(() => _progresso = 'Enviando fotos ${i + 1} de $total…');
        }
        final enviada = await api.enviarFoto(
          bytes: foto.foto.bytes,
          nome: foto.foto.nome,
          tipo: foto.foto.tipo,
          finalidade: 'manuscrito',
        );
        notificador.fotoEnviada(i, enviada.id);
      }
      final r = notificador.atual;
      final trecho = r.visibilidade == Visibilidade.trecho ? r.trecho : null;
      if (r.visibilidade == Visibilidade.trecho) {
        // Última conferência antes de enviar: o que a API vai fatiar é exatamente o que a pessoa viu na prévia.
        if (trecho == null ||
            fatiaPorPontos(r.texto, trecho.inicioPontos, trecho.fimPontos) !=
                _previaDoTrecho(r)) {
          throw const _TrechoInconsistente();
        }
      }
      if (mounted) setState(() => _progresso = 'Enviando o registro…');
      final registro = await api.entregarRegistro(
        texto: r.texto,
        visibilidade: r.visibilidade!,
        fotos: [for (final f in r.fotos) f.idEnviado!],
        trecho: trecho == null
            ? null
            : Trecho(inicio: trecho.inicioPontos, fim: trecho.fimPontos),
      );
      notificador.limpar();
      if (!mounted) return;
      _texto.marcado = null;
      _texto.clear();
      setState(() {
        _meuHoje = registro;
        _entregue = 'Registro entregue';
      });
    } on Object catch (erro) {
      if (!mounted) return;
      _tratarFalha(erro);
    } finally {
      if (mounted) {
        setState(() {
          _enviando = false;
          _progresso = null;
        });
      }
    }
  }

  void _tratarFalha(Object erro) {
    if (erro is _TrechoInconsistente) {
      setState(
        () => _erroDeEnvio =
            'Não foi possível confirmar o trecho. Escolha de novo.',
      );
      return;
    }
    if (erro is ErroApi) {
      if (erro.status == 401) {
        ref.read(sessaoProvider.notifier).acabou(erro);
        return;
      }
      if (erro.status == 409) {
        // O dia já foi entregue (talvez em outro aparelho): mostra o registro de hoje.
        setState(() => _erroDeEnvio = mensagemDoErro(erro));
        _carregar();
        return;
      }
      if (erro.status == 422) {
        final outros = erro.campos.keys.any((c) => c != 'texto');
        setState(() {
          _erroDosCampos = erro;
          if (outros || erro.campos.isEmpty) {
            _erroDeEnvio = mensagemDoErro(erro);
          }
        });
        return;
      }
    }
    setState(() {
      _erroDeEnvio = mensagemDoErro(erro);
      _podeTentarDeNovo = true;
    });
  }

  // ---------- telas ----------

  String _nomeDoParceiro() {
    final perfil = ref.read(sessaoProvider).value;
    final outros = perfil?.grupo?.membros
        .where((m) => m.nome != perfil.nome)
        .toList();
    if (outros != null && outros.length == 1) return outros.first.nome;
    return _doParceiroHoje?.autor.nome ?? 'A outra pessoa';
  }

  Widget _estadoDoParceiro() {
    final parceiro = _doParceiroHoje;
    final nome = _nomeDoParceiro();
    final texto = parceiro == null
        ? '$nome ainda não entregou hoje.'
        : parceiro.visibilidade == Visibilidade.privado
        ? '$nome entregou, mas manteve o registro privado.'
        : '$nome já entregou o registro de hoje.';
    return Mensagem(texto);
  }

  Widget _miniatura(int indice, FotoDoRascunho foto) {
    return SizedBox(
      key: Key('foto-escolhida-$indice'),
      width: 96,
      height: 96,
      child: Stack(
        children: [
          Positioned.fill(
            child: Semantics(
              image: true,
              label: 'Foto ${indice + 1} escolhida',
              excludeSemantics: true,
              child: ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: Image.memory(
                  foto.foto.bytes,
                  fit: BoxFit.cover,
                  errorBuilder: (_, _, _) =>
                      const Center(child: Icon(Icons.image_outlined)),
                ),
              ),
            ),
          ),
          Positioned(
            top: 0,
            right: 0,
            child: IconButton.filledTonal(
              tooltip: 'Tirar a foto ${indice + 1}',
              icon: const Icon(Icons.close),
              onPressed: _enviando
                  ? null
                  : () => ref.read(rascunhoProvider.notifier).tirarFoto(indice),
            ),
          ),
        ],
      ),
    );
  }

  Widget _secaoDoTrecho(Rascunho r) {
    final tema = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Mensagem(_instrucaoDoTrecho, erro: _selecaoVazia),
        Align(
          alignment: Alignment.centerLeft,
          child: FilledButton.tonal(
            onPressed: _enviando ? null : _usarSelecao,
            child: const Text('Usar a seleção'),
          ),
        ),
        if (r.trecho != null) ...[
          const SizedBox(height: 12),
          Text(
            'A outra pessoa lerá exatamente isto:',
            style: tema.textTheme.labelLarge,
          ),
          const SizedBox(height: 4),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              border: Border.all(color: tema.colorScheme.outline),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(_previaDoTrecho(r), key: const Key('previa-trecho')),
          ),
        ],
      ],
    );
  }

  Widget _formulario(Rascunho r) {
    final faltas = _faltas(r);
    final tema = Theme.of(context);
    return Pagina(
      filhos: [
        titulo(context, 'Hoje'),
        const SizedBox(height: 8),
        _estadoDoParceiro(),
        const SizedBox(height: 8),
        TextFormField(
          key: const Key('campo-texto'),
          controller: _texto,
          enabled: !_enviando,
          minLines: 6,
          maxLines: null,
          keyboardType: TextInputType.multiline,
          textCapitalization: TextCapitalization.sentences,
          inputFormatters: const [FormatadorDeQuebras()],
          onChanged: _aoMudarTexto,
          decoration: InputDecoration(
            labelText: 'Seu registro de hoje',
            helperText: 'Escreva pelo menos $_textoMinimo caracteres.',
            errorText: erroDoCampo(_erroDosCampos, 'texto'),
            alignLabelWithHint: true,
          ),
        ),
        Mensagem(_avisoDoTrecho),
        const SizedBox(height: 16),
        Text(
          'Fotos do manuscrito (de 1 a $_fotosMaximo)',
          style: tema.textTheme.titleMedium,
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            for (var i = 0; i < r.fotos.length; i++) _miniatura(i, r.fotos[i]),
          ],
        ),
        if (r.fotos.length < _fotosMaximo) ...[
          const SizedBox(height: 8),
          Align(
            alignment: Alignment.centerLeft,
            child: FilledButton.tonal(
              onPressed: _enviando ? null : _escolherFoto,
              child: const Text('Adicionar foto'),
            ),
          ),
        ],
        Mensagem(_erroDaFoto, erro: true),
        const SizedBox(height: 16),
        Text('Quem pode ler?', style: tema.textTheme.titleMedium),
        RadioGroup<String>(
          groupValue: r.visibilidade,
          onChanged: _enviando ? (_) {} : _escolherVisibilidade,
          child: Column(
            children: [
              for (final v in const [
                Visibilidade.todos,
                Visibilidade.privado,
                Visibilidade.trecho,
              ])
                RadioListTile<String>(
                  value: v,
                  contentPadding: EdgeInsets.zero,
                  title: Text(_rotuloDaVisibilidade(v)),
                ),
            ],
          ),
        ),
        if (r.visibilidade == Visibilidade.trecho) _secaoDoTrecho(r),
        const SizedBox(height: 16),
        if (_enviando)
          Semantics(
            liveRegion: true,
            child: Row(
              children: [
                const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
                const SizedBox(width: 12),
                Expanded(child: Text(_progresso ?? 'Enviando…')),
              ],
            ),
          )
        else ...[
          if (faltas.isNotEmpty)
            Padding(
              key: const Key('falta-para-entregar'),
              padding: const EdgeInsets.only(bottom: 8),
              child: Text('Falta: ${faltas.join(', ')}.'),
            ),
          FilledButton(
            key: const Key('botao-entregar'),
            onPressed: faltas.isEmpty ? _confirmar : null,
            child: const Text('Entregar'),
          ),
        ],
        Mensagem(_erroDeEnvio, erro: true),
        if (_podeTentarDeNovo && !_enviando)
          Align(
            alignment: Alignment.centerLeft,
            child: OutlinedButton(
              onPressed: _entregar,
              child: const Text('Tentar de novo'),
            ),
          ),
      ],
    );
  }

  Widget _registroDoDia(Registro registro) {
    return Pagina(
      filhos: [
        titulo(context, 'Hoje'),
        const SizedBox(height: 8),
        Mensagem(_entregue),
        Mensagem(_erroDeEnvio, erro: true),
        Container(
          key: const Key('registro-do-dia'),
          child: CartaoDeRegistro(registro: registro),
        ),
        const SizedBox(height: 8),
        _estadoDoParceiro(),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final rascunho = ref.watch(rascunhoProvider);
    if (_carregando) {
      return Center(
        child: Semantics(
          label: 'Carregando',
          child: const CircularProgressIndicator(),
        ),
      );
    }
    final erro = _erroDeCarga;
    if (erro != null) {
      return Pagina(
        filhos: [
          titulo(context, 'Hoje'),
          const SizedBox(height: 8),
          Mensagem(erro, erro: true),
          Align(
            alignment: Alignment.centerLeft,
            child: OutlinedButton(
              onPressed: _carregar,
              child: const Text('Tentar de novo'),
            ),
          ),
        ],
      );
    }
    final meu = _meuHoje;
    return meu == null ? _formulario(rascunho) : _registroDoDia(meu);
  }
}

class _TrechoInconsistente implements Exception {
  const _TrechoInconsistente();
}

class _ConfirmacaoDeEntrega extends StatefulWidget {
  const _ConfirmacaoDeEntrega({
    required this.quemLe,
    required this.fotos,
    this.trecho,
  });

  final String quemLe;
  final String? trecho;
  final int fotos;

  @override
  State<_ConfirmacaoDeEntrega> createState() => _ConfirmacaoDeEntregaState();
}

class _ConfirmacaoDeEntregaState extends State<_ConfirmacaoDeEntrega> {
  bool _respondido = false;

  void _responder(bool valor) {
    if (_respondido) {
      return; // toque repetido não fecha duas vezes nem entrega duas vezes
    }
    _respondido = true;
    Navigator.of(context).pop(valor);
  }

  @override
  Widget build(BuildContext context) {
    final fotos = widget.fotos == 1 ? '1 foto' : '${widget.fotos} fotos';
    return AlertDialog(
      title: const Text('Entregar o registro?'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Quem lê: ${widget.quemLe}'),
          if (widget.trecho != null) Text('Trecho: "${widget.trecho}"'),
          Text('Fotos: $fotos'),
          const SizedBox(height: 12),
          const Text(
            'Depois de entregar, o registro não pode ser editado nem apagado.',
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => _responder(false),
          child: const Text('Voltar'),
        ),
        FilledButton(
          onPressed: () => _responder(true),
          child: const Text('Entregar'),
        ),
      ],
    );
  }
}
