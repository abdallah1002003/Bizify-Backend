#!/bin/bash
# End Antigravity Collaborative Session
# Removes session marker and stops autonomous processes

echo "👋 Ending Antigravity Collaborative Session..."

# Remove session marker
rm -f .antigravity_session_active

echo "✅ Session marker removed"
echo "ℹ️  Learning and research are now paused"
echo "ℹ️  The system will continue to work but won't learn new patterns"

# Update dashboard automatically
python3 autonomous_system/scripts/update_dashboard.py
echo "📊 Dashboard updated automatically"

# Stop autonomous processes if running
pkill -f "RUN_FULL_AUTONOMOUS.py" 2>/dev/null || true
