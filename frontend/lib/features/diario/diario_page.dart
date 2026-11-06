// Diário (spec 006, US-12): registros do grupo, por mês, do mais novo para o mais antigo, na visão que a API devolver.
import 'package:entrelinhas/features/acesso/sessao.dart';
import 'package:entrelinhas/features/diario/cartao_de_registro.dart';
import 'package:entrelinhas/features/hoje/modelos.dart';
import 'package:entrelinhas/shared/api/api.dart';
import 'package:entrelinhas/shared/api/erros.dart';
import 'package:entrelinhas/shared/relogio.dart';
import 'package:entrelinhas/shared/ui/pagina.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class DiarioPage extends ConsumerStatefulWidget {
  const DiarioPage({super.key});

  @override
  ConsumerState<DiarioPage> createState() => _DiarioPageState();
}

class _DiarioPageState extends ConsumerState<DiarioPage> {
  late int _ano;
  late int _mes;
  late final int _anoAtual;
  late final int _mesAtual;
  List<Registro>? _registros;
  String? _erro;
  bool _carregando = true;

  /// Número do pedido mais recente: resposta de um mês que a pessoa já deixou para trás é descartada.
  int _pedido = 0;

  @override
  void initState() {
    super.initState();
    final hoje = emSaoPaulo(ref.read(relogioProvider)());
    _ano = _anoAtual = hoje.year;
    _mes = _mesAtual = hoje.month;
    _carregar();
  }

  bool get _noMesAtual => _ano == _anoAtual && _mes == _mesAtual;

  Future<void> _carregar() async {
    final pedido = ++_pedido;
    setState(() {
      _carregando = true;
      _erro = null;
    });
    try {
      final lista = await ref
          .read(apiProvider)
          .listarRegistros(mesDe(_ano, _mes));
      if (!mounted || pedido != _pedido) return;
      setState(() {
        _registros = lista;
        _carregando = false;
      });
    } on Object catch (erro) {
      if (!mounted || pedido != _pedido) return;
      if (erro is ErroApi && erro.status == 401) {
        ref.read(sessaoProvider.notifier).acabou(erro);
        return;
      }
      setState(() {
        _erro = mensagemDoErro(erro);
        _registros = null;
        _carregando = false;
      });
    }
  }

  void _irPara(int ano, int mes) {
    setState(() {
      _ano = ano;
      _mes = mes;
      _registros = null;
    });
    _carregar();
  }

  void _anterior() =>
      _mes == 1 ? _irPara(_ano - 1, 12) : _irPara(_ano, _mes - 1);

  void _seguinte() {
    if (_noMesAtual) return;
    _mes == 12 ? _irPara(_ano + 1, 1) : _irPara(_ano, _mes + 1);
  }

  @override
  Widget build(BuildContext context) {
    final registros = _registros;
    return Pagina(
      filhos: [
        titulo(context, 'Diário'),
        const SizedBox(height: 8),
        Row(
          children: [
            IconButton(
              tooltip: 'Mês anterior',
              icon: const Icon(Icons.chevron_left),
              onPressed: _anterior,
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
              onPressed: _noMesAtual ? null : _seguinte,
            ),
          ],
        ),
        const SizedBox(height: 8),
        if (_carregando && registros == null)
          Center(
            child: Semantics(
              label: 'Carregando',
              child: const CircularProgressIndicator(),
            ),
          )
        else if (_erro != null) ...[
          Mensagem(_erro, erro: true),
          const SizedBox(height: 8),
          Align(
            alignment: Alignment.centerLeft,
            child: OutlinedButton(
              onPressed: _carregar,
              child: const Text('Tentar de novo'),
            ),
          ),
        ] else if (registros != null && registros.isEmpty)
          const Mensagem('Nenhum registro neste mês.')
        else if (registros != null)
          for (final registro in registros)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: CartaoDeRegistro(registro: registro),
            ),
      ],
    );
  }
}
