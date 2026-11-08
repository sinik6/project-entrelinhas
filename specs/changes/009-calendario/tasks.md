---
id: 009-calendario
status: em-revisao
---

# Tarefas — Calendário (backend e telas)

Legenda: `[P]` paralelizável · teste antes da implementação · cada tarefa com `Req:` e `Verifica:` · tamanho XS/S/M/L.
Estratégia de fatiamento: a regra de dia e de "juntos" primeiro (função pura com oráculo), depois a rota, depois a tela.
Os testes levam `[009]` na docstring ou no nome. Depende da 005 no ar.

## Onda 1 — Testes primeiro (devem falhar)
- [x] T-1.1 Testes da função de estados: escreveu, falhou, pendente, fora, `private` conta, juntos (7199, 7200, 7201 s), virada de dia, oráculo e simetria (L)
  - Req: REQ-16.2, REQ-16.3, REQ-16.4, REQ-16.5, REQ-16.9, ABU-20, PROP-11, PROP-12, CTL-73
  - Arquivos: `backend/apps/calendario/tests/test_estados.py`
  - Verifica: `uv run pytest apps/calendario/tests/test_estados.py` → vermelho
- [x] T-1.2 [P] Testes da rota: forma, sem horários e sem texto, mês inválido ou futuro ou antes da entrada, sem grupo, outro grupo, consultas (M)
  - Req: REQ-16.1, REQ-16.6, REQ-16.7, REQ-16.8, ABU-19, NFR-CAL-2, NFR-CAL-3, CTL-71, CTL-72, CTL-74
  - Arquivos: `backend/apps/calendario/tests/test_rota.py`
  - Verifica: vermelho
- [x] T-1.3 [P] Testes da migração de `entrou_em` e do preenchimento na entrada no grupo (S)
  - Req: REQ-16.3
  - Arquivos: `backend/apps/acesso/tests/test_entrou_em.py`
  - Verifica: vermelho
- [x] T-1.4 [P] Testes de widget do calendário: grade, marcadores, formas, rótulos, legenda, navegação limitada, lista do dia, erros, acessibilidade (L)
  - Req: REQ-17.1, REQ-17.2, REQ-17.3, REQ-17.4, REQ-17.5, REQ-17.6, NFR-CAL-1
  - Arquivos: `frontend/test/calendario_test.dart`, `frontend/test/calendario_a11y_test.dart`
  - Verifica: vermelho

## Onda 2 — Implementação
- [x] T-2.1 `Perfil.entrou_em`: migração com preenchimento das contas existentes e gravação na criação do grupo e ao aceitar convite (S)
  - Req: REQ-16.3
  - Arquivos: `backend/apps/acesso/{models,services}.py`, `backend/apps/acesso/migrations/`
  - Verifica: `test_entrou_em.py` verde; testes da 003 continuam verdes; `migrate zero` reversível
  - Depende: T-1.3
- [x] T-2.2 Função pura `estado_do_mes` em `domain.py` (M)
  - Req: REQ-16.2 a 16.5, REQ-16.9, PROP-11, PROP-12, ABU-20
  - Arquivos: `backend/apps/calendario/domain.py`
  - Verifica: `test_estados.py` verde
  - Depende: T-1.1
- [x] T-2.3 View `GET /calendario`, validação do mês, resposta mínima (M)
  - Req: REQ-16.1, REQ-16.6, REQ-16.7, REQ-16.8, ABU-19, NFR-CAL-3
  - Arquivos: `backend/apps/calendario/{views,urls}.py`, `backend/config/api_v1.py`
  - Verifica: `test_rota.py` verde
  - Depende: T-1.2, T-2.1, T-2.2
- [x] T-2.4 OpenAPI da 009 e teste de contrato (S)
  - Req: NFR-CAL-2
  - Arquivos: `specs/changes/009-calendario/contracts/openapi.yaml`, `backend/tests/test_contrato.py`
  - Verifica: o teste compara rotas e códigos com o contrato; a linha `x-estado: planejado` sai do contrato
  - Depende: T-2.3
- [x] T-2.5 Front: cliente e modelos, grade do mês, marcadores com forma e rótulo, legenda, folha do dia, 5ª aba (L)
  - Req: REQ-17.1 a REQ-17.6, NFR-CAL-1
  - Arquivos: `frontend/lib/features/calendario/`, `frontend/lib/shared/api/`, `frontend/lib/app/`
  - Verifica: `calendario_test.dart` e `calendario_a11y_test.dart` verdes; testes anteriores verdes; `flutter analyze` limpo
  - Depende: T-1.4, T-2.3

## Onda 3 — Navegador e fechamento
- [ ] T-3.1 Teste no navegador, em contêiner, com dois participantes e registros em horários diferentes: conferir os estados, o selo "juntos" e a lista do dia; 360 e 1280 px, claro e escuro (M)
  - Req: REQ-17.2, REQ-17.4, NFR-CAL-1
  - Verifica: roteiro verde; evidência no `validation.md`
  - Depende: T-2.5
- [ ] T-3.2 Deploy (o dono manda "Commit e push") e conferência no ar (S)
  - Req: REQ-17.2, REQ-17.4
  - Verifica: evidência no `validation.md`
- [ ] T-3.3 Rastreabilidade, `sdd_lint`, auditoria independente por subagente, `validation.md`, arquivamento em `calendario.md` (M)
  - Req: PROP-11, PROP-12
  - Verifica: lint sem erro; auditoria sem achado grave aberto
