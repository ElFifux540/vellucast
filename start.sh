#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$ROOT_DIR/.run"

mkdir -p "$RUN_DIR"

BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

(
  cd "$BACKEND_DIR"
  if [ ! -d ".venv" ]; then
    python3 -m venv .venv
  fi
  # Activation de l'environnement virtuel
  source .venv/bin/activate
  uvicorn app.main:app --reload
) &
BACKEND_PID=$!

(
  cd "$FRONTEND_DIR"
  npm run dev
) &
FRONTEND_PID=$!

echo "$BACKEND_PID" > "$RUN_DIR/backend.pid"
echo "$FRONTEND_PID" > "$RUN_DIR/frontend.pid"

echo "Demarrage OK. PIDs enregistres dans .run"
