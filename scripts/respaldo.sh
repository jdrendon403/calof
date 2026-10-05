#!/usr/bin/env bash
# Respaldo diario de la base de datos y de las fotos/PDF (volumen media_data).
# Uso: scripts/respaldo.sh            (lo ejecuta cron todos los días)
# Variables: RESPALDO_DIR (por defecto ~/respaldos), RETENCION_DIAS (por defecto 14).
#
# Restaurar:
#   docker compose -f docker-compose.prod.yml exec -T db pg_restore -U sgtp -d sgtp --clean --if-exists < sgtp_FECHA.dump
#   docker run --rm -i -v calof_media_data:/media alpine tar xzf - -C /media < media_FECHA.tgz
set -euo pipefail

PROYECTO="$(cd "$(dirname "$0")/.." && pwd)"
DESTINO="${RESPALDO_DIR:-$HOME/respaldos}"
RETENCION_DIAS="${RETENCION_DIAS:-14}"
FECHA="$(date +%Y%m%d_%H%M)"
COMPOSE=(docker compose -f "$PROYECTO/docker-compose.prod.yml" --project-directory "$PROYECTO")

mkdir -p "$DESTINO"
chmod 700 "$DESTINO"

# Base de datos (formato custom de pg_dump, restaurable con pg_restore)
"${COMPOSE[@]}" exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB"' > "$DESTINO/sgtp_$FECHA.dump.tmp"
mv "$DESTINO/sgtp_$FECHA.dump.tmp" "$DESTINO/sgtp_$FECHA.dump"

# Fotos, firmas y PDF de informes
# Nombre exacto del volumen del proyecto (por defecto el proyecto compose se llama como la carpeta)
VOLUMEN="${COMPOSE_PROJECT_NAME:-$(basename "$PROYECTO")}_media_data"
if docker volume inspect "$VOLUMEN" >/dev/null 2>&1; then
  docker run --rm -v "$VOLUMEN":/media:ro alpine tar czf - -C /media . > "$DESTINO/media_$FECHA.tgz.tmp"
  mv "$DESTINO/media_$FECHA.tgz.tmp" "$DESTINO/media_$FECHA.tgz"
fi

# Borrar respaldos automáticos más viejos que la retención. El patrón exige el nombre exacto
# (sgtp_AAAAMMDD_HHMM.dump), así no borra respaldos manuales como sgtp_..._antes_migracion.dump.
AUTO='[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9]'
find "$DESTINO" -maxdepth 1 -type f \( -name "sgtp_$AUTO.dump" -o -name "media_$AUTO.tgz" \) \
  -mtime +"$RETENCION_DIAS" -delete

echo "$(date '+%F %T') respaldo OK: sgtp_$FECHA.dump $( [ -f "$DESTINO/media_$FECHA.tgz" ] && echo "media_$FECHA.tgz")"
