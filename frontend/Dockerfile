# SDK do Flutter em contêiner (ADR-0005): nada de Flutter instalado no Windows.
# Baixa o SDK oficial do servidor do Google e confere o SHA-256 publicado em
# https://storage.googleapis.com/flutter_infra_release/releases/releases_linux.json
# Para trocar de versão: atualizar FLUTTER_VERSAO e FLUTTER_SHA256 com os valores desse índice.
# Imagem de ferramentas: usada pelo infra/web.Dockerfile (build) e pelo CI (analyze e test).
FROM debian:bookworm-slim

ARG FLUTTER_VERSAO=3.47.8
ARG FLUTTER_SHA256=baf7dcc5a3dbba60fe863bf493a6cf203195621f7786eaa5a1bba02cd0d87dd2

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git unzip xz-utils \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 flutter \
    && mkdir -p /opt /app \
    && chown flutter /opt /app

USER flutter
WORKDIR /opt

RUN curl -fsSL -o flutter.tar.xz \
        "https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_${FLUTTER_VERSAO}-stable.tar.xz" \
    && echo "${FLUTTER_SHA256}  flutter.tar.xz" | sha256sum -c - \
    && tar -xJf flutter.tar.xz \
    && rm flutter.tar.xz

ENV PATH="/opt/flutter/bin:/opt/flutter/bin/cache/dart-sdk/bin:${PATH}" \
    PUB_CACHE=/home/flutter/.pub-cache \
    FLUTTER_SUPPRESS_ANALYTICS=true

RUN git config --global --add safe.directory /opt/flutter \
    && git config --global --add safe.directory /app \
    && flutter config --no-analytics --no-cli-animations \
    && dart --disable-analytics \
    && flutter precache --web \
    && flutter --version

# O CI roda como root (o usuário do runner não é o `flutter`, uid 1000): o git de root também precisa
# aceitar o SDK e a pasta montada como seguros.
USER root
RUN git config --system --add safe.directory '*'
USER flutter

WORKDIR /app
CMD ["flutter", "--version"]
