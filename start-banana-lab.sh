#!/usr/bin/env bash
# One-command local startup for The Banana Lab (MonkeyZoo Studio).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON="python"
else
  echo "ERROR: Python 3 not found. Install Python 3.10+." >&2
  exit 1
fi

if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  echo "==> Creating virtualenv at .venv"
  "$PYTHON" -m venv "$ROOT/.venv"
  PYTHON="$ROOT/.venv/bin/python"
fi

echo "==> Checking dependencies"
if ! "$PYTHON" -c "import flask, PIL, yaml, jsonschema" 2>/dev/null; then
  echo "==> Installing flask pillow pyyaml jsonschema"
  "$PYTHON" -m pip install --upgrade pip
  "$PYTHON" -m pip install flask pillow pyyaml jsonschema
fi

PORT="${PORT:-8765}"
export PORT

echo "==> Launching MonkeyZoo Studio at http://127.0.0.1:${PORT}/"
echo "Press Ctrl+C to stop."
exec "$PYTHON" "$ROOT/character-bibles/_review_app/app.py"

