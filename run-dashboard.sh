#!/usr/bin/env bash
# GT AI Dashboard Runner
# Starts both backend and frontend, then opens the browser
#
# Usage: ./run-dashboard.sh
#        ./run-dashboard.sh --stop   # kills existing dashboard processes

set -e

AGENT_HOME="/Users/gt/Public/MyFiles/agent-home"
DASHBOARD="$AGENT_HOME/dashboard"
BACKEND_PORT=7373
FRONTEND_PORT=3000
PIDFILE="/tmp/gt-dashboard.pid"

# Use Python 3.11 explicitly (3.14 breaks pydantic)
PYTHON="/opt/homebrew/bin/python3.11"

case "${1:-}" in
  --stop)
    echo "Stopping dashboard..."
    if [ -f "$PIDFILE" ]; then
      while read -r pid; do
        kill "$pid" 2>/dev/null || true
      done < "$PIDFILE"
      rm -f "$PIDFILE"
    fi
    pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
    pkill -f "vite.*dashboard/frontend" 2>/dev/null || true
    echo "Stopped."
    exit 0
    ;;
esac

cd "$DASHBOARD"

# Check if already running
if python3 -c "import socket; exit(0 if socket.socket().connect_ex(('127.0.0.1',$BACKEND_PORT))==0 else 1)" 2>/dev/null; then
    echo "Backend already running on port $BACKEND_PORT"
else
    echo "Starting backend..."
    cd backend
    if [ ! -d "venv" ]; then
        echo "  Creating Python venv with $PYTHON..."
        "$PYTHON" -m venv venv
    fi
    source venv/bin/activate
    echo "  Installing deps..."
    pip install -q -r requirements.txt
    echo "  Starting uvicorn..."
    python run.py &
    echo $! >> "$PIDFILE"
    cd ..
    sleep 2
fi

if python3 -c "import socket; exit(0 if socket.socket().connect_ex(('127.0.0.1',$FRONTEND_PORT))==0 else 1)" 2>/dev/null; then
    echo "Frontend already running on port $FRONTEND_PORT"
else
    echo "Starting frontend..."
    cd frontend
    if [ ! -d "node_modules" ]; then
        echo "  Installing npm deps..."
        /opt/homebrew/bin/npm install
    fi
    if [ ! -d "dist" ]; then
        echo "  Building frontend..."
        /opt/homebrew/bin/npm run build
    fi
    echo "  Starting Vite dev server..."
    /opt/homebrew/bin/npm run dev &
    echo $! >> "$PIDFILE"
    cd ..
    sleep 2
fi

echo ""
echo "GT AI Dashboard is running:"
echo "  Frontend: http://localhost:$FRONTEND_PORT"
echo "  Backend:  http://localhost:$BACKEND_PORT/api/docs"
echo ""
echo "Stop with: ./run-dashboard.sh --stop"

# Open browser
open "http://localhost:$FRONTEND_PORT" 2>/dev/null || true
