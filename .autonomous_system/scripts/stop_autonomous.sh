#!/bin/bash
# Stop Autonomous System Script
# Gracefully stops all autonomous workers and orchestrator

echo "🛑 Stopping Autonomous System..."
echo ""

# Find all autonomous processes
echo "📋 Finding active processes..."
WORKERS=$(ps aux | grep -E "worker" | grep -v grep | awk '{print $2}')
ORCHESTRATOR=$(ps aux | grep -E "orchestrator" | grep -v grep | awk '{print $2}')

# Count processes
WORKER_COUNT=$(echo "$WORKERS" | grep -v '^$' | wc -l | tr -d ' ')
ORCH_COUNT=$(echo "$ORCHESTRATOR" | grep -v '^$' | wc -l | tr -d ' ')

echo "   Workers found: $WORKER_COUNT"
echo "   Orchestrators found: $ORCH_COUNT"
echo ""

# Graceful shutdown
if [ ! -z "$WORKERS" ] || [ ! -z "$ORCHESTRATOR" ]; then
    echo "⏳ Attempting graceful shutdown..."
    
    # Kill workers
    if [ ! -z "$WORKERS" ]; then
        echo "$WORKERS" | while read pid; do
            if [ ! -z "$pid" ]; then
                kill -TERM $pid 2>/dev/null && echo "   ✓ Stopped worker PID: $pid"
            fi
        done
    fi
    
    # Kill orchestrator
    if [ ! -z "$ORCHESTRATOR" ]; then
        echo "$ORCHESTRATOR" | while read pid; do
            if [ ! -z "$pid" ]; then
                kill -TERM $pid 2>/dev/null && echo "   ✓ Stopped orchestrator PID: $pid"
            fi
        done
    fi
    
    # Wait for graceful shutdown
    echo ""
    echo "⏱️  Waiting 3 seconds for graceful shutdown..."
    sleep 3
    
    # Check if still running
    REMAINING=$(ps aux | grep -E "worker|orchestrator" | grep -v grep | wc -l | tr -d ' ')
    
    if [ "$REMAINING" -gt 0 ]; then
        echo "⚠️  Some processes still running, forcing shutdown..."
        pkill -9 -f "worker" 2>/dev/null
        pkill -9 -f "orchestrator" 2>/dev/null
        sleep 1
    fi
fi

# Final check
FINAL_COUNT=$(ps aux | grep -E "worker|orchestrator" | grep -v grep | wc -l | tr -d ' ')

if [ "$FINAL_COUNT" -eq 0 ]; then
    echo ""
    echo "✅ Autonomous System stopped successfully!"
    echo "📊 All workers and orchestrators terminated"
else
    echo ""
    echo "⚠️  Warning: $FINAL_COUNT processes may still be running"
    echo "   Run: ps aux | grep -E 'worker|orchestrator' | grep -v grep"
fi

echo ""
echo "💡 To restart: python3 autonomous_system/scripts/RUN_FULL_AUTONOMOUS.py"
