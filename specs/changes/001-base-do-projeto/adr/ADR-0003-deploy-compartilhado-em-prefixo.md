# ADR-0003 — Deploy na VPS compartilhada, sob o prefixo /entrelinhas

- Status: aceito
- Data: 2026-10-23
- Mudança de origem: 001-base-do-projeto

## Contexto
A VPS já hospeda Jalapão Store e Vinculus atrás do Traefik do repositório `traefikproxy`, com certificado do
domínio `jpsys.duckdns.org` e do IP.

## Decisão
O Entrelinhas publica em `https://jpsys.duckdns.org/entrelinhas` e pelo IP. O projeto não tem proxy nem porta
publicada; as rotas são rótulos no `docker-compose.deploy.yml`. Serviços na rede `traefik_proxy` têm nome único
(`entrelinhas-api`, `entrelinhas-web`), porque o Docker registra o nome de cada serviço como nome de rede em
todas as redes dele. Push na `main` → workflow `CI` → workflow `Deploy Entrelinhas` (ambiente `production`) →
`infra/deploy.sh`. O Django usa `DJANGO_PREFIXO_URL=entrelinhas` no Admin e nos estáticos.

## Alternativas consideradas
| Opção | Prós | Contras |
|---|---|---|
| Domínio próprio | URL limpa, sem prefixo | custo e certificado novos; não é o padrão atual da VPS |
| Subdomínio próprio no duckdns | sem prefixo | exige novo nome, novo certificado e nova regra no Traefik central |

## Consequências
O deploy depende da rede `traefik_proxy`. O front precisa de `basePath` `/entrelinhas`. Segredos do ambiente
`production`: `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD`, `DEPLOY_SSH_KEY`; variáveis `DEPLOY_HOST`, `DEPLOY_USER`.
