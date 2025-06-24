#!/bin/bash

# .env fayldan o'qish
export $(grep -v '^#' .env | xargs)
export $(grep -v '^#' .env.local | xargs)

# Foydalanuvchidan fayl nomini so'rash
read -p "⬇️ Tiklash uchun SQL fayl nomini kiriting (masalan: dump_20-06-2025_10_30_00.sql): " DUMP_FILE

if [ -z "backups/$DUMP_FILE" ]; then
  echo "❌ Fayl nomi kiritilmadi."
  exit 1
fi

if [ ! -f "backups/$DUMP_FILE" ]; then
  echo "❌ Fayl topilmadi: $DUMP_FILE"
  exit 1
fi

# Tiklash buyrug‘i
psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME < "$DUMP_FILE"

echo "✅ Tiklash yakunlandi: backups/$DUMP_FILE"
