---
id: 005-registros-backend
status: em-revisao
---

# Tarefas — Registros diários (backend)

Legenda: `[P]` paralelizável · teste antes da implementação · cada tarefa com `Req:` e `Verifica:` · tamanho XS/S/M/L.
Estratégia de fatiamento: risco primeiro (a função de visibilidade e a prova de que nada escondido vaza), depois entrega, leitura e lista.
Os testes levam `[005]` na docstring. Depende da 004 (fotos) em produção.

## Onda 1 — Testes primeiro (devem falhar)
- [ ] T-1.1 Testes da função `visivel_para` e das propriedades: PROP-6 (sem vazamento, marcadores únicos) e PROP-7 (fatia em pontos de código, com emoji e acentos) (M)
  - Req: REQ-9.2, REQ-9.3, REQ-9.4, PROP-6, PROP-7, NFR-REG-1, CTL-31
  - Arquivos: `backend/apps/registros/tests/test_visibilidade.py`
  - Verifica: `uv run pytest apps/registros/tests/test_visibilidade.py` → vermelho
- [ ] T-1.2 [P] Testes da entrega: fotos, texto, trecho, um por dia (threads reais), sem grupo, imutabilidade (L)
  - Req: REQ-8.1, REQ-8.2, REQ-8.3, REQ-8.4, REQ-8.5, REQ-8.6, REQ-8.7, ABU-9, ABU-11, NFR-REG-2, CTL-34, CTL-36, CTL-38
  - Arquivos: `backend/apps/registros/tests/test_entrega.py`
  - Verifica: vermelho
- [ ] T-1.3 [P] Testes de leitura por todas as rotas como autor e como parceiro; `private` e `partial` sem vazar em corpo, lista, foto e erro; outro grupo 404 (L)
  - Req: REQ-9.1, REQ-9.5, REQ-9.6, REQ-9.7, ABU-8, ABU-10, CTL-32, CTL-33, CTL-35
  - Arquivos: `backend/apps/registros/tests/test_leitura.py`
  - Verifica: vermelho
- [ ] T-1.4 [P] Testes da lista por mês: fuso de São Paulo na virada do dia, mês inválido ou futuro, sem grupo (M)
  - Req: REQ-10.1, REQ-10.2, REQ-10.3
  - Arquivos: `backend/apps/registros/tests/test_lista.py`
  - Verifica: vermelho
- [ ] T-1.5 [P] Testes de código: só `visivel_para` lê `.texto`; log sem texto; Admin sem registros (S)
  - Req: NFR-REG-1, NFR-REG-3, NFR-REG-4, CTL-37
  - Arquivos: `backend/apps/registros/tests/test_codigo.py`
  - Verifica: vermelho

## Onda 2 — Implementação
- [ ] T-2.1 ADR-0009 e ADR-0010 aceitos; modelo `Registro`, `Foto.registro` e `ordem`, restrições, migração reversível (M)
  - Req: REQ-8.4, REQ-8.5, ABU-9, CTL-39
  - Arquivos: `backend/apps/registros/models.py`, `backend/apps/registros/migrations/`, `backend/apps/fotos/models.py`, `backend/apps/fotos/migrations/`
  - Verifica: `makemigrations --check`; `migrate zero` reversível
  - Depende: T-1.2
- [ ] T-2.2 `domain.py` com `visivel_para`, o intervalo em pontos de código e as validações de texto e trecho (M)
  - Req: REQ-8.3, REQ-8.4, REQ-9.2, REQ-9.3, REQ-9.4, PROP-6, PROP-7, NFR-REG-1
  - Arquivos: `backend/apps/registros/domain.py`
  - Verifica: `test_visibilidade.py` verde
  - Depende: T-1.1
- [ ] T-2.3 Serviço `entregar` (transação: dia em SP, fotos, `IntegrityError` → 409) e view `POST /registros` (M)
  - Req: REQ-8.1, REQ-8.2, REQ-8.5, REQ-8.6, REQ-8.7, ABU-9, ABU-11
  - Arquivos: `backend/apps/registros/{services,views,serializers,urls}.py`, `backend/config/api_v1.py`
  - Verifica: `test_entrega.py` verde
  - Depende: T-2.1, T-2.2
- [ ] T-2.4 Views de leitura e lista, regra da foto para o parceiro na view de `fotos` (M)
  - Req: REQ-9.1, REQ-9.5, REQ-9.6, REQ-9.7, REQ-10.1, REQ-10.2, REQ-10.3, ABU-8, ABU-10
  - Arquivos: `backend/apps/registros/views.py`, `backend/apps/fotos/views.py`
  - Verifica: `test_leitura.py` e `test_lista.py` verdes; testes da 004 continuam verdes
  - Depende: T-2.3
- [ ] T-2.5 Log sem texto e Admin sem registros (XS)
  - Req: NFR-REG-3, NFR-REG-4
  - Arquivos: `backend/apps/registros/admin.py` (vazio de propósito), `backend/apps/registros/services.py`
  - Verifica: `test_codigo.py` verde
  - Depende: T-1.5
- [ ] T-2.6 Mutação da regra de visibilidade: um roteiro derruba cada mutante (trecho ignorado, foto no `partial`, `<` por `<=`, texto no `private`) (S)
  - Req: PROP-6, REQ-9.3, REQ-9.5
  - Arquivos: `backend/apps/registros/tests/mutacao.md` (resultado), roteiro no scratchpad
  - Verifica: 4 de 4 mutantes mortos, registrados no `validation.md`
  - Depende: T-2.4
- [ ] T-2.7 OpenAPI da 005 e teste de contrato (S)
  - Req: NFR-REG-2
  - Arquivos: `specs/changes/005-registros-backend/contracts/openapi.yaml`, `backend/tests/test_contrato.py`
  - Verifica: o teste compara rotas e códigos com o contrato; a linha `x-estado: planejado` sai do contrato
  - Depende: T-2.4

## Onda 3 — Publicação e fechamento
- [ ] T-3.1 Deploy (o dono manda "Commit e push"); conferir no ar: entregar, ler como parceiro `private` e `partial` sem vazamento, 405, 404 (M)
  - Req: REQ-8.1, REQ-9.3, REQ-9.4
  - Verifica: evidência no `validation.md`
- [ ] T-3.2 Rastreabilidade, `sdd_lint`, auditoria independente por subagente (foco: vazamento do texto escondido), `validation.md`, arquivamento em `registros.md` (M)
  - Req: PROP-6, REQ-9.7
  - Verifica: lint sem erro; auditoria sem achado grave aberto
