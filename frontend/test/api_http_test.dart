// [003] Cliente HTTP (ADR-0006): token de CSRF no cabeçalho, renovado depois de entrar e em caso de 403; erros viram ErroApi.
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:entrelinhas/features/hoje/modelos.dart';
import 'package:entrelinhas/shared/api/api.dart';
import 'package:entrelinhas/shared/api/api_http.dart';
import 'package:entrelinhas/shared/push/push_api.dart';
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
  dio: Dio(
    BaseOptions(
      baseUrl: 'http://teste.local/api/v1',
      validateStatus: (_) => true,
    ),
  )..httpClientAdapter = adaptador,
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

  test('[004] REQ-6.1: a foto sobe em multipart, com o token de CSRF, a finalidade e o arquivo', () async {
    final adaptador = AdaptadorFalso(
      (o) => switch (o.path) {
        '/auth/csrf' => json({'token': 'T1'}),
        '/fotos' => json({
          'id': 'abc',
          'finalidade': 'perfil',
          'largura': 10,
          'altura': 20,
        }, 201),
        _ => json({}, 204),
      },
    );

    final foto = await apiCom(adaptador).enviarFoto(
      bytes: Uint8List.fromList([1, 2, 3]),
      nome: 'x.png',
      tipo: 'image/png',
      finalidade: 'perfil',
    );

    final pedido = adaptador.requisicoes.firstWhere((o) => o.path == '/fotos');
    expect(pedido.method, 'POST');
    expect(pedido.headers['X-CSRFToken'], 'T1');
    final dados = pedido.data as FormData;
    expect(dados.fields.single.key, 'finalidade');
    expect(dados.fields.single.value, 'perfil');
    expect(dados.files.single.key, 'arquivo');
    expect(dados.files.single.value.filename, 'x.png');
    expect(foto.id, 'abc');
    expect(foto.largura, 10);
  });

  test('[004] REQ-6.1: depois de um 403 de CSRF a foto é reenviada com um corpo novo (o multipart só vale uma vez)', () async {
    var n = 0;
    final adaptador = AdaptadorFalso((o) {
      if (o.path == '/auth/csrf') return json({'token': 'T${++n}'});
      return o.headers['X-CSRFToken'] == 'T2'
          ? json({
              'id': 'abc',
              'finalidade': 'manuscrito',
              'largura': 1,
              'altura': 1,
            }, 201)
          : json({'detail': 'CSRF Failed'}, 403);
    });

    await apiCom(adaptador).enviarFoto(
      bytes: Uint8List.fromList([1]),
      nome: 'x.png',
      tipo: 'image/png',
      finalidade: 'manuscrito',
    );

    final tentativas = adaptador.requisicoes
        .where((o) => o.path == '/fotos')
        .toList();
    expect(tentativas, hasLength(2));
    expect(identical(tentativas.first.data, tentativas.last.data), isFalse);
  });

  test('[004] REQ-7.1: definir e remover a foto de perfil usam PUT e DELETE em /perfil/foto', () async {
    final adaptador = AdaptadorFalso(
      (o) => switch (o.path) {
        '/auth/csrf' => json({'token': 'T1'}),
        '/perfil/foto' when o.method == 'PUT' => json({
          ...perfilJson,
          'foto_url': 'fotos/abc/arquivo',
        }),
        _ => json({}, 204),
      },
    );
    final api = apiCom(adaptador);

    final perfil = await api.definirFotoDePerfil('abc');
    await api.removerFotoDePerfil();

    expect(perfil.fotoUrl, 'fotos/abc/arquivo');
    final put = adaptador.requisicoes.firstWhere((o) => o.method == 'PUT');
    expect(put.data, {'foto_id': 'abc'});
    expect(
      adaptador.requisicoes.where((o) => o.method == 'DELETE'),
      hasLength(1),
    );
  });

  test(
    '[004] REQ-7.3: nome, cor e foto dos membros vêm do grupo; sem foto, nulo',
    () {
      final grupo = Grupo.fromJson({
        'id': 'g',
        'tipo': 'escrita',
        'limite_membros': 2,
        'vaga': false,
        'membros': [
          {'nome': 'Ana', 'cor': '#4D7C0F', 'foto_url': 'fotos/a/arquivo'},
          {'nome': 'Bia', 'cor': '#B45309', 'foto_url': null},
        ],
      });

      expect(grupo.membros[0].fotoUrl, 'fotos/a/arquivo');
      expect(grupo.membros[1].fotoUrl, isNull);
    },
  );

  group('[006] cliente de registros', () {
    const autorJson = {'nome': 'Ana', 'cor': '#4D7C0F', 'foto_url': null};
    final doAutor = {
      'id': 'r1',
      'data': '2026-11-06',
      'entregue_em': '2026-11-06T12:30:00Z',
      'visibilidade': 'partial',
      'trecho': {'inicio': 1, 'fim': 3},
      'texto': 'abcdef',
      'fotos': ['f1'],
      'autor': autorJson,
      'meu': true,
    };
    final doParceiro = {
      'id': 'r2',
      'data': '2026-11-05',
      'entregue_em': '2026-11-05T12:00:00Z',
      'visibilidade_efetiva': 'private',
      'texto_visivel': null,
      'fotos': <String>[],
      'autor': {'nome': 'Bia', 'cor': '#B45309'},
      'meu': false,
      'aviso': 'Enviado, mas mantido privado pelo autor',
    };

    test('REQ-11.6: entrega leva texto, visibilidade, fotos e trecho em pontos de código, com CSRF', () async {
      final adaptador = AdaptadorFalso(
        (o) => switch (o.path) {
          '/auth/csrf' => json({'token': 'T1'}),
          _ => json(doAutor, 201),
        },
      );

      final r = await apiCom(adaptador).entregarRegistro(
        texto: 'abcdef',
        visibilidade: 'partial',
        fotos: ['f1'],
        trecho: const Trecho(inicio: 1, fim: 3),
      );

      final envio = adaptador.requisicoes.firstWhere(
        (o) => o.path == '/registros',
      );
      expect(envio.method, 'POST');
      expect(envio.headers['X-CSRFToken'], 'T1');
      expect(envio.data, {
        'texto': 'abcdef',
        'visibilidade': 'partial',
        'fotos': ['f1'],
        'trecho': {'inicio': 1, 'fim': 3},
      });
      expect(r.meu, isTrue);
      expect(r.trecho, const Trecho(inicio: 1, fim: 3));
      expect(r.visibilidade, 'partial');
    });

    test('REQ-11.6: sem trecho, o campo nem vai no corpo', () async {
      final adaptador = AdaptadorFalso(
        (o) =>
            o.path == '/auth/csrf' ? json({'token': 'T'}) : json(doAutor, 201),
      );

      await apiCom(
        adaptador,
      ).entregarRegistro(texto: 'abcdef', visibilidade: 'full', fotos: ['f1']);

      final envio = adaptador.requisicoes.firstWhere(
        (o) => o.path == '/registros',
      );
      expect((envio.data as Map).containsKey('trecho'), isFalse);
    });

    test('REQ-12.1: lista pelo mês e lê as duas visões', () async {
      final adaptador = AdaptadorFalso((o) => json([doAutor, doParceiro]));

      final lista = await apiCom(adaptador).listarRegistros('2026-11');

      expect(adaptador.requisicoes.single.uri.query, 'mes=2026-11');
      expect(lista, hasLength(2));
      expect(lista[0].meu, isTrue);
      expect(lista[0].texto, 'abcdef');
      expect(lista[1].meu, isFalse);
      expect(lista[1].texto, isNull);
      expect(lista[1].visibilidade, 'private');
      expect(lista[1].aviso, 'Enviado, mas mantido privado pelo autor');
      expect(lista[1].trecho, isNull);
      expect(lista[1].autor.fotoUrl, isNull);
    });

    test(
      'REQ-12.3: registro do parceiro lido pelo id usa texto_visivel',
      () async {
        final adaptador = AdaptadorFalso(
          (o) => json({...doParceiro, 'texto_visivel': 'só isto'}),
        );

        final r = await apiCom(adaptador).lerRegistro('r2');

        expect(adaptador.requisicoes.single.path, '/registros/r2');
        expect(r.texto, 'só isto');
      },
    );

    test('REQ-11.8: 409 do servidor vira ErroApi com a mensagem', () async {
      final adaptador = AdaptadorFalso(
        (o) => o.path == '/auth/csrf'
            ? json({'token': 'T'})
            : json({'detalhe': 'Você já entregou o registro de hoje.'}, 409),
      );

      await expectLater(
        apiCom(adaptador).entregarRegistro(
          texto: 'abcdefghij',
          visibilidade: 'full',
          fotos: ['f1'],
        ),
        throwsA(
          isA<ErroApi>()
              .having((e) => e.status, 'status', 409)
              .having((e) => e.detalhe, 'detalhe', contains('já entregou')),
        ),
      );
    });
  });

  group('[008] cliente de destaques', () {
    const autor = {'nome': 'Bia', 'cor': '#B45309'};
    final destaque = {
      'id': 'd1',
      'inicio': 5,
      'fim': 18,
      'trecho': 'tudo bem hoje',
      'autor': autor,
      'meu': false,
      'criado_em': '2026-11-06T12:00:00Z',
      'comentarios': [
        {
          'id': 'c1',
          'texto': 'Gostei.',
          'autor': autor,
          'meu': false,
          'criado_em': '2026-11-06T12:05:00Z',
          'editado_em': null,
        },
      ],
    };

    test('REQ-15.2: cria o destaque com posições, comentário e CSRF', () async {
      final adaptador = AdaptadorFalso(
        (o) =>
            o.path == '/auth/csrf' ? json({'token': 'T'}) : json(destaque, 201),
      );

      final d = await apiCom(adaptador)
          .criarDestaque('r1', inicio: 5, fim: 18, comentario: 'Gostei.');

      final envio = adaptador.requisicoes.firstWhere(
        (o) => o.path == '/registros/r1/destaques',
      );
      expect(envio.method, 'POST');
      expect(envio.headers['X-CSRFToken'], 'T');
      expect(envio.data, {'inicio': 5, 'fim': 18, 'comentario': 'Gostei.'});
      expect(d.trecho, 'tudo bem hoje');
      expect(d.comentarios.single.texto, 'Gostei.');
      expect(d.comentarios.single.editadoEm, isNull);
    });

    test('REQ-15.2: sem comentário o campo nem vai no corpo', () async {
      final adaptador = AdaptadorFalso(
        (o) =>
            o.path == '/auth/csrf' ? json({'token': 'T'}) : json(destaque, 201),
      );

      await apiCom(adaptador).criarDestaque('r1', inicio: 0, fim: 3);

      final envio = adaptador.requisicoes.firstWhere(
        (o) => o.path == '/registros/r1/destaques',
      );
      expect((envio.data as Map).containsKey('comentario'), isFalse);
    });

    test(
      'REQ-15.4: lista, comenta, edita e apaga pelas rotas certas',
      () async {
        final adaptador = AdaptadorFalso((o) {
          if (o.path == '/auth/csrf') return json({'token': 'T'});
          if (o.method == 'DELETE') return json({}, 204);
          if (o.path.startsWith('/comentarios') ||
              o.path.endsWith('/comentarios')) {
            return json(
              (destaque['comentarios']! as List).first,
              o.method == 'POST' ? 201 : 200,
            );
          }
          return json([destaque]);
        });
        final api = apiCom(adaptador);

        final lista = await api.listarDestaques('r1');
        await api.comentar('d1', 'oi');
        await api.editarComentario('c1', 'novo');
        await api.apagarComentario('c1');
        await api.apagarDestaque('d1');

        expect(lista.single.id, 'd1');
        final rotas = [
          for (final o in adaptador.requisicoes.where(
            (o) => o.path != '/auth/csrf',
          ))
            '${o.method} ${o.path}',
        ];
        expect(rotas, [
          'GET /registros/r1/destaques',
          'POST /destaques/d1/comentarios',
          'PATCH /comentarios/c1',
          'DELETE /comentarios/c1',
          'DELETE /destaques/d1',
        ]);
      },
    );

    test(
      'REQ-15.8: 403 da regra de negócio chega com a frase do servidor',
      () async {
        final adaptador = AdaptadorFalso(
          (o) => o.path == '/auth/csrf'
              ? json({'token': 'T'})
              : json({'detalhe': 'Só quem escreveu pode fazer isso.'}, 403),
        );

        await expectLater(
          apiCom(adaptador).apagarDestaque('d1'),
          throwsA(
            isA<ErroApi>().having(
              (e) => e.detalhe,
              'detalhe',
              contains('Só quem'),
            ),
          ),
        );
      },
    );
  });

  test(
    '[009] REQ-17.1: o calendário do mês vem com membros e estados alinhados',
    () async {
      final adaptador = AdaptadorFalso(
        (o) => json({
          'mes': '2026-11',
          'hoje': '2026-11-06',
          'membros': [
            {'nome': 'Ana', 'cor': '#4D7C0F', 'foto_url': null},
            {'nome': 'Bia', 'cor': '#B45309', 'foto_url': null},
          ],
          'dias': [
            {
              'data': '2026-11-01',
              'estados': ['escreveu', 'fora'],
              'juntos': false,
            },
            {
              'data': '2026-11-02',
              'estados': ['escreveu', 'escreveu'],
              'juntos': true,
            },
          ],
        }),
      );

      final c = await apiCom(adaptador).calendario('2026-11');

      expect(adaptador.requisicoes.single.uri.query, 'mes=2026-11');
      expect(c.membros.map((m) => m.nome), ['Ana', 'Bia']);
      expect(c.dias[0].estados, ['escreveu', 'fora']);
      expect(c.dias[1].juntos, isTrue);
      expect(c.dias[1].chave, '2026-11-02');
      expect(c.hoje, DateTime(2026, 11, 6));
    },
  );

  group('[010] cliente de lembretes', () {
    test(
      'REQ-18.2: a chave pública vem da API; 503 vira "sem lembretes" (nulo)',
      () async {
        final com = AdaptadorFalso((o) => json({'chave': 'PUB'}));
        final sem = AdaptadorFalso(
          (o) => json({'detalhe': 'Os lembretes não estão disponíveis.'}, 503),
        );

        expect(await apiCom(com).chavePublicaDeLembretes(), 'PUB');
        expect(await apiCom(sem).chavePublicaDeLembretes(), isNull);
      },
    );

    test('REQ-18.2: outro erro na chave (401) continua sendo erro', () async {
      final adaptador = AdaptadorFalso((o) => json({'detalhe': 'x'}, 401));

      await expectLater(
        apiCom(adaptador).chavePublicaDeLembretes(),
        throwsA(isA<ErroApi>().having((e) => e.status, 'status', 401)),
      );
    });

    test('REQ-18.3 e 18.6: guarda e remove a assinatura, com CSRF e o formato do servidor', () async {
      final adaptador = AdaptadorFalso(
        (o) => o.path == '/auth/csrf' ? json({'token': 'T'}) : json({}, 201),
      );
      final api = apiCom(adaptador);

      await api.guardarAssinatura(
        const AssinaturaDoNavegador(
          endpoint: 'https://fcm.googleapis.com/x',
          p256dh: 'P',
          auth: 'A',
        ),
      );
      await api.removerAssinatura('https://fcm.googleapis.com/x');

      final envios = adaptador.requisicoes
          .where((o) => o.path == '/lembretes/assinaturas')
          .toList();
      expect(envios[0].method, 'POST');
      expect(envios[0].headers['X-CSRFToken'], 'T');
      expect(envios[0].data, {
        'endpoint': 'https://fcm.googleapis.com/x',
        'keys': {'p256dh': 'P', 'auth': 'A'},
      });
      expect(envios[1].method, 'DELETE');
      expect(envios[1].data, {'endpoint': 'https://fcm.googleapis.com/x'});
    });
  });

  group('[011] cliente da recuperação de senha', () {
    test('REQ-22.2: o pedido vai com CSRF, só com o e-mail', () async {
      final adaptador = AdaptadorFalso(
        (o) => o.path == '/auth/csrf'
            ? json({'token': 'T'})
            : json({
                'detalhe': 'Se este e-mail tiver conta, enviamos um link.',
              }, 202),
      );

      await apiCom(adaptador).pedirRecuperacao('ana@example.com');

      final envio = adaptador.requisicoes.firstWhere(
        (o) => o.path == '/auth/recuperacao',
      );
      expect(envio.method, 'POST');
      expect(envio.headers['X-CSRFToken'], 'T');
      expect(envio.data, {'email': 'ana@example.com'});
    });

    test(
      'REQ-22.3: a redefinição manda uid, token e a senha nova; 204 sem corpo',
      () async {
        final adaptador = AdaptadorFalso(
          (o) => o.path == '/auth/csrf' ? json({'token': 'T'}) : json({}, 204),
        );

        await apiCom(adaptador).redefinirSenha(
          uid: 'MTA',
          token: 'tok',
          novaSenha: 'senha-nova-bem-comprida',
        );

        final envio = adaptador.requisicoes.firstWhere(
          (o) => o.path == '/auth/redefinir',
        );
        expect(envio.data, {
          'uid': 'MTA',
          'token': 'tok',
          'nova_senha': 'senha-nova-bem-comprida',
        });
      },
    );

    test('REQ-22.4: 400 do link inválido chega como ErroApi com a frase do servidor', () async {
      final adaptador = AdaptadorFalso(
        (o) => o.path == '/auth/csrf'
            ? json({'token': 'T'})
            : json({'detalhe': 'Link inválido ou vencido.'}, 400),
      );

      await expectLater(
        apiCom(adaptador).redefinirSenha(uid: 'x', token: 'y', novaSenha: 'z'),
        throwsA(isA<ErroApi>().having((e) => e.status, 'status', 400)),
      );
    });
  });
}

extension on ApiHttp {
  /// Só para o teste: um pedido que muda estado sem depender do corpo.
  Future<void> criarGrupoOuSair() => sair();
}
