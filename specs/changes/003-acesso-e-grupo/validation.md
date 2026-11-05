---
id: 003-acesso-e-grupo
status: rascunho
veredito: parcial
---

# Validação — Contas, perfil, grupo de escrita, convite e casca do front

Evidência do que foi **realmente executado**. A mudança **não está fechada**: faltam o teste do segundo participante no navegador, a conferência no ar pelo
dono, a auditoria independente e o arquivamento. Commits desta mudança: `a7eb1bf`, `c8e6cb3`, `ca2a7c8` (na `main`).

## Ambiente
- Backend: máquina local (Windows, Git Bash), PostgreSQL 17 descartável na porta 55433; `uv run pytest`. Os 12 testes que dependem de `jq` foram ignorados localmente (rodam no CI, Linux).
- Front: SDK do Flutter na imagem `entrelinhas-flutter-sdk:local` (versão fixa, SHA-256 conferido no build), `flutter analyze` e `flutter test` no contêiner.
- Navegador: pilha local (`docker compose up`: PostgreSQL, API, nginx com o app) aberta no navegador do aplicativo, em 2026-11-05.
- Produção: `https://jpsys.duckdns.org/entrelinhas`, sondada por `curl` em 2026-11-05 depois do deploy (CI e deploy verdes, informado pelo usuário).

## Critério → evidência
| ID | Como foi provado | Resultado |
|---|---|---|
| REQ-1.1, 1.2, 1.3, 1.4, ABU-2, PROP-4 | `test_req_1_*`, `test_abu_2_*` (backend: 178 passaram, 12 ignorados); no navegador local, o login do dono funcionou pelo fluxo real de CSRF e sessão | ✔ em teste e no navegador local; **não visto o login do dono no ar** |
| REQ-2.1 a 2.4, PROP-2 | `test_req_2_*`, `test_prop_2_*` (threads reais); no navegador local, o dono criou o grupo | ✔ em teste e no navegador local |
| REQ-3.1 a 3.7, ABU-3, PROP-3 | `test_req_3_*`, `test_abu_3_*`; no navegador local, o convite foi gerado (link com código no fragmento e validade de 7 dias) | ✔ em teste; **aceite do convite não visto no navegador nem no ar** |
| REQ-4.1 a 4.9, PROP-1 | `test_req_4_*`, `test_prop_1_*`; no navegador local, o perfil incompleto levou à tela de perfil e a cor sugerida foi gravada | ✔ |
| REQ-5.1 a 5.5 | 40 testes de widget (`entrar`, `convite`, `perfil`, `grupo`) e 7 do cliente HTTP, todos verdes; `flutter analyze` sem aviso | ✔ em teste; telas de entrar, perfil e grupo vistas no navegador local; **tela de criar conta pelo convite não vista no navegador** |
| NFR-SEC-1, 2, 3 | `test_nfr_sec_*`; cookies com `HttpOnly` vistos nos cabeçalhos da pilha local | ✔ |
| NFR-A11Y-1 | `acessibilidade_test.dart`: guias de contraste de texto e de alvo de toque nas telas, nos dois temas | ✔ em teste automatizado; **sem relatório de leitor de tela nem auditoria manual** |
| NFR-RESP-1 | testes de 360 e 1280 px sem estouro; no navegador local, 360 px (claro) e 1280 px (escuro) conferidos na tela de grupo | ✔ parcial: **nem todas as telas nos dois temas e larguras** |
| ABU-1, CTL-11 | `test_abu_1_*` (texto do compose); no ar, em 2026-11-05: 8 `POST` a `/auth/entrar` do mesmo endereço, os 5 primeiros passaram pelo limite (resposta 403 do CSRF, porque o pedido não levava o token) e do 6º ao 8º vieram 429 | ✔ no ar, de **um único endereço de origem**; o limite foi medido sem credenciais reais |
| ABU-4 | `test_abu_4_*` | ✔ em teste |
| CTL-19 | `test_ctl_19_*`; no ar, o cabeçalho `Content-Security-Policy` veio como no arquivo do nginx | ✔ |
| CTL-20 | `test_ctl_20_*` (SDK com SHA-256, pacotes só os do ADR-0005); build da imagem no CI | ✔ |
| Rotas no ar | `/entrelinhas/` 200, `/entrelinhas` 301, `/entrelinhas/api/v1/auth/csrf` 200, `/entrelinhas/admin/login/` 200 | ✔ |

## Correções do CI e do deploy (honestidade)
O primeiro push falhou no CI por dois motivos reais, corrigidos em seguida: formatação do `ruff` num teste (`c8e6cb3`) e o `flutter` rodando como `root` no runner
(permissão no `.dart_tool`, depois "dubious ownership" do git; `ca2a7c8` acrescenta `safe.directory` ao nível do sistema na imagem do SDK, reproduzido e verificado localmente
antes do push). Depois disso o usuário informou CI e deploy verdes.

## Não provado
- Aceite do convite pela segunda pessoa, no navegador e no ar.
- Login do dono no ar e o perfil do dono preenchido no ar (o `ADMIN_EMAIL` foi confirmado implicitamente pelo deploy verde, não por entrada real).
- O que o relatório de acessibilidade de um leitor de tela diria.
- Segurança por auditoria independente (ainda não feita para a 003).

## Veredito
**Parcial.** Backend e front estão completos e testados e a publicação está no ar; faltam as provas "no ar" do fluxo completo com as duas pessoas e a verificação independente (T-5.2).
