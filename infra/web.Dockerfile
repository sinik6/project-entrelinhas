# Imagem do nginx de produção (spec 003, ADR-0005 e ADR-0006): compila o Flutter web dentro do build
# (nada de Flutter fora de contêiner) e serve com o nginx, que também repassa /api/ à API.
# O prefixo da VPS entra no `--base-href` e no endereço da API; o Traefik tira o prefixo antes do nginx.
# A imagem do SDK (frontend/Dockerfile, SHA-256 conferido) é construída antes: `infra/deploy.sh` e o CI a fazem.
FROM entrelinhas-flutter-sdk:local AS flutter
ARG BASE_HREF=/
ARG API_BASE=/api/v1
WORKDIR /app
COPY --chown=flutter frontend/ ./
# Sem service worker (`--pwa-strategy=none`): a instalação como PWA e o cache vêm na mudança de lembretes,
# e um service worker não pode guardar texto de registro.
RUN flutter pub get \
    && flutter build web --release --no-web-resources-cdn --pwa-strategy=none \
         --base-href "${BASE_HREF}" --dart-define=API_BASE="${API_BASE}"

FROM nginx:1.29-alpine
COPY infra/nginx/entrelinhas.conf.template /etc/nginx/templates/default.conf.template
COPY --from=flutter /app/build/web /srv/app
