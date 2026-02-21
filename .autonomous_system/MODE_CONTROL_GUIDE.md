# 🎛️ Autonomous System Mode Control Guide

Complete guide for controlling and managing the autonomous system.

---

## 📋 Table of Contents

1. [System Modes](#system-modes)
2. [Starting the System](#starting-the-system)
3. [Stopping the System](#stopping-the-system)
4. [Switching Modes](#switching-modes)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)

---

## 🔄 System Modes

### 1. **LEARNING_ONLY Mode** 🎓
- **Description**: System monitors code and learns patterns only, without modification
- **Use Case**: Safe observation mode, perfect for initial setup
- **Auto-Fix**: ❌ Disabled
- **Learning**: ✅ Enabled

### 2. **AUTO_FIX Mode** 🤖
- **Description**: System detects problems and fixes them automatically
- **Use Case**: Active development with automated improvements
- **Auto-Fix**: ✅ Enabled
- **Learning**: ✅ Enabled

### 3. **COLLABORATIVE Mode** 🤝
- **Description**: System collaborates with you to improve code
- **Use Case**: Interactive development with AI assistance
- **Auto-Fix**: ✅ Enabled (with approval)
- **Learning**: ✅ Enabled

---

## 🎓 Selective Learning

**NEW FEATURE**: The autonomous system now learns **only** when working collaboratively with Antigravity.

### When Learning is Active ✅
- During Antigravity collaborative sessions
- When `.antigravity_session_active` file exists
- Pattern learning is enabled
- Web research is enabled (if requested)

### When Learning is Paused ⏸️
- During autonomous background operation
- When no Antigravity session is active
- System uses existing knowledge only
- No new patterns are saved

### Starting a Learning Session

```bash
# Method 1: Using script (recommended)
bash autonomous_system/scripts/start_with_antigravity.sh

# Method 2: Manual
touch .antigravity_session_active
```

### Ending a Learning Session

```bash
# Method 1: Using script (recommended)
bash autonomous_system/scripts/end_antigravity_session.sh

# Method 2: Manual
rm .antigravity_session_active
```

### Checking Session Status

```bash
python3 autonomous_system/core/session_detector.py check
```

---

## 🚀 Starting the System

### Method 1: Full System Start (Recommended)

```bash
# Start the complete autonomous system
cd /Users/abdallahabdelrhimantar/Desktop/p7
python3 autonomous_system/scripts/RUN_FULL_AUTONOMOUS.py
```

### Method 2: Worker Orchestrator Only

```bash
# Start just the worker orchestrator
python3 autonomous_system/core/worker_orchestrator.py
```

### Method 3: Individual Components

```bash
# Start auto-fix engine
python3 autonomous_system/core/auto_fix_engine.py --project-root .

# Start pattern learning
python3 autonomous_system/core/pattern_learning_system.py
```

---

## 🛑 Stopping the System

### Method 1: Graceful Shutdown (Recommended)

```bash
# Find all autonomous processes
ps aux | grep -E "worker|orchestrator|autonomous" | grep -v grep

# Kill gracefully (replace PID with actual process IDs)
kill -TERM <PID>

# Or kill all at once
pkill -f "worker"
pkill -f "orchestrator"
```

### Method 2: Force Stop

```bash
# Force kill all autonomous processes
pkill -9 -f "autonomous_system"
pkill -9 -f "worker"
pkill -9 -f "orchestrator"
```

### Method 3: Stop Script (Create this)

```bash
# Create stop script
cat > stop_autonomous.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping Autonomous System..."

# Find and kill all workers
pkill -TERM -f "worker"

# Find and kill orchestrator
pkill -TERM -f "orchestrator"

# Wait for graceful shutdown
sleep 2

# Force kill if still running
pkill -9 -f "worker" 2>/dev/null
pkill -9 -f "orchestrator" 2>/dev/null

echo "✅ Autonomous System stopped"
EOF

chmod +x stop_autonomous.sh
./stop_autonomous.sh
```

---

## 🔀 Switching Modes

### Set LEARNING_ONLY Mode

```bash
# Using script
bash autonomous_system/scripts/set_mode_learning.sh

# Using Python
python3 autonomous_system/core/mode_controller.py --set learning --project-root .
```

### Set AUTO_FIX Mode

```bash
# Using script
bash autonomous_system/scripts/set_mode_autofix.sh

# Using Python
python3 autonomous_system/core/mode_controller.py --set autofix --project-root .
```

### Set COLLABORATIVE Mode

```bash
# Using script
bash autonomous_system/scripts/set_mode_collaborative.sh

# Using Python
python3 autonomous_system/core/mode_controller.py --set collaborative --project-root .
```

### Check Current Mode

```bash
python3 autonomous_system/core/mode_controller.py --get
```

---

## 📊 Monitoring

### Check System Status

```bash
# View live dashboard
cat LIVE_DASHBOARD.md

# Check active workers
ps aux | grep -E "worker|orchestrator" | grep -v grep

# Count active processes
ps aux | grep -E "worker|orchestrator" | grep -v grep | wc -l
```

### View Learned Patterns

```bash
# Pretty print learned patterns
cat autonomous_system/knowledge/learned_patterns.json | python3 -m json.tool

# Count patterns
cat autonomous_system/knowledge/learned_patterns.json | python3 -c "import json, sys; print(json.load(sys.stdin)['total_patterns'])"
```

### Monitor Logs

```bash
# Watch system logs (if logging to file)
tail -f autonomous_system/logs/*.log

# Monitor worker activity
watch -n 1 'ps aux | grep worker | grep -v grep'
```

### Check System Health

```bash
# Verify all components
python3 -c "
from pathlib import Path
import json

# Check mode config
mode_file = Path('.autonomous_mode.json')
if mode_file.exists():
    config = json.loads(mode_file.read_text())
    print(f'✅ Mode: {config[\"mode\"]}')
else:
    print('❌ Mode config not found')

# Check learned patterns
patterns_file = Path('autonomous_system/knowledge/learned_patterns.json')
if patterns_file.exists():
    patterns = json.loads(patterns_file.read_text())
    print(f'✅ Patterns: {patterns[\"total_patterns\"]}')
else:
    print('⚠️ No patterns learned yet')
"
```

---

## 🔧 Troubleshooting

### Workers Not Starting

```bash
# Check for errors
python3 autonomous_system/core/worker_orchestrator.py 2>&1 | tee worker_debug.log

# Verify Python environment
python3 --version
which python3
```

### System Stuck

```bash
# Force restart
pkill -9 -f "autonomous"
sleep 2
python3 autonomous_system/scripts/RUN_FULL_AUTONOMOUS.py
```

### Mode Not Changing

```bash
# Manually edit mode config
cat > .autonomous_mode.json << 'EOF'
{
  "mode": "auto_fix",
  "description": "System detects problems and fixes them automatically"
}
EOF
```

### Patterns Not Saving

```bash
# Check directory permissions
ls -la autonomous_system/knowledge/

# Create directory if missing
mkdir -p autonomous_system/knowledge

# Test pattern save
python3 autonomous_system/core/pattern_learning_system.py
```

---

## 📝 Quick Reference Card

| Task | Command |
|------|---------|
| **Start System** | `python3 autonomous_system/scripts/RUN_FULL_AUTONOMOUS.py` |
| **Stop System** | `pkill -TERM -f "worker"; pkill -TERM -f "orchestrator"` |
| **Check Status** | `python3 autonomous_system/core/mode_controller.py --get` |
| **Set Auto-Fix** | `bash autonomous_system/scripts/set_mode_autofix.sh` |
| **Set Learning** | `bash autonomous_system/scripts/set_mode_learning.sh` |
| **View Dashboard** | `cat LIVE_DASHBOARD.md` |
| **View Patterns** | `cat autonomous_system/knowledge/learned_patterns.json \| python3 -m json.tool` |
| **Count Workers** | `ps aux \| grep worker \| grep -v grep \| wc -l` |

---

## 🎯 Best Practices

1. **Always use graceful shutdown** before force killing
2. **Monitor the dashboard** regularly for system health
3. **Start with LEARNING_ONLY** mode for new projects
4. **Switch to AUTO_FIX** once confident in patterns
5. **Check learned patterns** periodically to verify quality
6. **Keep backups** before enabling auto-fix mode

---

## 🆘 Emergency Commands

```bash
# Nuclear option - stop everything
pkill -9 -f "python3.*autonomous"

# Clean restart
pkill -9 -f "autonomous"; sleep 3; python3 autonomous_system/scripts/RUN_FULL_AUTONOMOUS.py

# Reset to defaults
rm .autonomous_mode.json
python3 autonomous_system/core/mode_controller.py --set learning
```

---

**Last Updated**: 2026-02-17  
**System Version**: Collaborative AI + Autonomous System v2.0

> 💡 **Remember**: The system learns and improves with every run!  
> 🤝 **Collaboration**: Best results come from AI + Autonomous working together
