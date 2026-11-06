---
id: 006-registros-front
status: em-revisao
---

# Tarefas — Registros diários (telas)

Legenda: `[P]` paralelizável · teste antes da implementação · cada tarefa com `Req:` e `Verifica:` · tamanho XS/S/M/L.
Estratégia de fatiamento: o que mais pode dar errado primeiro (conversão do trecho), depois escrever, depois ler.
Os testes levam `[006]` no nome. Depende da 005 no ar. Comandos Flutter: no contêiner do SDK (ver `specs/steering/tech.md`).

## Onda 1 — Testes primeiro (devem falhar)
- [x] T-1.1 Testes da conversão UTF-16 ↔ pontos de código e do ajuste a grafemas (PROP-8): emoji, acento composto, bandeira, quebra de linha (S)
  - Req: REQ-11.4, PROP-8, CTL-42
  - Arquivos: `frontend/test/texto_test.dart`
  - Verifica: `flutter test test/texto_test.dart` → vermelho
- [x] T-1.2 [P] Testes de widget da tela Hoje: campos, botão desabilitado com o que falta, confirmação, envio em ordem, erro de foto com retomada, dia já entregue, duplo toque (L)
  - Req: REQ-11.1, REQ-11.2, REQ-11.5, REQ-11.6, REQ-11.7, REQ-11.8, ABU-12, CTL-44
  - Arquivos: `frontend/test/hoje_test.dart`, `frontend/test/duplo_toque_test.dart`, `frontend/test/suporte/api_falsa.dart`
  - Verifica: vermelho
- [x] T-1.3 [P] Testes do trecho: seleção, "Usar a seleção", prévia exata, trecho enviado em pontos de código (M)
  - Req: REQ-11.3, REQ-11.4, PROP-8, CTL-42
  - Arquivos: `frontend/test/trecho_test.dart`
  - Verifica: vermelho
- [x] T-1.4 [P] Testes do Diário e do registro: mês, navegação, três visões, nota do trecho, aviso de privado, foto em tela cheia, vazio, erro, texto com marcação literal (L)
  - Req: REQ-12.1, REQ-12.2, REQ-12.3, REQ-12.4, REQ-12.5, REQ-12.6, REQ-12.7, ABU-13, NFR-TELA-2, CTL-43
  - Arquivos: `frontend/test/diario_test.dart`
  - Verifica: vermelho
- [x] T-1.5 [P] Testes de não persistência e de acessibilidade das telas novas (S)
  - Req: REQ-11.9, NFR-TELA-1, NFR-TELA-3, CTL-41
  - Arquivos: `frontend/test/sem_persistencia_test.dart`, `frontend/test/acessibilidade_test.dart`
  - Verifica: vermelho

## Onda 2 — Implementação
- [x] T-2.1 ADR-0011 e dependência `characters` (versão do SDK, em `pubspec.yaml` e `pubspec.lock`); ajustar o teste de pacotes permitidos (XS)
  - Req: REQ-11.4
  - Arquivos: `specs/changes/006-registros-front/adr/ADR-0011-*.md`, `frontend/pubspec.yaml`, `backend/tests/test_infra_web.py`
  - Verifica: `pub get` limpo; o teste de pacotes lista exatamente os do ADR-0005, 0008 e 0011
- [x] T-2.2 `shared/texto.dart`: conversão e grafemas (S)
  - Req: REQ-11.4, PROP-8
  - Arquivos: `frontend/lib/shared/texto.dart`
  - Verifica: `texto_test.dart` verde
  - Depende: T-1.1, T-2.1
- [x] T-2.3 Cliente da API e modelos: `entregarRegistro`, `listarRegistros`, `lerRegistro`, `enviarFoto`; modelos das duas visões (M)
  - Req: REQ-11.6, REQ-12.1
  - Arquivos: `frontend/lib/shared/api/`, `frontend/lib/features/hoje/modelos.dart`
  - Verifica: testes do cliente HTTP verdes (estende `api_http_test.dart`)
  - Depende: T-1.2
- [x] T-2.4 Tela Hoje: rascunho em memória, fotos, visibilidade, trecho com prévia, confirmação, envio em ordem e retomada (L)
  - Req: REQ-11.1 a REQ-11.9, ABU-12
  - Arquivos: `frontend/lib/features/hoje/`
  - Verifica: `hoje_test.dart`, `trecho_test.dart`, `duplo_toque_test.dart`, `sem_persistencia_test.dart` verdes
  - Depende: T-1.2, T-1.3, T-2.2, T-2.3
- [x] T-2.5 Telas Diário e Registro: lista por mês, cartões, visões, tela cheia com zoom (L)
  - Req: REQ-12.1 a REQ-12.7, ABU-13, NFR-TELA-2
  - Arquivos: `frontend/lib/features/diario/`
  - Verifica: `diario_test.dart` verde
  - Depende: T-1.4, T-2.3
- [x] T-2.6 Navegação (Hoje, Diário, Grupo, Perfil), redirecionamentos e acessibilidade das telas novas (M)
  - Req: NFR-TELA-1, NFR-TELA-3
  - Arquivos: `frontend/lib/app/`
  - Verifica: `acessibilidade_test.dart` e os testes da 003 verdes; `flutter analyze` limpo
  - Depende: T-2.4, T-2.5

## Onda 3 — Navegador e fechamento
- [x] T-3.1 Teste no navegador, na pilha local, com dois participantes: entregar `partial` (com emoji) — feito; `full` e `private` só em teste de widget; conferir a visão do parceiro; 360 e 1280 px, claro e escuro (M)
  - Req: REQ-11.3, REQ-12.3, NFR-TELA-1, CTL-45
  - Verifica: roteiro verde; evidência no `validation.md`
  - Depende: T-2.6
- [ ] T-3.2 Deploy (o dono manda "Commit e push") e conferência no ar (S)
  - Req: REQ-11.6, REQ-12.1
  - Verifica: evidência no `validation.md`
- [ ] T-3.3 Rastreabilidade, `sdd_lint`, auditoria independente por subagente, `validation.md`, arquivamento em `registros.md` (M)
  - Req: PROP-8, REQ-11.9
  - Verifica: lint sem erro; auditoria sem achado grave aberto
