#!/bin/bash

# .env fayldan o'qish
export $(grep -v '^#' .env | xargs)
export $(grep -v '^#' .env.local | xargs)

# Fayl nomini yaratish
DUMP_NAME="backups/dump_$(date +%d-%m-%Y"_"%H_%M_%S).sql"

# Backup buyrug'i
if pg_dump -c -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" > "$DUMP_NAME"; then
    echo "✅ Backup fayl yaratildi: $DUMP_NAME"
else
    echo "❌ Xatolik yuz berdi! Backup olinmadi."
fi
