#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# run.sh — Start the Power Up API development server
#
# Behaviour:
#   • If venv/ does not exist → create it and install all deps, then run
#   • If venv/ exists          → sync deps (uv is fast: skips if up-to-date),
#                                then run
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

VENV_DIR="venv"
# Force uv to use our named venv instead of its default .venv
export UV_PROJECT_ENVIRONMENT="$VENV_DIR"

# ── Locate uv ────────────────────────────────────────────────────────────────
if ! command -v uv &>/dev/null; then
    echo "❌  uv not found. Install it with:"
    echo "    curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "    or: brew install uv"
    exit 1
fi

# ── Create venv if missing ────────────────────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo "⚙️   Virtual environment not found. Creating '$VENV_DIR/'..."
    uv venv "$VENV_DIR" --python 3.12
    echo "✅  Created '$VENV_DIR/'"
else
    echo "✅  Virtual environment '$VENV_DIR/' found."
fi

# ── Sync dependencies (no-op if everything is already up-to-date) ─────────────
echo "📦  Syncing dependencies..."
uv sync

# ── Copy .env.example → .env if .env is missing ──────────────────────────────
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    echo "📋  Created .env from .env.example — update it with real values before connecting to a DB."
fi

# ── Run ───────────────────────────────────────────────────────────────────────
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-9000}"
RELOAD="${RELOAD:-true}"

echo ""
echo "🚀  Starting Power Up API on http://${HOST}:${PORT}"
echo "    Swagger UI → http://localhost:${PORT}/docs"
echo "    ReDoc      → http://localhost:${PORT}/redoc"
echo "    Health     → http://localhost:${PORT}/health"
echo ""

uv run uvicorn app.main:app \
    --host "$HOST" \
    --port "$PORT" \
    $( [ "$RELOAD" = "true" ] && echo "--reload" || true )
