#!/bin/bash

# .env fayldan o'qish
export $(grep -v '^#' .env | xargs)
export $(grep -v '^#' .env.local | xargs)

# Container nomi
CONTAINER=$(docker ps -aqf "name=stats-db")

# Foydalanuvchidan fayl nomini so'rash
read -p "⬇️ Tiklash uchun SQL fayl nomini kiriting (masalan: dump_20-06-2025_10_30_00.sql): " DUMP_FILE

# Fayl nomi bo'sh bo'lmasligini tekshirish
if [ -z "backups/$DUMP_FILE" ]; then
  echo "❌ Fayl nomi kiritilmadi."
  exit 1
fi

# Fayl mavjudligini tekshirish
if [ ! -f "backups/$DUMP_FILE" ]; then
  echo "❌ Fayl topilmadi: backups/$DUMP_FILE"
  exit 1
fi

# Restore qilish
cat "backups/$DUMP_FILE" | docker exec -i "$CONTAINER" psql -U "$DB_USER" -d "$DB_NAME"

echo "✅ Tiklash yakunlandi: backups/$DUMP_FILE"
