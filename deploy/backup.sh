#!/bin/sh
# Күн сайын PostgreSQL backup жасайды: /backups/erkek_ai_YYYY-MM-DD_HHMM.sql.gz
# BACKUP_KEEP_DAYS күннен ескі файлдар өшіріледі.
set -eu

KEEP_DAYS="${BACKUP_KEEP_DAYS:-14}"

while true; do
	STAMP="$(date +%Y-%m-%d_%H%M)"
	FILE="/backups/erkek_ai_${STAMP}.sql.gz"

	if pg_dump --no-owner --no-privileges | gzip > "${FILE}.tmp"; then
		mv "${FILE}.tmp" "${FILE}"
		echo "[backup] OK ${FILE}"
	else
		rm -f "${FILE}.tmp"
		echo "[backup] FAILED ${STAMP}" >&2
	fi

	find /backups -name 'erkek_ai_*.sql.gz' -mtime "+${KEEP_DAYS}" -delete

	sleep 86400
done
