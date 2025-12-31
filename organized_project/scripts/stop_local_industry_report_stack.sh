#!/usr/bin/env bash
set -euo pipefail

# Stops services started by start_local_industry_report_stack.sh

PID_RAG="/tmp/smartdigest_rag.pid"
PID_MODEL="/tmp/smartdigest_model_server.pid"
PID_BACKEND="/tmp/smartdigest_backend.pid"
PID_FRONTEND="/tmp/smartdigest_frontend.pid"

kill_pidfile() {
  local f="$1"
  if [ -f "$f" ]; then
    local pid
    pid="$(cat "$f" || true)"
    if [ -n "$pid" ]; then
      kill -9 "$pid" >/dev/null 2>&1 || true
    fi
    rm -f "$f" || true
  fi
}

kill_port() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -ti :"$port" | xargs -r kill -9 || true
  fi
}

echo "=== Stopping SmartDigest local stack ==="

# kill by port first (more reliable)
kill_port 5173 || true
kill_port 3000 || true
kill_port 8001 || true
kill_port 8002 || true

# also kill stored pids
kill_pidfile "$PID_FRONTEND"
kill_pidfile "$PID_BACKEND"
kill_pidfile "$PID_MODEL"
kill_pidfile "$PID_RAG"

echo "Done."


