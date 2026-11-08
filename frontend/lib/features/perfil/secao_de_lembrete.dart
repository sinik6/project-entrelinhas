// Seção "Lembrete diário" do Perfil (spec 010, US-18): liga e desliga o aviso das 21h30 neste aparelho.
// A assinatura do navegador vai ao servidor; nada do diário passa por aqui.
import 'package:entrelinhas/features/acesso/sessao.dart';
import 'package:entrelinhas/shared/api/api.dart';
import 'package:entrelinhas/shared/api/erros.dart';
import 'package:entrelinhas/shared/push/push_api.dart';
import 'package:entrelinhas/shared/ui/pagina.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

enum _Estado {
  carregando,
  indisponivel,
  semSuporte,
  precisaInstalar,
  desligado,
  ligado,
  bloqueado,
}

class SecaoDeLembrete extends ConsumerStatefulWidget {
  const SecaoDeLembrete({super.key});

  @override
  ConsumerState<SecaoDeLembrete> createState() => _SecaoDeLembreteState();
}

class _SecaoDeLembreteState extends ConsumerState<SecaoDeLembrete> {
  _Estado _estado = _Estado.carregando;
  String? _chave;
  String? _erro;
  bool _ocupado = false;

  @override
  void initState() {
    super.initState();
    _carregar();
  }

  Future<void> _carregar() async {
    try {
      final chave = await ref.read(apiProvider).chavePublicaDeLembretes();
      if (!mounted) return;
      if (chave == null) {
        setState(() => _estado = _Estado.indisponivel);
        return;
      }
      _chave = chave;
      final push = ref.read(pushApiProvider);
      switch (push.suporte) {
        case SuporteDePush.semSuporte:
          setState(() => _estado = _Estado.semSuporte);
          return;
        case SuporteDePush.precisaInstalar:
          setState(() => _estado = _Estado.precisaInstalar);
          return;
        case SuporteDePush.disponivel:
          break;
      }
      final permissao = await push.permissao();
      final atual = permissao == PermissaoDePush.negada
          ? null
          : await push.assinaturaAtual();
      if (!mounted) return;
      setState(
        () => _estado = permissao == PermissaoDePush.negada
            ? _Estado.bloqueado
            : (atual != null ? _Estado.ligado : _Estado.desligado),
      );
    } on Object catch (erro) {
      if (!mounted) return;
      if (erro is ErroApi && erro.status == 401) {
        ref.read(sessaoProvider.notifier).acabou(erro);
        return;
      }
      // Sem resposta do servidor a seção não aparece: o resto do perfil continua funcionando.
      setState(() => _estado = _Estado.indisponivel);
    }
  }

  Future<void> _alternar(bool ligar) async {
    if (_ocupado) return;
    setState(() {
      _ocupado = true;
      _erro = null;
    });
    final push = ref.read(pushApiProvider);
    final api = ref.read(apiProvider);
    try {
      if (ligar) {
        await _ligar(push, api);
      } else {
        await _desligar(push, api);
      }
    } on Object catch (erro) {
      if (!mounted) return;
      if (erro is ErroApi && erro.status == 401) {
        ref.read(sessaoProvider.notifier).acabou(erro);
        return;
      }
      setState(() {
        _erro = erro is ErroApi
            ? mensagemDoErro(erro)
            : 'Não foi possível ligar o lembrete. Tente de novo.';
      });
    } finally {
      if (mounted) setState(() => _ocupado = false);
    }
  }

  Future<void> _ligar(PushApi push, Api api) async {
    final permissao = await push.pedirPermissao();
    if (!mounted) return;
    if (permissao != PermissaoDePush.concedida) {
      setState(() => _estado = _Estado.bloqueado);
      return;
    }
    final assinatura = await push.assinar(_chave!);
    try {
      await api.guardarAssinatura(assinatura);
    } on Object {
      // O servidor não guardou: não deixa uma assinatura órfã no navegador.
      await push.cancelar();
      rethrow;
    }
    if (mounted) setState(() => _estado = _Estado.ligado);
  }

  Future<void> _desligar(PushApi push, Api api) async {
    final assinatura = await push.assinaturaAtual();
    await push.cancelar();
    if (assinatura != null) {
      try {
        await api.removerAssinatura(assinatura.endpoint);
      } on ErroApi catch (erro) {
        if (erro.status != 404) rethrow;
      }
    }
    if (mounted) setState(() => _estado = _Estado.desligado);
  }

  String get _texto => switch (_estado) {
    _Estado.ligado => 'Ligado neste aparelho.',
    _Estado.bloqueado => 'Bloqueado pelo navegador. Libere as notificações deste site nas configurações do navegador e tente de novo.',
    _Estado.precisaInstalar => 'No iPhone, o lembrete só funciona com o app instalado na tela inicial: toque em Compartilhar e depois em Adicionar à Tela de Início.',
    _Estado.semSuporte => 'Este navegador não permite lembretes.',
    _ => 'Desligado. Ligue para receber um aviso às 21h30 se você ainda não escreveu.',
  };

  @override
  Widget build(BuildContext context) {
    if (_estado == _Estado.carregando || _estado == _Estado.indisponivel) {
      return const SizedBox.shrink();
    }
    final podeMexer =
        !_ocupado &&
        (_estado == _Estado.desligado || _estado == _Estado.ligado);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        titulo(context, 'Lembrete diário'),
        const SizedBox(height: 8),
        SwitchListTile(
          key: const Key('chave-do-lembrete'),
          contentPadding: EdgeInsets.zero,
          title: const Text('Lembrete diário às 21h30'),
          subtitle: Text(_texto),
          value: _estado == _Estado.ligado,
          onChanged: podeMexer ? _alternar : null,
        ),
        Mensagem(_erro, erro: true),
        const SizedBox(height: 24),
      ],
    );
  }
}
