---
id: 004-fotos
status: rascunho
veredito: parcial
---

# Validação — Fotos privadas (manuscrito e perfil)

Evidência do que foi **realmente executado**. A mudança está implementada e testada **localmente**; **nada dela foi visto no ar**, não houve auditoria independente
e o arquivamento não foi feito. Nada commitado ainda (2026-11-05).

## Ambiente
- Backend: máquina local (Windows, Git Bash), PostgreSQL 17 descartável na porta 55433; `uv run pytest`. Pillow 13.0.0 (PyPI, publicada em 2026-10-16), `image_picker` 1.2.4 (pub.dev, publicador `flutter.dev`, publicado em 2026-10-06).
- Front: SDK do Flutter na imagem `entrelinhas-flutter-sdk:local`; `flutter analyze` e `flutter test` no contêiner.
- Navegador: pilha local (`docker compose up`: PostgreSQL, API, nginx com o app) no navegador do aplicativo; a escolha da foto no seletor nativo **não** foi acionada (ver "Não provado").
- Números finais: backend **232 passaram, 12 ignorados** (`jq`, rodam no CI); 48 deles são de `apps/fotos`; front **72 passaram**; `ruff`, `manage.py check` e `makemigrations --check` limpos; `sdd_lint` com 0 erros.

## Critério → evidência
| ID | Como foi provado | Resultado |
|---|---|---|
| REQ-6.1 | `test_req_6_1_envio_valido_*` (JPEG, PNG, WebP), conta sem perfil; no navegador local, o envio por `fetch` com o cookie e o token devolveu 201 | ✔ em teste e no navegador local |
| REQ-6.2, ABU-5 | `test_req_6_2_*` com 10 conteúdos (HTML, ZIP, SVG, GIF válido e quebrado, BMP, TIFF, vazio, JPEG truncado, PDF), todos recusados e nada gravado | ✔ em teste |
| REQ-6.3 | `test_req_6_3_*` (8 MB, 4097 px, 4096 px aceito); no navegador local, 8,5 MB → 422 com a mensagem; 10 MB → 413 do nginx | ✔ em teste e no navegador local |
| REQ-6.4, THR-25 | `test_req_6_4_*`: EXIF (marca, modelo, GPS), bytes depois da imagem e bloco de texto do PNG não chegam ao arquivo; nome UUID; tipo definido pelo servidor | ✔ em teste |
| REQ-6.5 | `test_req_6_5_*`; no navegador local, `Content-Type: image/jpeg`, `Cache-Control: private, no-store`, `X-Content-Type-Options: nosniff` e a CSP do nginx | ✔ em teste e no navegador local |
| REQ-6.6, ABU-6 | `test_req_6_6_*`, `test_abu_6_*` (mesmo grupo, outro grupo, anônimo, id inexistente e malformado) | ✔ em teste |
| REQ-6.7, 6.8 | `test_req_6_7_*`, `test_req_6_8_*` | ✔ em teste |
| REQ-6.9 | `test_req_6_9_*` (avulsa antiga some; avulsa recente e anexada antiga ficam); o `deploy.sh` executado com `docker` falso chama `limpar_fotos` depois de subir | ✔ em teste; **não rodou na VPS** |
| REQ-7.1 a 7.5 | `test_req_7_*`: definir, trocar e remover (registro e arquivo), grupo sem e-mail, parceiro vê e estranho recebe 404, finalidade errada, foto alheia ou inexistente com a mesma recusa | ✔ em teste |
| REQ-7.6, 7.7, 7.8, NFR-FOTO-3 | `foto_perfil_test.dart` (12 testes): prévia, envio em ordem, remoção, erros 422, 413, 429, 401, foto acima de 8 MB, falha do seletor, inicial sobre a cor, texto alternativo, 360 px; `acessibilidade_test.dart` com 2 telas novas (perfil com foto e com foto escolhida) nos dois temas e em 360 e 1280 px | ✔ em teste. No navegador local: a foto apareceu no avatar (o cookie vai junto na imagem), "Remover foto" trocou por "D" sobre a cor e o arquivo sumiu do volume; 360 px conferido |
| ABU-7 | `test_abu_7_*`: 21º envio na hora → 429; envios antigos não contam; 30 avulsas é o teto | ✔ em teste |
| PROP-5 | `test_prop_5_*`: 60 entradas sorteadas (semente fixa) a partir de JPEG com EXIF, PNG e WebP com bytes trocados, lixo no fim e truncamento; sempre recusa sem escrita ou arquivo decodificável sem EXIF; as duas saídas ocorreram | ✔ (exemplos, não prova exaustiva) |
| NFR-FOTO-1, CTL-24 | `test_ctl_24_*`, `test_nfr_foto_1_*` (volume só na API, fora de `static` e `media`) | ✔ em teste |
| NFR-FOTO-2, CTL-22 | `test_nfr_foto_2_*` (9 MB só em `location = /api/v1/fotos`); medido no navegador local (413 acima de 9 MB; outra rota recusa 2 MB) | ✔ |
| CTL-25 | `test_nfr_foto_1_imagem_da_api_*` (pasta 700 do usuário da API), `test_ctl_25_*` (cópia do volume com a API parada, arquivo 600, poda; ordem real do `deploy.sh` com `docker` falso) | ✔ em teste; **o `docker compose cp` real não foi executado** |
| Contrato | `test_ctl_18_*` compara as rotas com o OpenAPI (a 004 saiu de "planejado"); o OpenAPI da 003 ganhou `foto_url`; todos os contratos validam | ✔ |

## Mutação do serviço de fotos
Roteiro com 8 mutantes em `apps/fotos/servicos.py`; os 8 foram mortos: manuscrito visível ao parceiro; foto de perfil visível a qualquer grupo; arquivo guardado sem recodificar;
aceitar qualquer formato; limite de lado ignorado; apagar foto anexada; limpeza apagando anexadas; sem cota por hora. (Os mutantes "mantém o EXIF" e "aceita qualquer formato"
foram refeitos depois que a primeira rodada achou um mutante equivalente e uma amostra de GIF quebrada demais para exercitar a regra; os testes ganharam GIF, BMP e TIFF válidos.)

## Não provado
- **Nada no ar:** o deploy da 004 (volume novo, nginx, backup do volume, `limpar_fotos`) não foi feito; o primeiro deploy deve mostrar "fotos: nada a copiar ainda".
- O seletor nativo de arquivos (`image_picker`) não foi acionado no navegador: o envio foi feito por `fetch` no mesmo navegador, com os mesmos cookies e token. O caminho Flutter → `FormData` → API foi provado só por teste de unidade do cliente HTTP.
- Nenhuma foto de celular real (HEIC convertido, rotação EXIF) foi testada; a rotação é aplicada com `ImageOps.exif_transpose` antes de descartar o EXIF, mas sem foto real.
- `pip-audit` não foi rodado; a dependência Pillow foi conferida só pela data e pela versão no PyPI.
- Sem auditoria independente (T-4.2).

## Veredito
**Parcial.** Código, infra e telas da 004 estão prontos e testados localmente; faltam o deploy e a conferência no ar, a auditoria independente por subagente e o arquivamento em `fotos.md`.
