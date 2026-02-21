#!/bin/bash

# 🤖 Start Autonomous AI-to-AI Review System
# AI Critic works on your behalf, communicating with Main AI until perfect

echo "============================================"
echo "🤖 AUTONOMOUS AI-TO-AI REVIEW SYSTEM"
echo "============================================"
echo ""
echo "AI Critic will work ON YOUR BEHALF"
echo "Main AI will do the implementation"
echo "They will communicate until reaching consensus"
echo ""
echo "============================================"
echo ""

# Default task
TASK="${1:-Generate all missing unit tests and ensure perfect quality}"

echo "📋 Task: $TASK"
echo ""
echo "Starting autonomous review..."
echo ""

# Run the autonomous system
python3 RUN_AI_AGENT.py \
  --task "$TASK" \
  --max-iterations 10

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "============================================"
    echo "✅ SUCCESS: Consensus reached!"
    echo "✅ AI Critic approved the work"
    echo "✅ Your request is complete"
    echo "============================================"
else
    echo ""
    echo "============================================"
    echo "⚠️  No consensus reached"
    echo "⚠️  Review the reports and try again"
    echo "============================================"
fi
