#!/usr/bin/env bash

# Complete bootstrap script for the Patient Monitoring System.
# It installs backend + frontend dependencies, seeds the database,
# and generates the monitoring snapshots required by the UI.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
PIP_BIN="${PIP_BIN:-pip}"

command -v "$PYTHON_BIN" >/dev/null 2>&1 || {
  echo "❌ Python binary '$PYTHON_BIN' not found. Set PYTHON_BIN to your interpreter." >&2
  exit 1
}

command -v npm >/dev/null 2>&1 || {
  echo "❌ npm is required (Node.js 18+). Install Node.js and retry." >&2
  exit 1
}

cd "$PROJECT_ROOT"

echo "➤ Creating Python virtual environment (venv)..."
if [[ ! -d "venv" ]]; then
  "$PYTHON_BIN" -m venv venv
fi

echo "➤ Activating virtual environment..."
# shellcheck disable=SC1091
source "venv/bin/activate"

echo "➤ Installing backend dependencies..."
pip install --upgrade pip >/dev/null
pip install -r backend/requirements.txt

ENV_FILE="backend/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "➤ Creating backend/.env from template..."
  cp backend/.env.example "$ENV_FILE"
  echo "   ⚠️  Update '$ENV_FILE' with the correct DATABASE_URL before continuing if needed."
fi

echo "➤ Bootstrapping database from CSV files..."
python -m backend.app.db.bootstrap_db

echo "➤ Generating monitoring/detail snapshots..."
python -m backend.app.db.snapshot_builder

echo "➤ Installing frontend dependencies..."
(
  cd frontend
  npm install
)

echo ""
echo "✅ Setup complete!"
echo "Backend: uvicorn backend.app.main:app --reload --port 8000"
echo "Frontend: (cd frontend && npm run dev)"

