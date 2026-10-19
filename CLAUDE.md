# Entrelinhas — orientação do projeto

Diário compartilhado por exatamente duas pessoas (PWA): escrita diária, fotos de textos
manuscritos, visibilidade por entrega (`full` / `private` / `partial`) e destaques com comentários
estilo Kindle. Especificação de origem: `docs/especificacao-origem.md`.

Monorepo: `backend/` (Django 5.2 + DRF + PostgreSQL, uv) e, a partir da T0304, `frontend/`
(Next.js + TypeScript, mesmo padrão do Vinculus: BFF em `app/api/[...path]`, `basePath` `/entrelinhas`).

- Spec antes do código; uma tarefa pequena por vez, na ordem de `docs/roadmap.md`. Sem expansão de escopo.
- **Privacidade no servidor:** texto `private` ou fora do trecho `partial` nunca sai na resposta HTTP.
  Toda regra de visibilidade tem teste de API que prova que o texto escondido não aparece.
- Toda validação existe no backend (serializer/service, 422 com teste de API); o front só repete a regra.
- Backend: comandos dentro de `backend/` com uv (`pyproject.toml` + `uv.lock`); nunca pip global.
  Um app por domínio em `backend/apps/`; camadas: models · services · serializers · views · urls · tests.
- Antes de concluir: `ruff check`, `ruff format --check`, `manage.py check`, `makemigrations --check`, `pytest` (PostgreSQL real).
- Português em domínio, docstrings, comentários e docs.
- Commits: Conventional Commits, autor exclusivo `jpjamal <jpfisica3@gmail.com>`, sem coautores nem atribuição de IA.
- Commits direto na `main` (projeto pessoal), sempre `git fetch` antes. Só commitar/push quando o dono mandar.
- Segredos fora do Git. Produção exige `DJANGO_SECRET_KEY` e `POSTGRES_PASSWORD`.
- Produção: https://jpsys.duckdns.org/entrelinhas na VPS compartilhada, atrás do Traefik central
  (repo `traefikproxy`). Push na `main` → CI → workflow `Deploy Entrelinhas` (ambiente `production`)
  → `infra/deploy.sh`. Serviços na rede `traefik_proxy` têm nome único (`entrelinhas-api`, `entrelinhas-web`).

## Ambiente local (Windows)

- `UV_PYTHON_INSTALL_DIR=C:/Users/jpfis/.uvpython`; venv fora do repo (`UV_PROJECT_ENVIRONMENT`).
- Portas 5432 e 8000 costumam estar ocupadas: o `compose.yml` não publica o banco e sobe a API em 8010.
- Testes: Postgres descartável (`postgres:17-alpine`) em porta própria e `POSTGRES_HOST=127.0.0.1`.
