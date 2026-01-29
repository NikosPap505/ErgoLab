#!/bin/bash

set -e

echo "🗄️  Setting up ErgoLab Database..."

echo "📦 Running migrations..."
alembic upgrade head

echo "👤 Creating admin user..."
python scripts/create_admin.py

echo "✅ Database setup complete!"
echo ""
echo "Login credentials:"
echo "  Email: admin@ergolab.gr"
echo "  Password: admin123"
echo ""
echo "API Docs: http://localhost:8000/docs"
