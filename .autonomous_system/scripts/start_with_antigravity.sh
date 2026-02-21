#!/bin/bash
# Start Antigravity Collaborative Session
# Creates session marker and starts autonomous system

echo "🤝 Starting Antigravity Collaborative Session..."

# Create session marker
touch .antigravity_session_active

# Update dashboard automatically
python3 .autonomous_system/scripts/update_dashboard.py

# Build/Update File Index for Smart Search
echo "🔍 Updating Smart Search Index..."
python3 .autonomous_system/ai/file_indexer.py --build --silent
echo "✅ Smart Search Index Updated"

echo "✅ Session marker created"
echo "🚀 Starting autonomous system..."
echo "✅ Ready for collaborative work with learning enabled!"
echo "ℹ️  The system will now learn from patterns and can perform web research"

# Update dashboard automatically
python3 .autonomous_system/scripts/update_dashboard.py
echo "📊 Dashboard updated automatically"

# Optionally start the full autonomous system
python3 .autonomous_system/scripts/RUN_FULL_AUTONOMOUS.py --continuous --interval 60 --force
