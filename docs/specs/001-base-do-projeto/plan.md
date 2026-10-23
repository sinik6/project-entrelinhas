# Plano

1. `backend/`: settings em `base`/`dev`/`test`/`prod` (padrão do Vinculus), app `apps.common` com o health,
   `pyproject.toml` + `uv.lock`, Dockerfile com gunicorn e healthcheck.
2. `compose.yml` de desenvolvimento (banco sem porta publicada, API em 8010).
3. `.github/workflows/ci.yml`: lint, checagens, testes em PostgreSQL, build e validação do compose de produção.
4. `docker-compose.deploy.yml` com labels do Traefik e nomes únicos na rede compartilhada;
   `infra/deploy.sh` (build, backup, migrations, subida, conferência pelo HTTPS público).
5. `.github/workflows/deploy.yml` após o CI, no ambiente `production`.
6. Criar o repositório e o ambiente `production`; primeiro deploy conferido na VPS.

## Ameaças
Esta spec mexe em deploy e segredos.

| O que pode dar errado | Defesa | Teste |
|---|---|---|
| Deploy publica código não testado | o workflow só roda após o CI com sucesso em push na `main` | leitura do `deploy.yml` (`if:`) |
| Segredo vai para o Git ou para o rsync | `.env*` ignorados e excluídos do rsync; `.env.production` gerado na VPS, modo 600 | `.gitignore`, `deploy.yml` |
| Produção sobe com chave de desenvolvimento | `prod.py` lê `DJANGO_SECRET_KEY` sem valor padrão | 001-C5 |
| Nome de serviço colide com outro projeto na rede `traefik_proxy` | prefixo `entrelinhas-` | revisão do compose |
| Deploy falha no meio e serve código novo com banco antigo | `deploy.sh` para a API antes das migrations e só a sobe depois | `deploy.sh` (`set -e`) |
