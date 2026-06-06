#!/bin/bash
# Start the VN Banking Intelligence app (backend + frontend)

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "=== VN Banking Intelligence ==="
echo ""

# Backend
echo "[1/2] Starting FastAPI backend on http://localhost:8000 ..."
cd "$ROOT/backend"
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "  Created .env from .env.example — please fill in your API keys"
fi

# Use root venv if present, otherwise create one inside backend/
if [ -f "$ROOT/.venv/bin/uvicorn" ]; then
  UVICORN="$ROOT/.venv/bin/uvicorn"
elif [ -f ".venv/bin/uvicorn" ]; then
  UVICORN=".venv/bin/uvicorn"
else
  echo "  Installing Python dependencies..."
  python3 -m venv "$ROOT/.venv"
  "$ROOT/.venv/bin/pip" install -r requirements.txt -q
  UVICORN="$ROOT/.venv/bin/uvicorn"
fi

cd "$ROOT"
$UVICORN backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID"

# Frontend
echo "[2/2] Starting React frontend on http://localhost:5173 ..."
cd "$ROOT/frontend"
if [ ! -d "node_modules" ]; then
  echo "  Installing Node dependencies..."
  npm install -q
fi

npm run dev &
FRONTEND_PID=$!
echo "  Frontend PID: $FRONTEND_PID"

echo ""
echo "App running:"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both services."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait