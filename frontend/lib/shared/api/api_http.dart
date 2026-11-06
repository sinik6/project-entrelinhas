// Cliente HTTP da API (ADR-0006): mesma origem, sessão em cookie que o script não lê, CSRF por token no cabeçalho.
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:entrelinhas/features/hoje/modelos.dart';
import 'package:entrelinhas/shared/api/api.dart';

class ApiHttp implements Api {
  ApiHttp({Dio? dio})
    : _dio =
          dio ??
          Dio(
            BaseOptions(
              baseUrl: const String.fromEnvironment(
                'API_BASE',
                defaultValue: '/api/v1',
              ),
              connectTimeout: const Duration(seconds: 10),
              receiveTimeout: const Duration(seconds: 20),
              headers: {'Accept': 'application/json'},
              // Quem decide o que é erro é este cliente, pelo status, e não o dio.
              validateStatus: (_) => true,
            ),
          );

  final Dio _dio;
  String? _token;

  Future<String> _csrf() async {
    final resposta = await _enviar('GET', '/auth/csrf');
    return _token = (resposta.data as Map<String, dynamic>)['token'] as String;
  }

  Future<Response<dynamic>> _enviar(
    String metodo,
    String caminho, {
    Object? corpo,
    String? token,
  }) async {
    try {
      return await _dio.request<dynamic>(
        caminho,
        data: corpo,
        options: Options(
          method: metodo,
          headers: token == null ? null : {'X-CSRFToken': token},
        ),
      );
    } on DioException {
      throw const ErroApi(0);
    }
  }

  /// Pedido que muda estado: leva o token e, se o servidor recusar o token (403), busca outro e tenta uma vez.
  Future<dynamic> _alterar(
    String metodo,
    String caminho, {
    Object? corpo,
    Object? Function()? fabricaDoCorpo,
  }) async {
    // `fabricaDoCorpo` cria um corpo novo a cada tentativa: o multipart só pode ser enviado uma vez.
    var resposta = await _enviar(
      metodo,
      caminho,
      corpo: fabricaDoCorpo?.call() ?? corpo,
      token: _token ?? await _csrf(),
    );
    if (resposta.statusCode == 403) {
      resposta = await _enviar(
        metodo,
        caminho,
        corpo: fabricaDoCorpo?.call() ?? corpo,
        token: await _csrf(),
      );
    }
    return _resultado(resposta);
  }

  Future<dynamic> _ler(String caminho) async =>
      _resultado(await _enviar('GET', caminho));

  dynamic _resultado(Response<dynamic> resposta) {
    final status = resposta.statusCode ?? 0;
    if (status < 400) return resposta.data;
    final dados = resposta.data;
    final mapa = dados is Map<String, dynamic>
        ? dados
        : const <String, dynamic>{};
    final campos = <String, List<String>>{};
    final brutos = mapa['campos'];
    if (brutos is Map<String, dynamic>) {
      brutos.forEach(
        (campo, mensagens) => campos[campo] = [
          for (final m in mensagens as List<dynamic>) m.toString(),
        ],
      );
    }
    throw ErroApi(status, detalhe: mapa['detalhe'] as String?, campos: campos);
  }

  /// Depois de entrar o servidor troca o segredo do CSRF: o token antigo deixa de valer.
  void _esquecerToken() => _token = null;

  @override
  Future<Perfil> entrar(String email, String senha) async {
    final dados = await _alterar(
      'POST',
      '/auth/entrar',
      corpo: {'email': email, 'senha': senha},
    );
    _esquecerToken();
    return Perfil.fromJson(dados as Map<String, dynamic>);
  }

  @override
  Future<void> sair() async {
    await _alterar('POST', '/auth/sair');
    _esquecerToken();
  }

  @override
  Future<Perfil> perfil() async =>
      Perfil.fromJson(await _ler('/perfil') as Map<String, dynamic>);

  @override
  Future<Perfil> atualizarPerfil({String? nome, String? cor}) async {
    final dados = await _alterar(
      'PATCH',
      '/perfil',
      corpo: {'nome': ?nome, 'cor': ?cor},
    );
    return Perfil.fromJson(dados as Map<String, dynamic>);
  }

  @override
  Future<void> trocarSenha(String atual, String nova) async {
    await _alterar(
      'POST',
      '/perfil/senha',
      corpo: {'senha_atual': atual, 'senha_nova': nova},
    );
  }

  @override
  Future<Grupo?> grupo() async {
    final dados = await _ler('/grupo') as Map<String, dynamic>;
    return dados['grupo'] == null
        ? null
        : Grupo.fromJson(dados['grupo'] as Map<String, dynamic>);
  }

  @override
  Future<Grupo> criarGrupo() async =>
      Grupo.fromJson(await _alterar('POST', '/grupo') as Map<String, dynamic>);

  @override
  Future<FotoEnviada> enviarFoto({
    required Uint8List bytes,
    required String nome,
    required String tipo,
    required String finalidade,
  }) async {
    final dados = await _alterar(
      'POST',
      '/fotos',
      fabricaDoCorpo: () => FormData.fromMap({
        'finalidade': finalidade,
        'arquivo': MultipartFile.fromBytes(
          bytes,
          filename: nome,
          contentType: DioMediaType.parse(tipo),
        ),
      }),
    );
    return FotoEnviada.fromJson(dados as Map<String, dynamic>);
  }

  @override
  Future<Perfil> definirFotoDePerfil(String fotoId) async => Perfil.fromJson(
    await _alterar('PUT', '/perfil/foto', corpo: {'foto_id': fotoId})
        as Map<String, dynamic>,
  );

  @override
  Future<void> removerFotoDePerfil() async {
    await _alterar('DELETE', '/perfil/foto');
  }

  @override
  Future<Registro> entregarRegistro({
    required String texto,
    required String visibilidade,
    required List<String> fotos,
    Trecho? trecho,
  }) async => Registro.fromJson(
    await _alterar(
      'POST',
      '/registros',
      corpo: {
        'texto': texto,
        'visibilidade': visibilidade,
        'fotos': fotos,
        if (trecho != null) 'trecho': trecho.toJson(),
      },
    ) as Map<String, dynamic>,
  );

  @override
  Future<List<Registro>> listarRegistros(String mes) async => [
    for (final r in await _ler('/registros?mes=$mes') as List<dynamic>)
      Registro.fromJson(r as Map<String, dynamic>),
  ];

  @override
  Future<Registro> lerRegistro(String id) async =>
      Registro.fromJson(await _ler('/registros/$id') as Map<String, dynamic>);

  @override
  Future<ConviteGerado> gerarConvite() async => ConviteGerado.fromJson(
    await _alterar('POST', '/grupo/convites') as Map<String, dynamic>,
  );

  @override
  Future<Perfil> aceitarConvite({
    required String codigo,
    required String nome,
    required String email,
    required String senha,
    required String cor,
  }) async {
    final dados = await _alterar(
      'POST',
      '/convites/aceitar',
      corpo: {
        'codigo': codigo,
        'nome': nome,
        'email': email,
        'senha': senha,
        'cor': cor,
      },
    );
    _esquecerToken();
    return Perfil.fromJson(dados as Map<String, dynamic>);
  }
}
