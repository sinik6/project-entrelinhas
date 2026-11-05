---
id: 004-fotos
status: em-revisao
---

# Tarefas — Fotos privadas (manuscrito e perfil)

Legenda: `[P]` paralelizável · teste antes da implementação · cada tarefa com `Req:` e `Verifica:` · tamanho XS/S/M/L.
Estratégia de fatiamento: risco primeiro (recebimento seguro do arquivo e autorização), depois infra e por fim o front.
Os testes levam `[004]` na docstring.

## Onda 1 — Backend: testes primeiro (devem falhar)
- [x] T-1.1 Testes do envio e da recodificação: tipos, conteúdo falso, limites, EXIF descartado, nome por UUID, propriedade de corretude (M)
  - Req: REQ-6.1, REQ-6.2, REQ-6.3, REQ-6.4, ABU-5, PROP-5, NFR-FOTO-4, CTL-21
  - Arquivos: `backend/apps/fotos/tests/test_envio.py`
  - Verifica: `uv run pytest apps/fotos/tests/test_envio.py` → vermelho
- [x] T-1.2 [P] Testes de entrega, autorização e remoção: cabeçalhos, 404 cruzado, apagar avulsa, 409 anexada, `limpar_fotos`, cota (M)
  - Req: REQ-6.5, REQ-6.6, REQ-6.7, REQ-6.8, REQ-6.9, ABU-6, ABU-7, CTL-23, CTL-24
  - Arquivos: `backend/apps/fotos/tests/test_entrega.py`
  - Verifica: `uv run pytest apps/fotos/tests/test_entrega.py` → vermelho
- [x] T-1.3 [P] Testes da foto de perfil: definir, trocar, remover, regra de quem vê, grupo sem e-mail (M)
  - Req: REQ-7.1, REQ-7.2, REQ-7.3, REQ-7.4, REQ-7.5
  - Arquivos: `backend/apps/fotos/tests/test_perfil_foto.py`
  - Verifica: `uv run pytest apps/fotos/tests/test_perfil_foto.py` → vermelho

## Onda 2 — Backend: implementação
- [x] T-2.1 ADR-0007 e dependência Pillow (verificada no PyPI, versão travada no `uv.lock`) (XS)
  - Req: CTL-21
  - Arquivos: `specs/changes/004-fotos/adr/ADR-0007-*.md`, `backend/pyproject.toml`, `backend/uv.lock`
  - Verifica: `uv sync --frozen` limpo; ADR aceito pelo dono
- [x] T-2.2 App `fotos`: modelo `Foto`, migração, `Perfil.foto`, serviço de validação e recodificação (`Image.MAX_IMAGE_PIXELS`) (M)
  - Req: REQ-6.1 a 6.4, PROP-5, ABU-5, CTL-21
  - Arquivos: `backend/apps/fotos/{models,servicos}.py`, `backend/apps/fotos/migrations/`, `backend/apps/acesso/models.py`
  - Verifica: `test_envio.py` verde; `makemigrations --check`; `migrate zero` reversível
  - Depende: T-1.1, T-2.1
- [x] T-2.3 Views e rotas: enviar, entregar o arquivo com cabeçalhos fixos, apagar, cota, 404 por objeto (M)
  - Req: REQ-6.5 a 6.8, ABU-6, ABU-7
  - Arquivos: `backend/apps/fotos/{views,urls,serializers}.py`, `backend/config/api_v1.py`
  - Verifica: `test_entrega.py` verde
  - Depende: T-1.2, T-2.2
- [x] T-2.4 Perfil: `PUT/DELETE /perfil/foto`, `foto_url` em perfil e grupo, apagar a foto anterior (S)
  - Req: REQ-7.1 a 7.5
  - Arquivos: `backend/apps/acesso/{views,serializers,urls}.py`
  - Verifica: `test_perfil_foto.py` verde; testes da 003 continuam verdes
  - Depende: T-1.3, T-2.2
- [x] T-2.5 Comando `limpar_fotos` (S)
  - Req: REQ-6.9
  - Arquivos: `backend/apps/fotos/management/commands/limpar_fotos.py`
  - Verifica: teste do REQ-6.9 verde
  - Depende: T-2.2
- [x] T-2.6 OpenAPI da 004 e teste de contrato (S)
  - Req: NFR-FOTO-4
  - Arquivos: `specs/changes/004-fotos/contracts/openapi.yaml`, `backend/tests/test_contrato.py`
  - Verifica: o teste compara rotas e códigos com o contrato; a linha `x-estado: planejado` sai do contrato
  - Depende: T-2.3, T-2.4

## Onda 3 — Infra e front
- [x] T-3.1 [P] Testes de contrato da infra: volume `fotos_data`, limite de 9 MB só na rota de fotos, backup do volume, `limpar_fotos` no deploy (S)
  - Req: NFR-FOTO-1, NFR-FOTO-2, CTL-21, CTL-22
  - Arquivos: `backend/tests/test_infra_fotos.py`
  - Verifica: vermelho
- [x] T-3.2 Infra: volume e `FOTOS_DIR` no compose de produção e de dev, `location` no nginx, backup e limpeza no `deploy.sh` (M)
  - Req: NFR-FOTO-1, NFR-FOTO-2, CTL-25
  - Arquivos: `docker-compose.deploy.yml`, `compose.yml`, `infra/nginx/entrelinhas.conf.template`, `infra/deploy.sh`
  - Verifica: `test_infra_fotos.py` verde; `docker compose config`
  - Depende: T-3.1
- [x] T-3.3 Testes de widget da foto de perfil e ADR-0008 (`image_picker`) (M)
  - Req: REQ-7.6, REQ-7.7, REQ-7.8, NFR-FOTO-3
  - Arquivos: `frontend/test/foto_perfil_test.dart`, `specs/changes/004-fotos/adr/ADR-0008-*.md`
  - Verifica: vermelho
- [x] T-3.4 Front: seletor de foto, prévia, envio, remoção, inicial sobre a cor como alternativa (M)
  - Req: REQ-7.6, REQ-7.7, REQ-7.8
  - Arquivos: `frontend/lib/features/perfil/`, `frontend/lib/shared/api/`, `frontend/lib/shared/ui/avatar.dart`, `frontend/pubspec.yaml`
  - Verifica: `flutter analyze` e `flutter test` verdes
  - Depende: T-3.3, T-2.4
- [ ] T-3.5 (feito em parte: ver validation.md) Teste no navegador, em contêiner: enviar, trocar e remover foto; a foto aparece para a outra pessoa; o cookie vai na imagem; 360 e 1280 px (M)
  - Req: REQ-7.4, REQ-7.6, NFR-FOTO-3
  - Verifica: roteiro verde; evidência no `validation.md`
  - Depende: T-3.4, T-3.2

## Onda 4 — Publicação e fechamento
- [ ] T-4.1 Deploy (o dono manda "Commit e push"); conferir no ar o envio, a entrega com cabeçalhos e o 404 sem sessão (S)
  - Req: CTL-21, CTL-23
  - Verifica: evidência no `validation.md`
- [ ] T-4.2 Rastreabilidade, `sdd_lint`, auditoria independente por subagente, `validation.md` e arquivamento na spec viva `fotos.md` (M)
  - Req: PROP-5, CTL-23
  - Verifica: lint sem erro; auditoria sem achado grave aberto
