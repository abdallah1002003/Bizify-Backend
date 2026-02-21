#!/bin/bash
# Start Autonomous System Script
# Starts the full autonomous system with all components

echo "🚀 Starting Autonomous System..."
echo ""

# Check if already running
RUNNING=$(ps aux | grep -E "worker|orchestrator" | grep -v grep | wc -l | tr -d ' ')

if [ "$RUNNING" -gt 0 ]; then
    echo "⚠️  Warning: $RUNNING autonomous processes already running"
    echo "   Stop them first with: ./stop_autonomous.sh"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Cancelled"
        exit 1
    fi
fi

# Check current mode
if [ -f ".autonomous_mode.json" ]; then
    MODE=$(cat .autonomous_mode.json | python3 -c "import json, sys; print(json.load(sys.stdin)['mode'])" 2>/dev/null || echo "unknown")
    echo "📋 Current Mode: $MODE"
else
    echo "⚠️  No mode configuration found, will use default (learning_only)"
fi

echo ""
echo "🔧 Starting components..."

# Start the full autonomous system
python3 autonomous_system/scripts/RUN_FULL_AUTONOMOUS.py &

# Wait a moment for startup
sleep 2

# Check if started successfully
STARTED=$(ps aux | grep -E "worker|orchestrator" | grep -v grep | wc -l | tr -d ' ')

if [ "$STARTED" -gt 0 ]; then
    echo ""
    echo "✅ Autonomous System started successfully!"
    echo "📊 Active processes: $STARTED"
    echo ""
    echo "📈 Monitor with:"
    echo "   cat LIVE_DASHBOARD.md"
    echo "   ps aux | grep -E 'worker|orchestrator' | grep -v grep"
    echo ""
    echo "🛑 Stop with:"
    echo "   ./stop_autonomous.sh"
else
    echo ""
    echo "❌ Failed to start autonomous system"
    echo "   Check logs for errors"
fi
