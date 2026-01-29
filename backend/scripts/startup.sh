#!/bin/bash

set -e

echo "🚀 Starting ErgoLab Backend..."

echo "⏳ Waiting for PostgreSQL..."
while ! pg_isready -h postgres -U ergolab; do
  sleep 1
done

echo "✓ PostgreSQL ready"

echo "📦 Running database migrations..."
alembic upgrade head

echo "🗂️  Initializing MinIO bucket..."
python scripts/init_minio.py

echo "👤 Creating admin user..."
python scripts/create_admin.py

echo "✅ Backend ready!"

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
