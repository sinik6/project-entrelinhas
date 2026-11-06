// Rascunho do dia (spec 006, REQ-11.9): vive só na memória do app. Nada daqui vai para o armazenamento do navegador;
// recarregar a página descarta tudo, de propósito (texto íntimo em aparelho que pode ser compartilhado).
import 'package:entrelinhas/shared/foto/seletor_de_foto.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Foto escolhida; `idEnviado` aparece quando ela já subiu (um novo envio não a manda de novo).
class FotoDoRascunho {
  const FotoDoRascunho({required this.foto, this.idEnviado});

  final FotoEscolhida foto;
  final String? idEnviado;

  FotoDoRascunho comId(String id) => FotoDoRascunho(foto: foto, idEnviado: id);
}

/// Trecho escolhido, nas duas contagens. O texto do rascunho precisa ser o mesmo de quando ele foi escolhido.
class TrechoDoRascunho {
  const TrechoDoRascunho({
    required this.inicioUtf16,
    required this.fimUtf16,
    required this.inicioPontos,
    required this.fimPontos,
  });

  final int inicioUtf16;
  final int fimUtf16;
  final int inicioPontos;
  final int fimPontos;
}

class Rascunho {
  const Rascunho({
    this.texto = '',
    this.fotos = const [],
    this.visibilidade,
    this.trecho,
  });

  final String texto;
  final List<FotoDoRascunho> fotos;

  /// `null` = a pessoa ainda não escolheu (não existe opção padrão).
  final String? visibilidade;
  final TrechoDoRascunho? trecho;

  Rascunho copiar({
    String? texto,
    List<FotoDoRascunho>? fotos,
    String? Function()? visibilidade,
    TrechoDoRascunho? Function()? trecho,
  }) => Rascunho(
    texto: texto ?? this.texto,
    fotos: fotos ?? this.fotos,
    visibilidade: visibilidade == null ? this.visibilidade : visibilidade(),
    trecho: trecho == null ? this.trecho : trecho(),
  );
}

class RascunhoNotifier extends Notifier<Rascunho> {
  @override
  Rascunho build() => const Rascunho();

  /// O rascunho de agora, lido sem `ref` (a tela pode ter sido fechada no meio de um envio).
  Rascunho get atual => state;

  void texto(String novo) => state = state.copiar(texto: novo);

  void adicionarFoto(FotoEscolhida foto) => state = state.copiar(
    fotos: [
      ...state.fotos,
      FotoDoRascunho(foto: foto),
    ],
  );

  void tirarFoto(int indice) => state = state.copiar(
    fotos: [
      for (var i = 0; i < state.fotos.length; i++)
        if (i != indice) state.fotos[i],
    ],
  );

  void fotoEnviada(int indice, String id) => state = state.copiar(
    fotos: [
      for (var i = 0; i < state.fotos.length; i++)
        i == indice ? state.fotos[i].comId(id) : state.fotos[i],
    ],
  );

  /// Trocar a visibilidade descarta o trecho: ao voltar para "só um trecho" ele é escolhido de novo.
  void visibilidade(String valor) =>
      state = state.copiar(visibilidade: () => valor, trecho: () => null);

  void trecho(TrechoDoRascunho? valor) =>
      state = state.copiar(trecho: () => valor);

  void limpar() => state = const Rascunho();
}

final rascunhoProvider = NotifierProvider<RascunhoNotifier, Rascunho>(
  RascunhoNotifier.new,
);
