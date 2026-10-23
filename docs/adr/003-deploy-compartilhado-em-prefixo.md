# ADR-003 — Deploy na VPS compartilhada, sob o prefixo `/entrelinhas`

**Status:** aceita.

## Decisão
O Entrelinhas roda na VPS onde já estão Jalapão Store e Vinculus, atrás do Traefik do repositório
`traefikproxy`, em `https://jpsys.duckdns.org/entrelinhas` (e pelo IP). O projeto não tem proxy nem
porta publicada. As rotas são labels no `docker-compose.deploy.yml`. Os serviços que entram na rede
`traefik_proxy` têm nome único (`entrelinhas-api`, `entrelinhas-web`), porque o Docker registra o
nome de cada serviço como nome de rede em todas as redes dele.

Push na `main` → workflow `CI` → workflow `Deploy Entrelinhas` (ambiente `production`) →
`infra/deploy.sh`: build, parada da API, backup do banco, migrations, subida e conferência pelo HTTPS público.

## Por quê
Reaproveita o certificado, o roteamento e o pipeline que já funcionam no Vinculus; um domínio só.

## Consequências
- Django usa `DJANGO_PREFIXO_URL=entrelinhas` no Admin e nos estáticos.
- Quando existir o front, ele é construído com `NEXT_PUBLIC_BASE_PATH=/entrelinhas`.
- O deploy depende da rede `traefik_proxy` existir na VPS.
- Segredos do ambiente `production`: `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD`, `DEPLOY_SSH_KEY`
  (variáveis `DEPLOY_HOST`, `DEPLOY_USER`). Nunca vão para o Git.
