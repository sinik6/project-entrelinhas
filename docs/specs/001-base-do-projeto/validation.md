# Validação

Executado localmente em 2026-10-23, com PostgreSQL 17 descartável (container apagado depois).

| Critério | Prova | Resultado |
|---|---|---|
| 001-C1 | `test_health_responde_ok_sem_login` (`backend/apps/common/tests/test_health.py`) | passa |
| 001-C2 | `test_health_consulta_o_banco` (mesmo arquivo): consulta falhando levanta erro, não devolve 200 | passa |
| 001-C3 | `ruff check` e `ruff format --check` limpos (20 arquivos); `manage.py check` e `makemigrations --check` sem pendência; `check --deploy` com `config.settings.prod` sem avisos (rodado em 2026-10-19, antes das mudanças de docs; o código de settings não mudou depois) | passa localmente; execução no CI **não conferida** |
| 001-C4 | `docker build backend` concluiu e `docker compose -f docker-compose.deploy.yml config` válido (2026-10-19); `compose.yml` de desenvolvimento válido por `config` | passa localmente |
| 001-C5 | `test_producao_recusa_subir_sem_secret_key` (`backend/tests/test_configuracao.py`) | passa |
| 001-C6 | — | **pendente**: ambiente `production` não criado, chave SSH não instalada, deploy não executado |

Suíte: `pytest --create-db` → 3 passed.

## Não verificado
- Execução do CI no GitHub (o primeiro push foi feito; o resultado não foi lido).
- `docker compose up --build` completo no Docker local (só `config` e `docker build` foram rodados).
- O deploy na VPS e o certificado em `/entrelinhas` (001-C6).
- `infra/deploy.sh` só passou em `bash -n`; não rodou na VPS.
