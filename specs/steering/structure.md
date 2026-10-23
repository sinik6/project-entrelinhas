# Estrutura — Entrelinhas

## Organização de pastas
```
project-entrelinhas/
├── AGENTS.md  CLAUDE.md          porta de entrada para agentes
├── specs/                        steering · capability-map · system · changes · archive · origem
├── backend/
│   ├── config/settings/          base · dev · test · prod (cada um importa base)
│   ├── config/urls.py            Admin (com prefixo da VPS) + /api/v1/
│   ├── config/api_v1.py          cada app de domínio registra suas rotas aqui
│   ├── apps/common/              health check e utilidades compartilhadas
│   └── tests/                    testes transversais (configuração)
├── infra/deploy.sh               publicação na VPS
├── compose.yml                   desenvolvimento
├── docker-compose.deploy.yml     produção (labels do Traefik)
└── .github/workflows/            ci.yml · deploy.yml
```
O `frontend/` nasce na mudança do front (ver `capability-map.md`).

## Padrões (com exemplo real)
| Assunto | Padrão | Exemplo |
|---|---|---|
| Configuração | uma função `env()` sem padrão para segredo; settings por ambiente | `backend/config/settings/base.py`, `prod.py` |
| App de domínio | `models` · `services` · `serializers` · `views` · `urls` · `tests`; um app por domínio | `backend/apps/common/` |
| Regra de negócio | no service; service não importa DRF; cálculo puro em `domain.py` | — (primeira entrega: acesso-espaco) |
| Endpoint | `APIView`/`ViewSet` fina; permissão padrão `IsAuthenticated`, rota pública declara `AllowAny` | `backend/apps/common/views.py` |
| Rotas | cada app expõe `urls.py` incluído em `config/api_v1.py` | `backend/apps/common/urls.py` |
| Testes | pytest-django em PostgreSQL real; ID da spec no nome ou na docstring | `backend/apps/common/tests/test_health.py` |
| Deploy | compose de produção sem porta publicada; serviços com nome único na rede `traefik_proxy` | `docker-compose.deploy.yml` |

## Nomes
- Código, docstrings e comentários em português; infraestrutura pode usar termos em inglês.
- Serviços na rede compartilhada com prefixo do projeto: `entrelinhas-api`, `entrelinhas-web`.
- Branch única `main` (projeto pessoal). Commits em Conventional Commits, autor `jpjamal <jpfisica3@gmail.com>`,
  sem coautores nem atribuição de IA; mensagem cita os IDs da spec quando houver.
- Mudanças em `specs/changes/NNN-slug/`; capacidades em kebab-case; siglas de 2–5 letras.

## Padrões concorrentes / dívidas conhecidas
| Onde | Problema | Decisão |
|---|---|---|
| contrato da API | sem gerador de OpenAPI (exigiria dependência) | contrato escrito à mão em `contracts/`; gerar do código quando a primeira API de domínio pedir (ADR) |
