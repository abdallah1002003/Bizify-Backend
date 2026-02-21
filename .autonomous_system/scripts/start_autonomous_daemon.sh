#!/bin/bash
# Autonomous System Daemon Launcher with Worker Orchestrator
# Manages multiple workers from a single command

# Default configuration
WORKERS=3
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --workers)
            WORKERS="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --workers N    Number of workers to spawn (default: 3)"
            echo "  --help         Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "🚀 Launching Autonomous System with Worker Orchestrator"
echo "📂 Working Directory: $PROJECT_ROOT"
echo "🤖 Workers: $WORKERS"
echo ""

# Ensure we are in project root
cd "$PROJECT_ROOT"

# Create logs directory
mkdir -p autonomous_reports/logs

# Check if orchestrator is already running
if [ -f .orchestrator.pid ]; then
    OLD_PID=$(cat .orchestrator.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "⚠️  Orchestrator already running (PID: $OLD_PID)"
        echo "   Stop it first with: ./autonomous_system/scripts/stop_autonomous_daemon.sh"
        exit 1
    else
        echo "🧹 Cleaning up stale PID file"
        rm .orchestrator.pid
    fi
fi

# Start orchestrator
echo "🎛️  Starting Worker Orchestrator..."
nohup python3 autonomous_system/core/worker_orchestrator.py \
    --workers $WORKERS \
    --project-root "$PROJECT_ROOT" \
    > autonomous_reports/logs/orchestrator.log 2>&1 &

ORCHESTRATOR_PID=$!

# Wait a moment for startup
sleep 2

# Check if orchestrator started successfully
if ps -p $ORCHESTRATOR_PID > /dev/null 2>&1; then
    echo "✅ Orchestrator Started Successfully!"
    echo "🆔 Orchestrator PID: $ORCHESTRATOR_PID"
    echo "🤖 Spawning $WORKERS workers..."
    echo ""
    
    # Wait for workers to start
    sleep 3
    
    # Show status
    if [ -f .workers_state.json ]; then
        echo "📊 Worker Status:"
        python3 -c "import json; data=json.load(open('.workers_state.json')); print(f\"   Workers Active: {data['worker_count']}\"); [print(f\"   - {wid}: PID {w['pid']}\") for wid, w in data['workers'].items()]"
        echo ""
    fi
    
    echo "📜 Logs:"
    echo "   - Orchestrator: autonomous_reports/logs/orchestrator.log"
    echo "   - Workers: autonomous_reports/logs/Worker-*.log"
    echo ""
    echo "📊 Dashboard: cat LIVE_DASHBOARD.md"
    echo "🛑 To stop: ./autonomous_system/scripts/stop_autonomous_daemon.sh"
else
    echo "❌ Failed to start orchestrator"
    echo "📜 Check logs: autonomous_reports/logs/orchestrator.log"
    exit 1
fi
