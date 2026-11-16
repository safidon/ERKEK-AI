#!/bin/sh
# PostgreSQL backup: /backups/erkek_ai_YYYY-MM-DD_HHMM.sql.gz
#
# - Күн сайын BACKUP_HOUR_UTC сағатта (әдепкі 22:00 UTC = 03:00 Астана).
# - Іске қосылғанда соңғы 24 сағатта көшірме болмаса — бірден жасайды.
# - Файлдар тек иесіне оқылады (ішінде жеке деректер бар).
# - BACKUP_KEEP_DAYS күннен ескілері өшіріледі.
set -eu

umask 077

KEEP_DAYS="${BACKUP_KEEP_DAYS:-14}"
HOUR_UTC="${BACKUP_HOUR_UTC:-22}"

chmod 700 /backups 2>/dev/null || true
chmod 600 /backups/erkek_ai_*.sql.gz 2>/dev/null || true

make_backup() {
	STAMP="$(date -u +%Y-%m-%d_%H%M)"
	FILE="/backups/erkek_ai_${STAMP}.sql.gz"

	if pg_dump --no-owner --no-privileges | gzip > "${FILE}.tmp"; then
		mv "${FILE}.tmp" "${FILE}"
		echo "[backup] OK ${FILE} ($(wc -c < "${FILE}") bytes)"
	else
		rm -f "${FILE}.tmp"
		echo "[backup] FAILED ${STAMP}" >&2
	fi

	find /backups -name 'erkek_ai_*.sql.gz' -mtime "+${KEEP_DAYS}" -delete
}

seconds_until_next_run() {
	now=$(date -u +%s)
	since_midnight=$((now % 86400))
	target=$((HOUR_UTC * 3600))
	delay=$(( (target - since_midnight + 86400) % 86400 ))
	[ "$delay" -eq 0 ] && delay=86400
	echo "$delay"
}

# Соңғы тәулікте көшірме жоқ болса — қазір жасаймыз.
if [ -z "$(find /backups -name 'erkek_ai_*.sql.gz' -mmin -1440 2>/dev/null)" ]; then
	echo "[backup] no backup in the last 24h, making one now"
	make_backup
fi

while true; do
	delay=$(seconds_until_next_run)
	echo "[backup] next run in ${delay}s"
	sleep "$delay"
	make_backup
done
