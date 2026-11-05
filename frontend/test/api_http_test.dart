// [003] Cliente HTTP (ADR-0006): token de CSRF no cabeçalho, renovado depois de entrar e em caso de 403; erros viram ErroApi.
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:entrelinhas/shared/api/api.dart';
import 'package:entrelinhas/shared/api/api_http.dart';
import 'package:flutter_test/flutter_test.dart';

class AdaptadorFalso implements HttpClientAdapter {
  AdaptadorFalso(this.responder);

  final ResponseBody Function(RequestOptions) responder;
  final requisicoes = <RequestOptions>[];

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    requisicoes.add(options);
    return responder(options);
  }

  @override
  void close({bool force = false}) {}
}

ResponseBody json(Object corpo, [int status = 200]) => ResponseBody.fromString(
  jsonEncode(corpo),
  status,
  headers: {
    Headers.contentTypeHeader: [Headers.jsonContentType],
  },
);

const perfilJson = {
  'email': 'ana@example.com',
  'nome': 'Ana',
  'cor': '#4D7C0F',
  'completo': true,
  'grupo': null,
};

ApiHttp apiCom(AdaptadorFalso adaptador) => ApiHttp(
  dio: Dio(BaseOptions(baseUrl: 'http://teste.local/api/v1', validateStatus: (_) => true))
    ..httpClientAdapter = adaptador,
);

void main() {
  test('[003] ABU-4: pedido que muda estado leva o token de /auth/csrf em X-CSRFToken; leitura não precisa', () async {
    final adaptador = AdaptadorFalso(
      (o) => switch (o.path) {
        '/auth/csrf' => json({'token': 'T1'}),
        '/perfil' => json(perfilJson),
        _ => json({}, 204),
      },
    );
    final api = apiCom(adaptador);

    await api.perfil();
    await api.criarGrupoOuSair();

    final leitura = adaptador.requisicoes.firstWhere(
      (o) => o.path == '/perfil',
    );
    final escrita = adaptador.requisicoes.firstWhere(
      (o) => o.path == '/auth/sair',
    );
    expect(leitura.headers.containsKey('X-CSRFToken'), isFalse);
    expect(escrita.method, 'POST');
    expect(escrita.headers['X-CSRFToken'], 'T1');
  });

  test('[003] ABU-4: depois de entrar o token antigo é esquecido e um novo é buscado', () async {
    var n = 0;
    final adaptador = AdaptadorFalso(
      (o) => switch (o.path) {
        '/auth/csrf' => json({'token': 'T${++n}'}),
        '/auth/entrar' => json(perfilJson),
        _ => json({}, 204),
      },
    );
    final api = apiCom(adaptador);

    await api.entrar('ana@example.com', 'senha-longa-demais-1');
    await api.sair();

    final entrar = adaptador.requisicoes.firstWhere(
      (o) => o.path == '/auth/entrar',
    );
    final sair = adaptador.requisicoes.firstWhere(
      (o) => o.path == '/auth/sair',
    );
    expect(entrar.headers['X-CSRFToken'], 'T1');
    expect(sair.headers['X-CSRFToken'], 'T2');
    expect(
      adaptador.requisicoes.where((o) => o.path == '/auth/csrf'),
      hasLength(2),
    );
  });

  test(
    '[003] ABU-4: 403 renova o token e tenta de novo uma única vez',
    () async {
      var n = 0;
      final adaptador = AdaptadorFalso((o) {
        if (o.path == '/auth/csrf') return json({'token': 'T${++n}'});
        return o.headers['X-CSRFToken'] == 'T2'
            ? json({}, 204)
            : json({'detail': 'CSRF Failed'}, 403);
      });

      await apiCom(adaptador).sair();

      final tentativas = adaptador.requisicoes
          .where((o) => o.path == '/auth/sair')
          .toList();
      expect(tentativas, hasLength(2));
      expect(tentativas.last.headers['X-CSRFToken'], 'T2');
    },
  );

  test('[003] ABU-4: 403 que continua depois de renovar vira erro, sem repetir sem fim', () async {
    final adaptador = AdaptadorFalso(
      (o) => o.path == '/auth/csrf'
          ? json({'token': 'T'})
          : json({'detail': 'CSRF Failed'}, 403),
    );

    await expectLater(
      apiCom(adaptador).sair(),
      throwsA(isA<ErroApi>().having((e) => e.status, 'status', 403)),
    );
    expect(
      adaptador.requisicoes.where((o) => o.path == '/auth/sair'),
      hasLength(2),
    );
  });

  test(
    '[003] REQ-5.4: 422 traz os erros por campo; 400 traz a mensagem única',
    () async {
      final adaptador = AdaptadorFalso(
        (o) => switch (o.path) {
          '/auth/csrf' => json({'token': 'T'}),
          '/perfil' => json({
            'campos': {
              'cor': ['Essa cor fica ilegível.'],
            },
          }, 422),
          _ => json({'detalhe': 'E-mail ou senha incorretos.'}, 400),
        },
      );
      final api = apiCom(adaptador);

      await expectLater(
        api.atualizarPerfil(cor: '#FFFFFF'),
        throwsA(
          isA<ErroApi>().having((e) => e.status, 'status', 422).having(
            (e) => e.campos['cor'],
            'cor',
            ['Essa cor fica ilegível.'],
          ),
        ),
      );
      await expectLater(
        api.entrar('a@b.c', 'x'),
        throwsA(
          isA<ErroApi>()
              .having((e) => e.status, 'status', 400)
              .having(
                (e) => e.detalhe,
                'detalhe',
                'E-mail ou senha incorretos.',
              ),
        ),
      );
    },
  );

  test('[003] REQ-5.4: falha de rede vira ErroApi com status 0', () async {
    final adaptador = AdaptadorFalso(
      (o) => throw DioException(
        requestOptions: o,
        type: DioExceptionType.connectionError,
      ),
    );

    await expectLater(
      apiCom(adaptador).perfil(),
      throwsA(isA<ErroApi>().having((e) => e.status, 'status', 0)),
    );
  });

  test(
    '[003] REQ-4.1: o perfil devolvido pela API vira o modelo do app',
    () async {
      final adaptador = AdaptadorFalso((o) => json(perfilJson));

      final perfil = await apiCom(adaptador).perfil();

      expect(perfil.email, 'ana@example.com');
      expect(perfil.nome, 'Ana');
      expect(perfil.completo, isTrue);
      expect(perfil.grupo, isNull);
    },
  );
}

extension on ApiHttp {
  /// Só para o teste: um pedido que muda estado sem depender do corpo.
  Future<void> criarGrupoOuSair() => sair();
}
