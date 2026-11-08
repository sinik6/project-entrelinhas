---
id: 007-destaques-backend
status: em-revisao
---

# Tarefas — Destaques e comentários (backend)

Legenda: `[P]` paralelizável · teste antes da implementação · cada tarefa com `Req:` e `Verifica:` · tamanho XS/S/M/L.
Estratégia de fatiamento: risco primeiro (posição contra o texto visível e a sonda), depois limites e autoria, depois leitura.
Os testes levam `[007]` na docstring. Depende da 005 no ar.

## Onda 1 — Testes primeiro (devem falhar)
- [x] T-1.1 Testes de criação e posição: texto visível em `full` e `partial`, tipos, limites, sem texto visível (409), sonda do parceiro, PROP-9 (L)
  - Req: REQ-13.1, REQ-13.2, REQ-13.3, REQ-13.4, ABU-14, PROP-9, CTL-51
  - Arquivos: `backend/apps/destaques/tests/test_destaque.py`
  - Verifica: `uv run pytest apps/destaques/tests/test_destaque.py` → vermelho
- [x] T-1.2 [P] Testes de limites e autoria: 50 destaques e 20 comentários (threads reais), apagar, editar, 403 (L)
  - Req: REQ-13.5, REQ-13.6, REQ-13.7, REQ-14.1, REQ-14.2, REQ-14.3, REQ-14.4, ABU-15, ABU-16, CTL-53, CTL-54
  - Arquivos: `backend/apps/destaques/tests/test_comentario.py`
  - Verifica: vermelho
- [x] T-1.3 [P] Testes de leitura, isolamento por grupo e de código (log, Admin) (M)
  - Req: REQ-14.5, REQ-14.6, REQ-14.7, NFR-DEST-1, NFR-DEST-2, CTL-52, CTL-55
  - Arquivos: `backend/apps/destaques/tests/test_leitura.py`
  - Verifica: vermelho

## Onda 2 — Implementação
- [x] T-2.1 Na 005: expor `texto_visivel_para(registro, usuario)` (sem abrir segunda porta ao texto) e anotar em ADR-0009 que os offsets do destaque são do texto visível (XS)
  - Req: REQ-13.2, CTL-56
  - Arquivos: `backend/apps/registros/domain.py`, `specs/changes/005-registros-backend/adr/ADR-0009-*.md`
  - Verifica: testes da 005 continuam verdes
- [x] T-2.2 App `destaques`: modelos, restrições, migração reversível (S)
  - Req: REQ-13.1, REQ-14.1
  - Arquivos: `backend/apps/destaques/{models}.py`, `backend/apps/destaques/migrations/`
  - Verifica: `makemigrations --check`; `migrate zero`
  - Depende: T-1.1
- [x] T-2.3 Criação e validação de posição contra o texto visível; mensagens sem o tamanho total (M)
  - Req: REQ-13.1 a REQ-13.4, ABU-14, PROP-9
  - Arquivos: `backend/apps/destaques/{services,serializers,views,urls}.py`, `backend/config/api_v1.py`
  - Verifica: `test_destaque.py` verde
  - Depende: T-2.1, T-2.2
- [x] T-2.4 Limites com trava, apagar, comentar, editar, autoria (M)
  - Req: REQ-13.5 a REQ-13.7, REQ-14.1 a REQ-14.4, ABU-15, ABU-16
  - Arquivos: `backend/apps/destaques/{services,views}.py`
  - Verifica: `test_comentario.py` verde
  - Depende: T-1.2, T-2.3
- [x] T-2.5 Leitura por registro, isolamento, log e Admin sem destaques (S)
  - Req: REQ-14.5, REQ-14.6, REQ-14.7, NFR-DEST-2
  - Arquivos: `backend/apps/destaques/{views,admin}.py`
  - Verifica: `test_leitura.py` verde
  - Depende: T-1.3, T-2.3
- [x] T-2.6 Mutação: validar contra texto integral, tamanho total na mensagem, autoria trocada; todos mortos (S)
  - Req: ABU-14, ABU-16, PROP-9
  - Verifica: 3 de 3 mutantes mortos, registrados no `validation.md`
  - Depende: T-2.5
- [x] T-2.7 OpenAPI da 007 e teste de contrato (S)
  - Req: NFR-DEST-1
  - Arquivos: `specs/changes/007-destaques-backend/contracts/openapi.yaml`, `backend/tests/test_contrato.py`
  - Verifica: o teste compara rotas e códigos com o contrato; a linha `x-estado: planejado` sai do contrato
  - Depende: T-2.5

## Onda 3 — Publicação e fechamento
- [ ] T-3.1 Deploy (o dono manda "Commit e push") e conferência no ar: destacar em `full` e `partial`, comentar como o outro, 403, 409 em `private` (M)
  - Req: REQ-13.1, REQ-14.1, REQ-13.3
  - Verifica: evidência no `validation.md`
- [ ] T-3.2 Rastreabilidade, `sdd_lint`, auditoria independente por subagente, `validation.md`, arquivamento em `destaques.md` (M)
  - Req: PROP-9, ABU-14
  - Verifica: lint sem erro; auditoria sem achado grave aberto
