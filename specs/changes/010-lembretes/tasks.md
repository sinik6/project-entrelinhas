---
id: 010-lembretes
status: em-revisao
---

# Tarefas — Lembretes (PWA e Web Push)

Legenda: `[P]` paralelizável · teste antes da implementação · cada tarefa com `Req:` e `Verifica:` · tamanho XS/S/M/L.
Estratégia de fatiamento: a regra de quem recebe e a defesa contra SSRF primeiro (backend), depois o disparador, a infra e por fim o front e o PWA.
Os testes levam `[010]` na docstring ou no nome. Depende da 005 (quem entregou) e do app da 003 no ar.

## Onda 1 — Backend: testes primeiro (devem falhar)
- [x] T-1.1 Testes das assinaturas: guardar, repetir, trocar de dono, lista de serviços, IPs e hosts internos, `http`, chaves inválidas, 5 por pessoa, remover, 404 de outra pessoa (L)
  - Req: REQ-18.3, REQ-18.4, REQ-18.5, REQ-18.6, ABU-21, ABU-22, NFR-LEMB-5, CTL-81, CTL-82
  - Arquivos: `backend/apps/lembretes/tests/test_assinaturas.py`
  - Verifica: `uv run pytest apps/lembretes/tests/test_assinaturas.py` → vermelho
- [x] T-1.2 [P] Testes do disparador com relógio e envio injetados: 21h30, quem já entregou, uma vez por dia, 404/410, janela até 23h00, falha sem repetir, texto genérico, oráculo (PROP-13) (L)
  - Req: REQ-19.1, REQ-19.2, REQ-19.3, REQ-19.4, REQ-19.5, REQ-19.6, REQ-19.8, PROP-13, CTL-85, CTL-86
  - Arquivos: `backend/apps/lembretes/tests/test_disparador.py`
  - Verifica: vermelho
- [x] T-1.3 [P] Testes de concorrência do disparador (duas execuções ao mesmo tempo, reinício no meio) e do segredo (chave privada fora de resposta e de log) (M)
  - Req: ABU-23, REQ-19.3, NFR-LEMB-1, CTL-86
  - Arquivos: `backend/apps/lembretes/tests/test_concorrencia.py`, `backend/apps/lembretes/tests/test_segredo.py`
  - Verifica: vermelho

## Onda 2 — Backend: implementação
- [x] T-2.1 ADR-0012 aceito; dependência `pywebpush` (verificada no PyPI, versão travada no `uv.lock`) (XS)
  - Req: CTL-88
  - Arquivos: `specs/changes/010-lembretes/adr/ADR-0012-*.md`, `backend/pyproject.toml`, `backend/uv.lock`
  - Verifica: `uv sync --frozen` limpo
- [x] T-2.2 App `lembretes`: modelos, migração reversível, validação do endpoint (lista de serviços, HTTPS, sem IP) e rotas de assinatura (M)
  - Req: REQ-18.3 a REQ-18.6, ABU-21, ABU-22
  - Arquivos: `backend/apps/lembretes/{models,validacao,serializers,views,urls}.py`, `backend/config/api_v1.py`
  - Verifica: `test_assinaturas.py` verde; `migrate zero`
  - Depende: T-1.1, T-2.1
- [x] T-2.3 Disparador: função `enviar_lembretes(agora, enviar)`, comando `enviar_lembretes`, laço `rodar_lembretes`, `gerar_vapid`, saúde por batimento (L)
  - Req: REQ-19.1 a REQ-19.6, REQ-19.8, ABU-23, PROP-13, NFR-LEMB-3
  - Arquivos: `backend/apps/lembretes/{disparador,envio}.py`, `backend/apps/lembretes/management/commands/`
  - Verifica: `test_disparador.py` e `test_concorrencia.py` verdes
  - Depende: T-1.2, T-1.3, T-2.2
- [x] T-2.4 OpenAPI da 010 e teste de contrato (S)
  - Req: NFR-LEMB-5
  - Arquivos: `specs/changes/010-lembretes/contracts/openapi.yaml`, `backend/tests/test_contrato.py`
  - Verifica: o teste compara rotas e códigos com o contrato; a linha `x-estado: planejado` sai do contrato
  - Depende: T-2.2

## Onda 3 — Infra
- [x] T-3.1 [P] Testes de contrato da infra: serviço sem porta e sem rótulos do Traefik, `restart`, `healthcheck`, variáveis VAPID exigidas no compose e no `deploy.sh`, `Service-Worker-Allowed` e `no-cache` do `sw.js` no nginx (S)
  - Req: NFR-LEMB-1, NFR-LEMB-2, NFR-LEMB-3, CTL-83, CTL-84, CTL-87
  - Arquivos: `backend/tests/test_infra_lembretes.py`
  - Verifica: vermelho
- [x] T-3.2 Infra: serviço `entrelinhas-lembretes`, variáveis e conferência das chaves no `deploy.sh`, cabeçalhos do `sw.js`, `compose.yml` de desenvolvimento (M)
  - Req: NFR-LEMB-1, NFR-LEMB-3
  - Arquivos: `docker-compose.deploy.yml`, `compose.yml`, `infra/deploy.sh`, `infra/nginx/entrelinhas.conf.template`, `.github/workflows/deploy.yml` (exporta os segredos)
  - Verifica: `test_infra_lembretes.py` verde; `docker compose config`
  - Depende: T-3.1

## Onda 4 — Front e PWA
- [x] T-4.1 Testes do front: seção de lembrete com `PushApi` falsa (ligar, desligar, negada, sem suporte, iPhone), manifesto completo, `sw.js` em Node (push e toque, sem cache) (L)
  - Req: REQ-18.1, REQ-18.2, REQ-18.6, REQ-18.7, REQ-18.8, REQ-19.7, NFR-LEMB-2, NFR-LEMB-4
  - Arquivos: `frontend/test/lembrete_test.dart`, `frontend/test/manifesto_test.dart`, `frontend/web/test/sw.test.mjs`
  - Verifica: vermelho
- [x] T-4.2 PWA: manifesto completo, ícones próprios (192, 512, máscara), `sw.js` só de push, registro do service worker (M)
  - Req: REQ-18.1, REQ-19.7, NFR-LEMB-2
  - Arquivos: `frontend/web/manifest.json`, `frontend/web/icons/`, `frontend/web/sw.js`, `frontend/web/index.html`
  - Verifica: `manifesto_test.dart` e o teste do `sw.js` verdes
  - Depende: T-4.1
- [x] T-4.3 Front: `PushApi` (interop com `dart:js_interop`), seção de lembrete em Perfil com os estados e as instruções do iPhone (L)
  - Req: REQ-18.2, REQ-18.6, REQ-18.7, REQ-18.8, NFR-LEMB-4
  - Arquivos: `frontend/lib/features/lembretes/`, `frontend/lib/features/perfil/`
  - Verifica: `lembrete_test.dart` verde; `flutter analyze` limpo
  - Depende: T-2.2, T-4.1

## Onda 5 — Publicação e fechamento
- [ ] T-5.1 (do usuário) Gerar as chaves com `manage.py gerar_vapid` e criar no GitHub, ambiente `production`, os segredos `VAPID_PRIVATE_KEY`, `VAPID_PUBLIC_KEY` e `VAPID_ASSUNTO` (um `mailto:`); a chave privada nunca vai ao chat (XS)
  - Req: NFR-LEMB-1, CTL-83
  - Verifica: o deploy passa na conferência das chaves
- [ ] T-5.2 Deploy (o dono manda "Commit e push") e conferência no ar: instalar o app no Android e no iPhone, ligar o lembrete, receber o aviso às 21h30, não receber depois de entregar, tocar abre Hoje (M)
  - Req: REQ-19.1, REQ-19.2, REQ-19.7
  - Verifica: evidência no `validation.md` (inclui o que não pôde ser provado)
  - Depende: T-3.2, T-4.3, T-5.1
- [ ] T-5.3 Rastreabilidade, `sdd_lint`, auditoria independente por subagente (foco: SSRF, segredo, duplicidade), `validation.md`, arquivamento em `lembretes.md` (M)
  - Req: PROP-13, ABU-21, ABU-23
  - Verifica: lint sem erro; auditoria sem achado grave aberto
