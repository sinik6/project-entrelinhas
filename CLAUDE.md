# Entrelinhas — orientação do projeto

Diário compartilhado por exatamente duas pessoas (PWA): escrita diária, fotos de textos
manuscritos, visibilidade por entrega (`full` / `private` / `partial`) e destaques com comentários
estilo Kindle. Texto original da spec: `docs/especificacao-origem.md`.

Monorepo: `backend/` (Django 5.2 + DRF + PostgreSQL, uv) e, a partir da T0304, `frontend/`
(Next.js + TypeScript, mesmo padrão do Vinculus: BFF em `app/api/[...path]`, `basePath` `/entrelinhas`).
Docs: `docs/` vale para o sistema todo (constituição, regras por domínio em `docs/dominio/`, ADRs,
specs, roadmap); `backend/docs/` guarda o "como é feito" do backend.

- Ler `docs/constitution.md`, `docs/dominio/` e `backend/docs/architecture.md` antes de mudar código.
- Toda mudança tem spec em `docs/specs/NNN-nome/` (spec → plan → tasks → validation), critérios `NNN-Cn`
  citados nos testes. Uma tarefa pequena por vez, na ordem de `docs/roadmap.md`. Sem expansão de escopo.
- **Privacidade no servidor:** texto `private` ou fora do trecho `partial` nunca sai na resposta HTTP;
  todo endpoint que devolve texto tem teste de API provando isso (ADR-002).
- Toda validação existe no backend (serializer/service, 422 com teste de API); o front só repete a regra.
- Backend: comandos dentro de `backend/` com uv; nunca pip global. Um app por domínio em `backend/apps/`;
  camadas: models · services · serializers · views · urls · tests. Regra de negócio no service.
- Antes de concluir: comandos de `docs/tecnologia.md` (ruff, check, makemigrations --check, pytest em PostgreSQL real).
- Português em domínio, docstrings, comentários e docs.
- Commits: Conventional Commits, autor exclusivo `jpjamal <jpfisica3@gmail.com>`, sem coautores nem atribuição de IA.
- Commits direto na `main`, sempre `git fetch` antes. Só commitar/push quando o dono mandar (push dispara o deploy).
- Segredos fora do Git. Produção exige `DJANGO_SECRET_KEY` e `POSTGRES_PASSWORD`.
- Produção: https://jpsys.duckdns.org/entrelinhas, VPS compartilhada atrás do Traefik central (repo
  `traefikproxy`). Push na `main` → CI → `Deploy Entrelinhas` (ambiente `production`) → `infra/deploy.sh`.
  Serviços na rede `traefik_proxy` têm nome único (`entrelinhas-api`, `entrelinhas-web`). Ver ADR-003.

## Fronteiras

| Sempre | Perguntar antes | Nunca |
|---|---|---|
| ler constituição e domínio | migração que altera ou apaga dados | commitar segredo ou `.env` |
| teste de que texto escondido não vaza | dependência nova (ADR) | coautor ou atribuição de IA no commit |
| atualizar a spec antes do código | commit/push na `main`; mexer em deploy, Traefik, segredos | validar só na tela |
| registrar suposições na spec | mudar visibilidade ou o limite de 2 membros | enviar texto `private`/fora do `partial` |

## Ambiente local (Windows)
Ver `docs/tecnologia.md`: `UV_PYTHON_INSTALL_DIR`, venv fora do repo, portas 5432/8000 ocupadas (API em 8010),
Postgres descartável em porta própria para os testes.
