#!/bin/bash
# Start Live Dashboard Auto-Updater
# Updates dashboard every 5 seconds with real-time metrics

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "🎯 Starting Live Dashboard Auto-Updater..."
echo "📊 Dashboard will update every 5 seconds"
echo "📍 Location: LIVE_DASHBOARD.md"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run dashboard updater in continuous mode
python3 autonomous_system/monitoring/dashboard_updater.py --interval 5
