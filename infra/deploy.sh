#!/usr/bin/env bash
# Publicação na VPS. Roda em ~/project-entrelinhas, chamado pelo workflow deploy.yml depois do
# rsync e do .env.production (segredos do GitHub, modo 600).
#
# Ordem: constrói a imagem → congela a escrita (para a API) → backup do banco → migrations →
# sobe tudo → confere pelo HTTPS público. Falhou no meio? A API fica parada para inspeção;
# nunca serve código novo com banco pela metade.
set -euo pipefail
cd "$(dirname "$0")/.."

test -s .env.production
dc() {
    docker compose -f docker-compose.deploy.yml --env-file .env.production "$@"
}
# Lê um valor do .env.production: vale a última ocorrência (os segredos são gravados depois das variables)
# e as aspas simples que o workflow põe em volta do valor são tiradas. O arquivo usa aspas simples para o
# Compose não interpolar `$` nem tratar `#` como comentário (um pedaço da senha apareceria em aviso no log).
valor() { grep "^$1=" .env.production | tail -n 1 | cut -d= -f2- | tr -d '\r' | sed -e "s/^'//" -e "s/'\$//" || true; }

# Nome, e-mail e senha do administrador vão só à execução do comando (spec 002): nunca ao serviço da API.
admin_inicial() {
    ADMIN_USUARIO="$(valor ADMIN_USUARIO)" ADMIN_EMAIL="$(valor ADMIN_EMAIL)" \
    SENHA_ADMIN_INICIAL="$(valor SENHA_ADMIN_INICIAL)" \
        dc run --rm --no-deps -l traefik.enable=false -e SENHA_ADMIN_INICIAL -e ADMIN_USUARIO -e ADMIN_EMAIL \
        entrelinhas-api python manage.py administrador_inicial "$@"
}

# O traefikproxy publica o sistema (rede traefik_proxy). Sem ela o compose falharia no meio,
# com a API já parada.
if ! docker network inspect traefik_proxy >/dev/null 2>&1; then
    echo "A rede traefik_proxy não existe: publique o traefikproxy antes." >&2
    exit 1
fi

backups="$HOME/backups/project-entrelinhas"
mkdir -p "$backups"
chmod 700 "$backups"
stamp=$(date -u +%Y%m%dT%H%M%SZ)

echo "=== Construindo as imagens"
# O SDK do Flutter (com SHA-256 conferido) é uma imagem à parte, base do build do app web.
docker build -t entrelinhas-flutter-sdk:local frontend
dc build

echo "=== Conferindo a configuração do administrador"
# Antes de parar a API (spec 002, REQ-2.5): senha ausente, curta ou comum aborta aqui, com o Admin ainda
# no ar. A conferência não usa o banco; a criação da conta vem depois, em "Administrador inicial".
admin_inicial --verificar

echo "=== Congelando a escrita e fazendo backup"
dc stop entrelinhas-api >/dev/null 2>&1 || true
if dc ps --status running --services | grep -qx db; then
    dc exec -T db pg_dump -U entrelinhas -d entrelinhas -Fc > "$backups/db-$stamp.dump"
    test -s "$backups/db-$stamp.dump"
    chmod 600 "$backups/db-$stamp.dump"
    echo "   banco: $backups/db-$stamp.dump"
fi

echo "=== Migrations"
dc up -d --wait db
dc run --rm --no-deps -l traefik.enable=false entrelinhas-api python manage.py migrate --noinput

echo "=== Administrador inicial"
# O comando não escreve a senha. Uma recusa que só aparece aqui (usuário comum com o mesmo nome) falha o
# deploy com a API já parada, por causa do `set -e`; senha ausente ou fraca já foi barrada acima.
admin_inicial

echo "=== Subindo o sistema"
dc up -d --wait --remove-orphans

echo "=== Conferindo pelo HTTPS público"
# Rota nova: o Traefik pode levar alguns segundos para ler os labels. --retry-all-errors repete
# também erro de certificado (o do domínio sai do resolver duckdns).
for base in https://jpsys.duckdns.org https://217.216.82.25; do
    for caminho in /entrelinhas/admin/login/ /entrelinhas/ /entrelinhas/api/v1/auth/csrf; do
        curl --fail --silent --show-error --insecure --output /dev/null \
            --retry 20 --retry-delay 3 --retry-all-errors "$base$caminho"
        echo "   $base$caminho: ok"
    done
done
codigo=$(curl --silent --output /dev/null --write-out '%{http_code} %{redirect_url}' http://217.216.82.25/entrelinhas/admin/login/)
case "$codigo" in
    30[18]\ https://217.216.82.25/entrelinhas/admin/login/) echo "   http → https: ok" ;;
    *) echo "HTTP não redirecionou para HTTPS: $codigo" >&2; exit 1 ;;
esac

# Guarda só os 10 backups mais novos do banco. `find` (e não `ls` com curinga): no primeiro
# deploy não há backup e o curinga derrubaria o script pelo pipefail.
find "$backups" -maxdepth 1 -type f -name 'db-*' -printf '%T@ %p\n' \
    | sort -rn | tail -n +11 | cut -d' ' -f2- | xargs -r rm -f

dc ps
echo "✅ Entrelinhas publicado em https://jpsys.duckdns.org/entrelinhas"
