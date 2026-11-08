// API de mentira para os testes de widget: guarda o estado e as chamadas, e pode falhar quando o teste pedir.
import 'dart:async';
import 'dart:typed_data';

import 'package:entrelinhas/features/calendario/modelos.dart';
import 'package:entrelinhas/features/destaques/modelos.dart';
import 'package:entrelinhas/features/hoje/modelos.dart';
import 'package:entrelinhas/shared/api/api.dart';
import 'package:entrelinhas/shared/push/push_api.dart';

const corAmbar = '#B45309';
const corVerde = '#4D7C0F';

Perfil perfilCompleto({
  String email = 'ana@example.com',
  String nome = 'Ana',
  Grupo? grupo,
  String cor = corVerde,
  String? fotoUrl,
}) => Perfil(
  email: email,
  nome: nome,
  cor: cor,
  completo: true,
  grupo: grupo,
  fotoUrl: fotoUrl,
);

/// Hoje, nos testes: 6/11/2026, 12:00 em São Paulo (15:00 UTC).
final agoraDeTeste = DateTime.utc(2026, 11, 6, 15);
const hojeDeTeste = '2026-11-06';

/// Registro na visão do autor (`meu`) ou do parceiro.
Registro registroDe({
  String id = 'r1',
  String data = hojeDeTeste,
  DateTime? entregueEm,
  String nome = 'Ana',
  String cor = corVerde,
  bool meu = true,
  String visibilidade = Visibilidade.todos,
  String? texto = 'Um dia calmo, de muita chuva.',
  Trecho? trecho,
  List<String> fotos = const ['fotoA'],
  String? aviso,
}) => Registro(
  id: id,
  data: data,
  entregueEm: entregueEm ?? DateTime.utc(2026, 11, 6, 12, 30),
  visibilidade: visibilidade,
  texto: texto,
  fotos: fotos,
  autor: Autor(nome: nome, cor: cor),
  meu: meu,
  trecho: trecho,
  aviso: aviso,
);

Destaque destaqueDe({
  String id = 'd1',
  int inicio = 0,
  int fim = 5,
  String trecho = 'Hoje ',
  String nome = 'Bia',
  String cor = corAmbar,
  bool meu = false,
  List<Comentario> comentarios = const [],
}) => Destaque(
  id: id,
  inicio: inicio,
  fim: fim,
  trecho: trecho,
  autor: Autor(nome: nome, cor: cor),
  meu: meu,
  criadoEm: agoraDeTeste,
  comentarios: comentarios,
);

Comentario comentarioDe({
  String id = 'c1',
  String texto = 'Gostei disso.',
  String nome = 'Bia',
  String cor = corAmbar,
  bool meu = false,
}) => Comentario(
  id: id,
  texto: texto,
  autor: Autor(nome: nome, cor: cor),
  meu: meu,
  criadoEm: agoraDeTeste,
);

/// Dia do calendário para os testes; `estados` na ordem dos membros (Ana, Bia).
DiaDoCalendario diaCal(
  int dia, {
  List<String> estados = const ['escreveu', 'escreveu'],
  bool juntos = false,
  int mes = 11,
}) => DiaDoCalendario(
  data: DateTime(2026, mes, dia),
  estados: estados,
  juntos: juntos,
);

Calendario calendarioDe(
  List<DiaDoCalendario> dias, {
  String mes = '2026-11',
  DateTime? hoje,
}) => Calendario(
  mes: mes,
  hoje: hoje ?? DateTime(2026, 11, 6),
  membros: const [
    Autor(nome: 'Ana', cor: corVerde),
    Autor(nome: 'Bia', cor: corAmbar),
  ],
  dias: dias,
);

const perfilIncompleto = Perfil(email: 'dono@example.com', completo: false);

Grupo grupoCom(List<Membro> membros, {bool? vaga}) => Grupo(
  id: 'g1',
  tipo: 'escrita',
  limiteMembros: 2,
  membros: membros,
  vaga: vaga ?? membros.length < 2,
);

class ApiFalsa implements Api {
  ApiFalsa({this.sessao, this.grupoAtual});

  /// Quem está logado; `null` = anônimo.
  Perfil? sessao;
  Grupo? grupoAtual;

  /// Perfil devolvido por `entrar` e por `aceitarConvite` (padrão: o da sessão ou um completo).
  Perfil? perfilDoLogin;
  Object? falhaAoEntrar;
  Object? falhaAoAceitar;
  Object? falhaAoAtualizar;
  Object? falhaAoTrocarSenha;
  Object? falhaAoCriarGrupo;
  Object? falhaAoConvidar;
  Object? falhaAoEnviarFoto;
  Object? falhaAoDefinirFoto;
  Object? falhaAoRemoverFoto;

  /// Registros que a API "tem" (todas as pessoas), já na visão de quem está logado.
  final registros = <Registro>[];
  Object? falhaAoEntregar;
  Object? falhaAoListar;

  /// Falhas consumidas uma por envio de foto, em ordem (`null` = esse envio dá certo).
  final filaDeFalhasDeFoto = <Object?>[];

  /// Enquanto não for completado, a entrega fica pendente (para provar o duplo toque).
  Completer<void>? portaoDaEntrega;
  Map<String, Object?> ultimaEntrega = {};

  /// Destaques por registro (spec 007), já na visão de quem está logado.
  final destaques = <String, List<Destaque>>{};
  Object? falhaAoListarDestaques;
  Object? falhaAoDestacar;
  Object? falhaAoComentar;
  Completer<void>? portaoDoDestaque;
  Completer<void>? portaoDoComentario;
  Map<String, Object?> ultimoDestaque = {};

  /// Calendários por mês (`AAAA-MM`); mês ausente = 422 "grupo ainda não existia".
  final calendarios = <String, Calendario>{};
  Object? falhaAoCalendario;

  /// Recuperação de senha (spec 011).
  Object? falhaAoPedirRecuperacao;
  Object? falhaAoRedefinir;
  Completer<void>? portaoDaRedefinicao;
  Completer<void>? portaoDoPedido;
  final pedidosDeRecuperacao = <String>[];
  Map<String, String> ultimaRedefinicao = {};

  /// Lembretes (spec 010): `null` = servidor sem chaves VAPID (503).
  String? chaveDeLembretes = 'CHAVE-PUBLICA';
  Object? falhaAoGuardarAssinatura;
  Completer<void>? portaoDaAssinatura;
  final assinaturasGuardadas = <AssinaturaDoNavegador>[];
  final assinaturasRemovidas = <String>[];
  int fotosEnviadas = 0;
  Map<String, Object?> ultimaFoto = {};

  final chamadas = <String>[];
  Map<String, String?> ultimoPerfilEnviado = {};
  Map<String, String> ultimoAceite = {};

  @override
  Future<Perfil> entrar(String email, String senha) async {
    chamadas.add('entrar:$email');
    if (falhaAoEntrar != null) throw falhaAoEntrar!;
    sessao = perfilDoLogin ?? perfilCompleto(email: email);
    return sessao!;
  }

  @override
  Future<void> sair() async {
    chamadas.add('sair');
    sessao = null;
  }

  @override
  Future<Perfil> perfil() async {
    chamadas.add('perfil');
    final atual = sessao;
    if (atual == null) throw const ErroApi(401);
    return atual;
  }

  @override
  Future<Perfil> atualizarPerfil({String? nome, String? cor}) async {
    chamadas.add('atualizarPerfil');
    ultimoPerfilEnviado = {'nome': nome, 'cor': cor};
    if (falhaAoAtualizar != null) throw falhaAoAtualizar!;
    final atual = sessao!;
    sessao = Perfil(
      email: atual.email,
      nome: nome ?? atual.nome,
      cor: cor ?? atual.cor,
      completo: true,
      grupo: atual.grupo,
    );
    return sessao!;
  }

  @override
  Future<void> trocarSenha(String atual, String nova) async {
    chamadas.add('trocarSenha');
    if (falhaAoTrocarSenha != null) throw falhaAoTrocarSenha!;
  }

  @override
  Future<Grupo?> grupo() async {
    chamadas.add('grupo');
    return grupoAtual;
  }

  @override
  Future<Grupo> criarGrupo() async {
    chamadas.add('criarGrupo');
    if (falhaAoCriarGrupo != null) throw falhaAoCriarGrupo!;
    final eu = sessao!;
    grupoAtual = grupoCom([
      Membro(nome: eu.nome ?? '', cor: eu.cor ?? corVerde),
    ]);
    sessao = Perfil(
      email: eu.email,
      nome: eu.nome,
      cor: eu.cor,
      completo: eu.completo,
      grupo: grupoAtual,
      fotoUrl: eu.fotoUrl,
    );
    return grupoAtual!;
  }

  @override
  Future<Registro> entregarRegistro({
    required String texto,
    required String visibilidade,
    required List<String> fotos,
    Trecho? trecho,
  }) async {
    chamadas.add('entregarRegistro');
    ultimaEntrega = {
      'texto': texto,
      'visibilidade': visibilidade,
      'fotos': List<String>.of(fotos),
      'trecho': trecho,
    };
    await portaoDaEntrega?.future;
    if (falhaAoEntregar != null) throw falhaAoEntregar!;
    if (registros.any((r) => r.meu && r.data == hojeDeTeste)) {
      throw const ErroApi(409, detalhe: 'Você já entregou o registro de hoje.');
    }
    final eu = sessao!;
    final novo = Registro(
      id: 'novo${registros.length + 1}',
      data: hojeDeTeste,
      entregueEm: agoraDeTeste,
      visibilidade: visibilidade,
      texto: texto,
      fotos: fotos,
      autor: Autor(nome: eu.nome ?? '', cor: eu.cor ?? corVerde),
      meu: true,
      trecho: trecho,
    );
    registros.add(novo);
    return novo;
  }

  @override
  Future<List<Registro>> listarRegistros(String mes) async {
    chamadas.add('listarRegistros:$mes');
    if (falhaAoListar != null) throw falhaAoListar!;
    return registros.where((r) => r.data.startsWith(mes)).toList()
      ..sort((a, b) => b.entregueEm.compareTo(a.entregueEm));
  }

  @override
  Future<Registro> lerRegistro(String id) async {
    chamadas.add('lerRegistro:$id');
    return registros.firstWhere(
      (r) => r.id == id,
      orElse: () => throw const ErroApi(404),
    );
  }

  @override
  Future<void> pedirRecuperacao(String email) async {
    chamadas.add('pedirRecuperacao');
    pedidosDeRecuperacao.add(email);
    await portaoDoPedido?.future;
    if (falhaAoPedirRecuperacao != null) throw falhaAoPedirRecuperacao!;
  }

  @override
  Future<void> redefinirSenha({
    required String uid,
    required String token,
    required String novaSenha,
  }) async {
    chamadas.add('redefinirSenha');
    ultimaRedefinicao = {'uid': uid, 'token': token, 'nova_senha': novaSenha};
    await portaoDaRedefinicao?.future;
    if (falhaAoRedefinir != null) throw falhaAoRedefinir!;
  }

  @override
  Future<String?> chavePublicaDeLembretes() async {
    chamadas.add('chavePublicaDeLembretes');
    return chaveDeLembretes;
  }

  @override
  Future<void> guardarAssinatura(AssinaturaDoNavegador assinatura) async {
    chamadas.add('guardarAssinatura');
    await portaoDaAssinatura?.future;
    if (falhaAoGuardarAssinatura != null) throw falhaAoGuardarAssinatura!;
    assinaturasGuardadas.add(assinatura);
  }

  @override
  Future<void> removerAssinatura(String endpoint) async {
    chamadas.add('removerAssinatura');
    assinaturasRemovidas.add(endpoint);
  }

  @override
  Future<Calendario> calendario(String mes) async {
    chamadas.add('calendario:$mes');
    if (falhaAoCalendario != null) throw falhaAoCalendario!;
    return calendarios[mes] ??
        (throw const ErroApi(
          422,
          campos: {
            'mes': ['O grupo ainda não existia nesse mês.'],
          },
        ));
  }

  @override
  Future<List<Destaque>> listarDestaques(String registroId) async {
    chamadas.add('listarDestaques:$registroId');
    if (falhaAoListarDestaques != null) throw falhaAoListarDestaques!;
    return List.of(destaques[registroId] ?? const []);
  }

  @override
  Future<Destaque> criarDestaque(
    String registroId, {
    required int inicio,
    required int fim,
    String? comentario,
  }) async {
    chamadas.add('criarDestaque');
    ultimoDestaque = {
      'registro': registroId,
      'inicio': inicio,
      'fim': fim,
      'comentario': comentario,
    };
    await portaoDoDestaque?.future;
    if (falhaAoDestacar != null) throw falhaAoDestacar!;
    final eu = sessao!;
    final autor = Autor(nome: eu.nome ?? '', cor: eu.cor ?? corVerde);
    final novo = Destaque(
      id: 'dn${(destaques[registroId]?.length ?? 0) + 1}',
      inicio: inicio,
      fim: fim,
      trecho: '?',
      autor: autor,
      meu: true,
      criadoEm: agoraDeTeste,
      comentarios: [
        if (comentario != null)
          Comentario(
            id: 'cn1',
            texto: comentario,
            autor: autor,
            meu: true,
            criadoEm: agoraDeTeste,
          ),
      ],
    );
    destaques.putIfAbsent(registroId, () => []).add(novo);
    return novo;
  }

  Destaque _destaque(String id) => destaques.values
      .expand((l) => l)
      .firstWhere((d) => d.id == id, orElse: () => throw const ErroApi(404));

  void _trocar(Destaque novo) {
    for (final lista in destaques.values) {
      final i = lista.indexWhere((d) => d.id == novo.id);
      if (i >= 0) lista[i] = novo;
    }
  }

  @override
  Future<void> apagarDestaque(String destaqueId) async {
    chamadas.add('apagarDestaque:$destaqueId');
    final d = _destaque(destaqueId);
    if (!d.meu) {
      throw const ErroApi(403, detalhe: 'Só quem escreveu pode fazer isso.');
    }
    for (final lista in destaques.values) {
      lista.removeWhere((x) => x.id == destaqueId);
    }
  }

  @override
  Future<Comentario> comentar(String destaqueId, String texto) async {
    chamadas.add('comentar');
    await portaoDoComentario?.future;
    if (falhaAoComentar != null) throw falhaAoComentar!;
    final d = _destaque(destaqueId);
    final eu = sessao!;
    final novo = Comentario(
      id: 'cx${d.comentarios.length + 1}',
      texto: texto,
      autor: Autor(nome: eu.nome ?? '', cor: eu.cor ?? corVerde),
      meu: true,
      criadoEm: agoraDeTeste,
    );
    _trocar(d.copiar(comentarios: [...d.comentarios, novo]));
    return novo;
  }

  @override
  Future<Comentario> editarComentario(String comentarioId, String texto) async {
    chamadas.add('editarComentario:$comentarioId');
    for (final d in destaques.values.expand((l) => l).toList()) {
      for (final c in d.comentarios) {
        if (c.id != comentarioId) continue;
        if (!c.meu) {
          throw const ErroApi(
            403,
            detalhe: 'Só quem escreveu pode fazer isso.',
          );
        }
        final novo = Comentario(
          id: c.id,
          texto: texto,
          autor: c.autor,
          meu: true,
          criadoEm: c.criadoEm,
          editadoEm: agoraDeTeste,
        );
        _trocar(
          d.copiar(
            comentarios: [
              for (final x in d.comentarios) x.id == c.id ? novo : x,
            ],
          ),
        );
        return novo;
      }
    }
    throw const ErroApi(404);
  }

  @override
  Future<void> apagarComentario(String comentarioId) async {
    chamadas.add('apagarComentario:$comentarioId');
    for (final d in destaques.values.expand((l) => l).toList()) {
      if (d.comentarios.any((c) => c.id == comentarioId)) {
        _trocar(
          d.copiar(
            comentarios: [
              for (final c in d.comentarios)
                if (c.id != comentarioId) c,
            ],
          ),
        );
        return;
      }
    }
    throw const ErroApi(404);
  }

  @override
  Future<ConviteGerado> gerarConvite() async {
    chamadas.add('gerarConvite');
    if (falhaAoConvidar != null) throw falhaAoConvidar!;
    return ConviteGerado(
      codigo: 'CODIGO123',
      expiraEm: DateTime.utc(2026, 11, 10, 15, 30),
    );
  }

  @override
  Future<FotoEnviada> enviarFoto({
    required Uint8List bytes,
    required String nome,
    required String tipo,
    required String finalidade,
  }) async {
    chamadas.add('enviarFoto:$finalidade');
    ultimaFoto = {
      'tamanho': bytes.length,
      'nome': nome,
      'tipo': tipo,
      'finalidade': finalidade,
    };
    if (filaDeFalhasDeFoto.isNotEmpty) {
      final falha = filaDeFalhasDeFoto.removeAt(0);
      if (falha != null) throw falha;
    }
    if (falhaAoEnviarFoto != null) throw falhaAoEnviarFoto!;
    fotosEnviadas++;
    return FotoEnviada(
      id: 'foto$fotosEnviadas',
      finalidade: finalidade,
      largura: 100,
      altura: 100,
    );
  }

  @override
  Future<Perfil> definirFotoDePerfil(String fotoId) async {
    chamadas.add('definirFotoDePerfil:$fotoId');
    if (falhaAoDefinirFoto != null) throw falhaAoDefinirFoto!;
    final atual = sessao!;
    sessao = Perfil(
      email: atual.email,
      nome: atual.nome,
      cor: atual.cor,
      completo: atual.completo,
      grupo: atual.grupo,
      fotoUrl: 'fotos/$fotoId/arquivo',
    );
    return sessao!;
  }

  @override
  Future<void> removerFotoDePerfil() async {
    chamadas.add('removerFotoDePerfil');
    if (falhaAoRemoverFoto != null) throw falhaAoRemoverFoto!;
    final atual = sessao!;
    sessao = Perfil(
      email: atual.email,
      nome: atual.nome,
      cor: atual.cor,
      completo: atual.completo,
      grupo: atual.grupo,
    );
  }

  @override
  Future<Perfil> aceitarConvite({
    required String codigo,
    required String nome,
    required String email,
    required String senha,
    required String cor,
  }) async {
    chamadas.add('aceitarConvite:$codigo');
    ultimoAceite = {
      'codigo': codigo,
      'nome': nome,
      'email': email,
      'senha': senha,
      'cor': cor,
    };
    if (falhaAoAceitar != null) throw falhaAoAceitar!;
    final dono = Membro(nome: 'Dono', cor: corVerde);
    grupoAtual = grupoCom([dono, Membro(nome: nome, cor: cor)]);
    sessao =
        perfilDoLogin ??
        Perfil(
          email: email,
          nome: nome,
          cor: cor,
          completo: true,
          grupo: grupoAtual,
        );
    return sessao!;
  }
}
