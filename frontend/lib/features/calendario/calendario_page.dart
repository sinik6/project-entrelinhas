// Calendário (spec 009, US-17): a grade do mês com o estado de cada pessoa em cada dia, derivado dos registros pela API.
import 'package:entrelinhas/features/acesso/sessao.dart';
import 'package:entrelinhas/features/calendario/marcador.dart';
import 'package:entrelinhas/features/calendario/modelos.dart';
import 'package:entrelinhas/features/diario/cartao_de_registro.dart';
import 'package:entrelinhas/features/hoje/modelos.dart';
import 'package:entrelinhas/shared/api/api.dart';
import 'package:entrelinhas/shared/api/erros.dart';
import 'package:entrelinhas/shared/relogio.dart';
import 'package:entrelinhas/shared/ui/cores.dart';
import 'package:entrelinhas/shared/ui/pagina.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

const _diasDaSemana = ['dom', 'seg', 'ter', 'qua', 'qui', 'sex', 'sáb'];

/// "Dia 12: Ana escreveu; Bia não escreveu; escreveram juntos" (REQ-17.3).
String rotuloDoDia(DiaDoCalendario dia, List<Autor> membros) {
  final partes = <String>[
    for (var i = 0; i < membros.length && i < dia.estados.length; i++)
      switch (dia.estados[i]) {
        EstadoDoDia.escreveu => '${membros[i].nome} escreveu',
        EstadoDoDia.falhou => '${membros[i].nome} não escreveu',
        EstadoDoDia.pendente => '${membros[i].nome} ainda não escreveu',
        _ => '${membros[i].nome} ainda não estava no grupo',
      },
    if (dia.juntos) 'escreveram juntos',
  ];
  return 'Dia ${dia.data.day}: ${partes.join('; ')}';
}

class CalendarioPage extends ConsumerStatefulWidget {
  const CalendarioPage({super.key});

  @override
  ConsumerState<CalendarioPage> createState() => _CalendarioPageState();
}

class _CalendarioPageState extends ConsumerState<CalendarioPage> {
  late int _ano;
  late int _mes;
  late final int _anoAtual;
  late final int _mesAtual;
  Calendario? _calendario;
  String? _erro;
  bool _carregando = true;
  bool _semAnterior = false;

  /// Resposta de um mês que a pessoa já deixou para trás é descartada.
  int _pedido = 0;

  @override
  void initState() {
    super.initState();
    final hoje = emSaoPaulo(ref.read(relogioProvider)());
    _ano = _anoAtual = hoje.year;
    _mes = _mesAtual = hoje.month;
    _carregar(_ano, _mes);
  }

  bool get _noMesAtual => _ano == _anoAtual && _mes == _mesAtual;

  Future<void> _carregar(int ano, int mes) async {
    final pedido = ++_pedido;
    setState(() {
      _carregando = true;
      _erro = null;
    });
    try {
      final calendario = await ref
          .read(apiProvider)
          .calendario(mesDe(ano, mes));
      if (!mounted || pedido != _pedido) return;
      setState(() {
        _ano = ano;
        _mes = mes;
        _calendario = calendario;
        _carregando = false;
      });
    } on Object catch (erro) {
      if (!mounted || pedido != _pedido) return;
      if (erro is ErroApi && erro.status == 401) {
        ref.read(sessaoProvider.notifier).acabou(erro);
        return;
      }
      if (erro is ErroApi && erro.status == 422 && _calendario != null) {
        // O grupo ainda não existia nesse mês: fica onde estava e não oferece voltar mais.
        setState(() {
          _semAnterior = true;
          _carregando = false;
        });
        return;
      }
      setState(() {
        _erro = mensagemDoErro(erro);
        _carregando = false;
      });
    }
  }

  void _anterior() =>
      _mes == 1 ? _carregar(_ano - 1, 12) : _carregar(_ano, _mes - 1);

  void _seguinte() {
    if (_noMesAtual) return;
    _semAnterior = false;
    _mes == 12 ? _carregar(_ano + 1, 1) : _carregar(_ano, _mes + 1);
  }

  void _abrirDia(DiaDoCalendario dia) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (_) => _FolhaDoDia(dia: dia),
    );
  }

  Widget _celula(DiaDoCalendario? dia, Calendario cal) {
    if (dia == null) return const SizedBox(height: 64);
    final tema = Theme.of(context);
    final hoje =
        dia.data.year == cal.hoje.year &&
        dia.data.month == cal.hoje.month &&
        dia.data.day == cal.hoje.day;
    return Semantics(
      container: true,
      button: true,
      label: rotuloDoDia(dia, cal.membros),
      excludeSemantics: true,
      child: InkWell(
        key: Key('dia-${dia.chave}'),
        borderRadius: BorderRadius.circular(8),
        onTap: () => _abrirDia(dia),
        child: Container(
          height: 64,
          decoration: hoje
              ? BoxDecoration(
                  border: Border.all(color: tema.colorScheme.primary, width: 2),
                  borderRadius: BorderRadius.circular(8),
                )
              : null,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('${dia.data.day}', style: tema.textTheme.labelLarge),
              const SizedBox(height: 4),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  for (var i = 0; i < cal.membros.length; i++)
                    if (MarcadorDeEstado.formaDe(dia.estados[i]) !=
                        FormaDoMarcador.nenhuma)
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 1),
                        child: MarcadorDeEstado(
                          key: Key('marcador-${dia.chave}-$i'),
                          estado: dia.estados[i],
                          cor: corDeTexto(cal.membros[i].cor),
                          tamanho: 12,
                        ),
                      ),
                  if (dia.juntos)
                    Padding(
                      padding: const EdgeInsets.only(left: 2),
                      child: Icon(
                        Icons.people_alt,
                        key: Key('selo-juntos-${dia.chave}'),
                        size: 14,
                        color: tema.colorScheme.onSurface,
                      ),
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _grade(Calendario cal) {
    final porDia = {for (final d in cal.dias) d.data.day: d};
    final total = DateTime(_ano, _mes + 1, 0).day;
    final deslocamento = DateTime(_ano, _mes, 1).weekday % 7; // domingo = 0
    final celulas = <Widget>[
      for (var i = 0; i < deslocamento; i++) const SizedBox(height: 64),
      for (var d = 1; d <= total; d++) _celula(porDia[d], cal),
    ];
    while (celulas.length % 7 != 0) {
      celulas.add(const SizedBox(height: 64));
    }
    return Column(
      children: [
        Row(
          children: [
            for (final nome in _diasDaSemana)
              Expanded(
                child: Center(
                  child: Text(
                    nome,
                    style: Theme.of(context).textTheme.labelMedium,
                  ),
                ),
              ),
          ],
        ),
        const SizedBox(height: 4),
        for (var linha = 0; linha < celulas.length; linha += 7)
          Row(
            children: [
              for (final c in celulas.sublist(linha, linha + 7))
                Expanded(child: c),
            ],
          ),
      ],
    );
  }

  Widget _legenda(Calendario cal) {
    final esquema = Theme.of(context).colorScheme;
    Widget item(Widget forma, String texto) => Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        forma,
        const SizedBox(width: 6),
        Flexible(child: Text(texto)),
      ],
    );
    return Container(
      key: const Key('legenda'),
      child: Wrap(
        spacing: 16,
        runSpacing: 8,
        children: [
          item(
            MarcadorDeEstado(
              estado: EstadoDoDia.escreveu,
              cor: esquema.onSurface,
            ),
            'Escreveu',
          ),
          item(
            MarcadorDeEstado(
              estado: EstadoDoDia.falhou,
              cor: esquema.onSurface,
            ),
            'Não escreveu',
          ),
          item(
            MarcadorDeEstado(
              estado: EstadoDoDia.pendente,
              cor: esquema.onSurface,
            ),
            'Ainda dá tempo (hoje)',
          ),
          item(
            Icon(Icons.people_alt, size: 14, color: esquema.onSurface),
            'Escreveram juntos',
          ),
          const Text('Em branco: antes de entrar no grupo'),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final cal = _calendario;
    return Align(
      alignment: Alignment.topCenter,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 560),
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(8, 16, 8, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16),
                child: titulo(context, 'Calendário'),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  IconButton(
                    tooltip: 'Mês anterior',
                    icon: const Icon(Icons.chevron_left),
                    onPressed: _semAnterior || _carregando ? null : _anterior,
                  ),
                  Expanded(
                    child: Semantics(
                      liveRegion: true,
                      child: Text(
                        nomeDoMes(_ano, _mes),
                        textAlign: TextAlign.center,
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                    ),
                  ),
                  IconButton(
                    tooltip: 'Mês seguinte',
                    icon: const Icon(Icons.chevron_right),
                    onPressed: _noMesAtual || _carregando ? null : _seguinte,
                  ),
                ],
              ),
              const SizedBox(height: 8),
              if (_erro != null) ...[
                Mensagem(_erro, erro: true),
                Align(
                  alignment: Alignment.centerLeft,
                  child: OutlinedButton(
                    onPressed: () => _carregar(_ano, _mes),
                    child: const Text('Tentar de novo'),
                  ),
                ),
              ] else if (cal == null)
                Center(
                  child: Semantics(
                    label: 'Carregando',
                    child: const CircularProgressIndicator(),
                  ),
                )
              else ...[
                _grade(cal),
                const SizedBox(height: 16),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  child: _legenda(cal),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

/// Registros de um dia, na visão de quem pede (a mesma do Diário).
class _FolhaDoDia extends ConsumerStatefulWidget {
  const _FolhaDoDia({required this.dia});

  final DiaDoCalendario dia;

  @override
  ConsumerState<_FolhaDoDia> createState() => _FolhaDoDiaState();
}

class _FolhaDoDiaState extends ConsumerState<_FolhaDoDia> {
  List<Registro>? _registros;
  String? _erro;

  @override
  void initState() {
    super.initState();
    _carregar();
  }

  Future<void> _carregar() async {
    setState(() => _erro = null);
    final data = widget.dia.data;
    try {
      final lista = await ref
          .read(apiProvider)
          .listarRegistros(mesDe(data.year, data.month));
      if (!mounted) return;
      setState(
        () => _registros = [
          for (final r in lista)
            if (r.data == widget.dia.chave) r,
        ],
      );
    } on Object catch (erro) {
      if (!mounted) return;
      if (erro is ErroApi && erro.status == 401) {
        ref.read(sessaoProvider.notifier).acabou(erro);
        Navigator.of(context).pop();
        return;
      }
      setState(() => _erro = mensagemDoErro(erro));
    }
  }

  @override
  Widget build(BuildContext context) {
    final registros = _registros;
    final data = widget.dia.data;
    return SafeArea(
      child: SingleChildScrollView(
        key: const Key('folha-do-dia'),
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            titulo(
              context,
              'Dia ${data.day} de ${nomeDoMes(data.year, data.month)}',
            ),
            const SizedBox(height: 12),
            if (_erro != null) ...[
              Mensagem(_erro, erro: true),
              Align(
                alignment: Alignment.centerLeft,
                child: OutlinedButton(
                  onPressed: _carregar,
                  child: const Text('Tentar de novo'),
                ),
              ),
            ] else if (registros == null)
              Center(
                child: Semantics(
                  label: 'Carregando',
                  child: const CircularProgressIndicator(),
                ),
              )
            else if (registros.isEmpty)
              const Mensagem('Nenhum registro neste dia.')
            else
              for (final r in registros)
                Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: CartaoDeRegistro(registro: r),
                ),
          ],
        ),
      ),
    );
  }
}
