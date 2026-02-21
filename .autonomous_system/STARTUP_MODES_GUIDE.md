# 🎮 System Startup Modes Guide

## 📋 All Available Startup Modes

This guide explains all the different ways you can start and use the autonomous system.

---

## 1️⃣ Collaborative Mode + Learning

**Description:** System works with you and learns from your interactions

**How to Start:**
```bash
bash autonomous_system/scripts/start_with_antigravity.sh
```

**Features:**
- ✅ Pattern learning active
- ✅ Web research available
- ✅ Advanced auto-fix
- ✅ Stays with you until task complete
- ✅ Saves new knowledge

**How to Stop:**
```bash
bash autonomous_system/scripts/end_antigravity_session.sh
```

---

## 2️⃣ Autonomous Mode - No Learning

**Description:** System works in background but without learning

**How to Start:**
```bash
# Simply don't create the session file
# Or stop the current session
bash autonomous_system/scripts/end_antigravity_session.sh
```

**Features:**
- ✅ Uses existing knowledge
- ✅ Basic error fixing
- ✅ Code analysis
- ❌ No new pattern learning
- ❌ No web research

---

## 3️⃣ Full Autonomous System

**Description:** Full activation of all autonomous system components

**How to Start:**
```bash
python3 autonomous_system/scripts/RUN_FULL_AUTONOMOUS.py
```

**Features:**
- ✅ Multiple workers
- ✅ Continuous monitoring
- ✅ Auto-fix
- ✅ Self-improvement
- ⚠️ Requires approval to start

**How to Stop:**
```bash
# Press Ctrl+C or
pkill -f "RUN_FULL_AUTONOMOUS.py"
```

---

## 4️⃣ Learning Only Mode

**Description:** System observes and learns only without modifications

**How to Start:**
```bash
bash autonomous_system/scripts/set_mode_learning.sh
```

**Features:**
- ✅ Learning active
- ✅ Monitoring active
- ❌ No code modifications
- ❌ No auto-fix

---

## 5️⃣ Collaborative Mode (Without Learning)

**Description:** System helps but doesn't learn new patterns

**How to Start:**
```bash
bash autonomous_system/scripts/set_mode_collaborative.sh
# Don't create session file
```

**Features:**
- ✅ Suggests improvements
- ✅ Helps with errors
- ✅ Uses existing knowledge
- ❌ No new learning

---

## 6️⃣ Auto-Fix Mode

**Description:** System automatically fixes everything it finds

**How to Start:**
```bash
bash autonomous_system/scripts/set_mode_autofix.sh
```

**Features:**
- ✅ Automatic detection
- ✅ Automatic fixing
- ✅ Applies learned patterns
- ⚠️ Requires backup

---

## 📊 Comparison Table

| Mode | Learning | Web Research | Auto-Fix | Monitoring |
|------|----------|--------------|----------|------------|
| **Collaborative + Learning** | ✅ | ✅ | ✅ Advanced | ✅ |
| **Autonomous - No Learning** | ❌ | ❌ | ✅ Basic | ✅ |
| **Full Autonomous** | ✅ | ✅ | ✅ | ✅ |
| **Learning Only** | ✅ | ❌ | ❌ | ✅ |
| **Collaborative** | ❌ | ❌ | ✅ | ✅ |
| **Auto-Fix** | ✅ | ❌ | ✅ Auto | ✅ |

---

## 💡 Recommendations

### For Daily Work
**Use:** Collaborative + Learning
```bash
bash autonomous_system/scripts/start_with_antigravity.sh
```

### For Background Monitoring
**Use:** Autonomous - No Learning
```bash
# Just run without session file
```

### For Testing
**Use:** Learning Only
```bash
bash autonomous_system/scripts/set_mode_learning.sh
```

### For Production
**Use:** Auto-Fix Mode (with backup!)
```bash
bash autonomous_system/scripts/set_mode_autofix.sh
```

---

## 🔍 Check Current Status

```bash
# Check if session is active
python3 autonomous_system/core/session_detector.py check

# View dashboard
cat LIVE_DASHBOARD.md
```

---

## ⚙️ Advanced Configuration

### Session Timeout
Default: 5 minutes of inactivity

To change:
```python
# In session_detector.py
SESSION_TIMEOUT = 300  # seconds
```

### Knowledge Base Location
```
autonomous_reports/knowledge/patterns.json
```

---

## 7️⃣ Smart File Search (New!)

**Description:** Quickly find files and context for Antigravity

**How to Use:**
```bash
python3 autonomous_system/scripts/find_files.py "what you are looking for"
```

**Example:**
```bash
python3 autonomous_system/scripts/find_files.py "error handling"
```

**Features:**
- ✅ Finds relevant files instantly
- ✅ Shows related files
- ✅ Identifies tests
- ✅ Checks session status

---

## 8️⃣ Collaborative Coder (AI Partner)

**Description:** Your AI Partner for drafting and reviewing code.

**Commands:**

1. **Draft Code:**
   ```bash
   python3 autonomous_system/scripts/partner.py draft "login function"
   ```

2. **Review Code:**
   ```bash
   python3 autonomous_system/scripts/partner.py review path/to/file.py
   ```

3. **Teach System:**
   ```bash
   python3 autonomous_system/scripts/partner.py teach "login pattern" path/to/file.py
   ```

**Features:**
- ✅ Generates code from project patterns
- ✅ Reviews code for best practices
- ✅ Learns from your corrections

---

## 9️⃣ Recursive Evolution (Self-Improvement) ♾️

**Description:** The system continuously improves its own code.

**Command:**
```bash
python3 autonomous_system/scripts/evolve.py --target autonomous_system --iterations 10
```

**How it works:**
1. **Analyze:** Scans code for weak points.
2. **Draft:** AI Partner writes improved version.
3. **Compare:** Benchmarks new vs old.
4. **Upgrade:** Hot-swaps code if better.

---

## 🆘 Troubleshooting

### Session Not Active
```bash
# Manually create session
touch .antigravity_session_active
```

### Learning Not Working
```bash
# Check session status
python3 autonomous_system/core/session_detector.py check

# Restart session
bash autonomous_system/scripts/start_with_antigravity.sh
```

### System Not Responding
```bash
# Stop all processes
pkill -f "autonomous"

# Restart
bash autonomous_system/scripts/start_with_antigravity.sh
```

---

## 📚 More Information

- **Mode Control Guide:** `autonomous_system/MODE_CONTROL_GUIDE.md`
- **Live Dashboard:** `LIVE_DASHBOARD.md`
- **Knowledge Base:** `autonomous_reports/knowledge/`

---

**Last Updated:** 2026-02-17  
**Version:** 3.0 - Collaborative AI + Selective Learning
