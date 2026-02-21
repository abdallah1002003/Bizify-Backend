#!/usr/bin/env python3
"""
Auto Dashboard Updater
Updates LIVE_DASHBOARD.md automatically based on system state
"""
import sys
from pathlib import Path
from datetime import datetime

# Add .autonomous_system to path
sys.path.insert(0, str(Path.cwd() / ".autonomous_system"))

from core.session_detector import AntigravitySessionDetector
from evolution.pattern_learning import PatternLearningSystem

def get_system_status():
    """Get current system status."""
    detector = AntigravitySessionDetector(Path.cwd())
    learner = PatternLearningSystem(Path.cwd())
    
    is_active = detector.is_antigravity_active()
    stats = learner.get_knowledge_stats()
    
    return {
        'active': is_active,
        'total_patterns': stats['success_patterns'],
        'failure_patterns': stats['failure_patterns'],
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def generate_dashboard(status):
    """Generate dashboard content based on status."""
    
    # Prepare conditional content
    if status['active']:
        status_line = "**Status**: 🟢 **COLLABORATIVE MODE ACTIVE**"
        learning_line = "**Learning**: ✅ **ENABLED** (Antigravity Session Active)"
        mode = "COLLABORATIVE"
        learning_status = "✅ Active"
        research_status = "✅ Enabled"
        autofix_status = "✅ Enabled (with approval)"
        
        cap_learning = "✅ Active"
        cap_research = "✅ Ready"
        cap_analysis = "✅ Active"
        cap_autofix = "✅ Active"
        cap_sync = "✅ Active"
        
        health_detector = "🟢 Active"
        health_learning = "🟢 Active"
        health_research = "🟢 Ready"
        health_autofix = "🟢 Ready"
        health_kb = "🟢 Healthy"
        
        monitor_icon = "✅"
        learn_icon = "✅"
        ready_icon = "✅"
        help_icon = "✅"
        persist_icon = "✅"
        
        learning_note = "✅"
        session_status_text = "🟢 Active"
        health_text = "✅ Fully Operational"
        remember_msg = "I'm here to help! I'll learn from our work together."
        collab_msg = "Working together for the best results!"
    else:
        status_line = "**Status**: ⏸️ **SYSTEM PAUSED**"
        learning_line = "**Learning**: ❌ **DISABLED** (No Active Session)"
        mode = "PAUSED"
        learning_status = "❌ Disabled"
        research_status = "❌ Disabled"
        autofix_status = "✅ Basic (using existing knowledge only)"
        
        cap_learning = "⏸️ Paused"
        cap_research = "⏸️ Paused"
        cap_analysis = "✅ Active"
        cap_autofix = "⚠️ Basic"
        cap_sync = "✅ Active"
        
        health_detector = "🟢 Active"
        health_learning = "⏸️ Paused"
        health_research = "⏸️ Paused"
        health_autofix = "🟡 Basic"
        health_kb = "🟢 Healthy"
        
        monitor_icon = "⏸️"
        learn_icon = "❌"
        ready_icon = "✅"
        help_icon = "⚠️"
        persist_icon = "⚠️"
        
        learning_note = "(paused)"
        session_status_text = "⏸️ Paused"
        health_text = "⚠️ Limited Mode"
        remember_msg = "Start a session to enable learning!"
        collab_msg = "Use start_with_antigravity.sh to begin!"
    
    autofix_desc = "Fixing issues collaboratively" if status['active'] else "Basic fixes only"
    
    dashboard = f"""# 🧠 Autonomous System Live Dashboard

{status_line}  
{learning_line}

---

## 📊 System Metrics

### Knowledge Base
- **Total Patterns**: {status['total_patterns']:,} verified patterns 💎
- **Success Rate**: High confidence learning
- **Growth Strategy**: 🤝 Collaborative with Antigravity

### Current Session
- **Mode**: {mode}
- **Learning**: {learning_status}
- **Web Research**: {research_status}
- **Auto-Fix**: {autofix_status}

---

## 🎯 Active Capabilities

| Capability | Status | Description |
|------------|--------|-------------|
| **Pattern Learning** | {cap_learning} | Learning from interactions |
| **Web Research** | {cap_research} | Can research when needed |
| **Code Analysis** | {cap_analysis} | Analyzing code quality |
| **Auto-Fix** | {cap_autofix} | {autofix_desc} |
| **Knowledge Sync** | {cap_sync} | Syncing with knowledge base |

---

## 🤝 Collaborative Features

### What I'm Doing Now
- {monitor_icon} Monitoring your work
- {learn_icon} Learning from our interactions
- {ready_icon} Ready to assist with any task
- {help_icon} Will help fix errors as they occur
- {persist_icon} Won't stop until task is complete

### How I Help
1. **Error Detection**: I spot issues immediately
2. **Auto-Fix**: I suggest or apply fixes
3. **Learning**: I learn from successful patterns {learning_note}
4. **Persistence**: I stay with you until task completion

---

## 📈 Session Statistics

- **Last Updated**: {status['timestamp']}
- **Session Status**: {session_status_text}
- **Total Knowledge**: {status['total_patterns']:,} patterns
- **System Health**: {health_text}

---

## 🔔 System Health

| Component | Status |
|-----------|--------|
| Session Detector | {health_detector} |
| Pattern Learning | {health_learning} |
| Web Researcher | {health_research} |
| Auto-Fix Engine | {health_autofix} |
| Knowledge Base | {health_kb} |

---

## 💡 Quick Commands

```bash
# Check session status
python3 .autonomous_system/core/session_detector.py check

# Start collaborative session
bash .autonomous_system/scripts/start_with_antigravity.sh

# End session
bash .autonomous_system/scripts/end_antigravity_session.sh

# Update dashboard
python3 .autonomous_system/scripts/update_dashboard.py
```

---

**Last Updated**: {status['timestamp']}  
**System Version**: Collaborative AI + Selective Learning v3.0

> 💡 **Remember**: {remember_msg}  
> 🤝 **Collaboration**: {collab_msg}
"""
    
    return dashboard

def update_dashboard():
    """Update the dashboard file."""
    dashboard_file = Path.cwd() / "LIVE_DASHBOARD.md"
    
    # Get current status
    status = get_system_status()
    
    # Generate new dashboard
    content = generate_dashboard(status)
    
    # Write to file
    dashboard_file.write_text(content)
    
    print(f"✅ Dashboard updated successfully")
    print(f"   Status: {'Active' if status['active'] else 'Paused'}")
    print(f"   Patterns: {status['total_patterns']:,}")
    print(f"   Time: {status['timestamp']}")

if __name__ == "__main__":
    update_dashboard()
