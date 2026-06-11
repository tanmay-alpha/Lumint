#!/usr/bin/env bash
# Smoke test for the Lumint FastAPI backend.
#
# Runs after `make smoke` (the Makefile invokes this file). Checks:
#   1. /healthz returns 200
#   2. /readyz returns 200 (or 503 with a useful error body)
#   3. /api/openapi.json returns 200 and is valid JSON
#   4. CORS headers are correct on a request with an Origin header
#
set -euo pipefail

# Allow a custom PORT via environment; default to 8000.
PORT="${PORT:-8000}"
HOST="http://localhost:${PORT}"
PID=""

# Helper to run the server in the background.
start_server() {
    # Resolve to the backend/ directory regardless of where this script is
    # invoked from. The Windows venv ships a `python.exe` under Scripts/; on
    # POSIX this would be `bin/python` — try both for portability.
    local backend_dir
    backend_dir="$(cd "$(dirname "$0")/.." && pwd)"
    cd "$backend_dir"

    local py
    if [[ -x "./venv/Scripts/python.exe" ]]; then
        py="./venv/Scripts/python.exe"
    elif [[ -x "./venv/bin/python" ]]; then
        py="./venv/bin/python"
    else
        echo "FAIL: no python interpreter found under backend/venv/"
        exit 1
    fi

    "$py" -m uvicorn app.main:app --port "$PORT" &
    PID=$!
    echo "Started server on PID $PID, listening on $HOST"
}

cleanup() {
    if [[ -n "$PID" ]]; then
        echo "Killing server (PID $PID)..."
        kill "$PID" 2>/dev/null || true
        wait "$PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

# Wait up to 30s for the server to be healthy.
wait_for_server() {
    local max_attempts=30
    local attempt=0
    echo "Waiting up to ${max_attempts}s for /healthz..."
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -sfS "$HOST/healthz" > /dev/null 2>&1; then
            echo "Server is up after $((attempt + 1))s"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    echo "Server never became healthy after ${max_attempts}s"
    return 1
}

echo "=== Starting backend for smoke test ==="
start_server
wait_for_server

echo "=== Testing /healthz ==="
HEALTH_RESP=$(curl -fsS "$HOST/healthz")
echo "$HEALTH_RESP"
HEALTH_STATUS=$(echo "$HEALTH_RESP" | python -c "import sys,json; print(json.load(sys.stdin).get('status'))" 2>/dev/null)
if [[ "$HEALTH_STATUS" != "ok" ]]; then
    echo 'FAIL: /healthz did not return {"status": "ok"}'
    exit 1
fi
echo 'OK: /healthz returns 200 with {"status": "ok"}'

echo "=== Testing /readyz ==="
READY_RESP=$(curl -fsS "$HOST/readyz")
echo "$READY_RESP"
READY_STATUS_CODE=$(curl -fsS -o /dev/null -w "%{http_code}" "$HOST/readyz")
# /readyz returns 200 when all deps are ready:
#   - in test env with SQLite, the DB check passes
#   - tesseract might not be on PATH in CI (but that doesn't break the /readyz route itself)
#   - the returned JSON includes a "checks" key either way, which is sufficient for the smoke test.
if ! echo "$READY_RESP" | python -c "import sys,json; d=json.load(sys.stdin); assert 'status' in d and 'checks' in d" 2>/dev/null; then
    echo "FAIL: /readyz returned invalid JSON"
    exit 1
fi
echo "OK: /readyz returns a properly-formed JSON (status: $READY_STATUS_CODE)"

echo "=== Testing /api/health (legacy) ==="
LEGACY_RESP=$(curl -fsS "$HOST/api/health")
echo "$LEGACY_RESP"
LEGACY_STATUS=$(echo "$LEGACY_RESP" | python -c "import sys,json; print(json.load(sys.stdin).get('status'))" 2>/dev/null)
if [[ "$LEGACY_STATUS" != "ok" ]]; then
    echo 'FAIL: /api/health did not return {"status": "ok"}'
    exit 1
fi
echo "OK: /api/health returns 200"

echo "=== Testing /openapi.json ==="
OPENAPI_RESP=$(curl -fsS "$HOST/openapi.json")
echo "$OPENAPI_RESP" | python -c "import sys,json; d=json.load(sys.stdin); assert 'openapi' in d; print('Valid OpenAPI document')"
echo "OK: /openapi.json returns a valid OpenAPI doc"

echo "=== Testing CORS header ==="
CORS_RESP=$(curl -fsS -H "Origin: http://localhost:3000" -i "$HOST/healthz" 2>/dev/null)
if echo "$CORS_RESP" | grep -qi "access-control-allow-origin"; then
    echo "OK: CORS header is present when Origin is sent"
else
    echo "FAIL: no Access-Control-Allow-Origin header in response"
    echo "$CORS_RESP"
    exit 1
fi

echo "=== Smoke test passed ==="
exit 0