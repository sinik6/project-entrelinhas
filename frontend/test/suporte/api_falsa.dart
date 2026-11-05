// API de mentira para os testes de widget: guarda o estado e as chamadas, e pode falhar quando o teste pedir.
import 'package:entrelinhas/shared/api/api.dart';

const corAmbar = '#B45309';
const corVerde = '#4D7C0F';

Perfil perfilCompleto({
  String email = 'ana@example.com',
  String nome = 'Ana',
  Grupo? grupo,
  String cor = corVerde,
}) => Perfil(email: email, nome: nome, cor: cor, completo: true, grupo: grupo);

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
    return grupoAtual!;
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
