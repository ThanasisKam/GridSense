#!/bin/bash
set -e

echo "==> Seeding databases (idempotent — safe to run multiple times)..."
python scripts/seed.py

echo "==> Starting GridSense API..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
