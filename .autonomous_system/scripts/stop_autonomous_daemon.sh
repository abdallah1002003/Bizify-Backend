#!/bin/bash
# Stop Autonomous System Daemon and All Workers
# Gracefully shuts down orchestrator and all managed workers

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "🛑 Stopping Autonomous System..."
echo ""

# Check if orchestrator is running
if [ ! -f .orchestrator.pid ]; then
    echo "⚠️  No orchestrator PID file found"
    echo "   Checking for running workers..."
    
    # Try to stop any running workers directly
    if [ -f .workers.json ]; then
        echo "   Found workers, attempting to stop..."
        python3 -c "
import json
import os
import signal

try:
    with open('.workers.json') as f:
        workers = json.load(f)
    
    for worker_id, data in workers.items():
        pid = data.get('pid')
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
                print(f'   Sent SIGTERM to {worker_id} (PID: {pid})')
            except ProcessLookupError:
                print(f'   {worker_id} (PID: {pid}) not running')
            except Exception as e:
                print(f'   Error stopping {worker_id}: {e}')
except FileNotFoundError:
    print('   No workers file found')
except Exception as e:
    print(f'   Error: {e}')
"
    fi
    
    exit 0
fi

# Read orchestrator PID
ORCHESTRATOR_PID=$(cat .orchestrator.pid)

# Check if orchestrator is actually running
if ! ps -p $ORCHESTRATOR_PID > /dev/null 2>&1; then
    echo "⚠️  Orchestrator (PID: $ORCHESTRATOR_PID) is not running"
    echo "🧹 Cleaning up stale files..."
    rm -f .orchestrator.pid .workers_state.json
    exit 0
fi

echo "🎛️  Stopping Orchestrator (PID: $ORCHESTRATOR_PID)..."

# Send SIGTERM for graceful shutdown
kill -TERM $ORCHESTRATOR_PID

# Wait for graceful shutdown (up to 15 seconds)
echo "⏳ Waiting for graceful shutdown..."
for i in {1..15}; do
    if ! ps -p $ORCHESTRATOR_PID > /dev/null 2>&1; then
        echo "✅ Orchestrator stopped gracefully"
        break
    fi
    sleep 1
    echo -n "."
done
echo ""

# Force kill if still running
if ps -p $ORCHESTRATOR_PID > /dev/null 2>&1; then
    echo "⚠️  Orchestrator didn't stop gracefully, forcing..."
    kill -9 $ORCHESTRATOR_PID
    sleep 1
    
    if ps -p $ORCHESTRATOR_PID > /dev/null 2>&1; then
        echo "❌ Failed to stop orchestrator"
        exit 1
    else
        echo "✅ Orchestrator force-stopped"
    fi
fi

# Verify all workers are stopped
if [ -f .workers_state.json ]; then
    echo "🔍 Verifying workers stopped..."
    python3 -c "
import json
import os

try:
    with open('.workers_state.json') as f:
        state = json.load(f)
    
    running_workers = []
    for worker_id, data in state.get('workers', {}).items():
        pid = data.get('pid')
        if pid:
            try:
                os.kill(pid, 0)  # Check if process exists
                running_workers.append((worker_id, pid))
            except ProcessLookupError:
                pass
    
    if running_workers:
        print(f'   ⚠️  {len(running_workers)} workers still running:')
        for wid, pid in running_workers:
            print(f'      - {wid} (PID: {pid})')
            try:
                os.kill(pid, 15)  # SIGTERM
                print(f'        Sent SIGTERM')
            except:
                pass
    else:
        print('   ✅ All workers stopped')
except Exception as e:
    print(f'   Error checking workers: {e}')
"
fi

# Cleanup
echo "🧹 Cleaning up..."
rm -f .orchestrator.pid .workers_state.json

echo ""
echo "✅ Autonomous System stopped successfully"
