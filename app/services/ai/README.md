# AI Agent Development Environment 🤖🧠

Welcome, AI Expert. This environment has been prepared to "Supreme" standards to support the development of autonomous agents for the **Idea-Spark777** ecosystem.

## 🏗️ Architectural Overview

The AI domain is centralized in `app/services/ai/ai_service.py` (The AI Master Service). It handles:
- **Agent Templating**: Registration of new agent definitions.
- **Run Orchestration**: Managing the lifecycle of agent executions (Pending -> Running -> Success/Failed).
- **Validation Loops**: Capturing agent critiques and confidence scores.
- **Embedding Integration**: Handling vectorization of business context.

## 🧬 Development Protocol: Supreme Agents

To build a new agent, inherit from the `BaseAgent` class (found in `app/services/ai/base_agent.py`).

### Key Interfaces
1. **Bridge Access**: Use the `EvolutionService` to consult the **Master Patterns** (133k+ verified rules) via the `AntigravityBridge`.
2. **Context Injection**: Agents can retrieve business/idea context directly from the database using provided services.
3. **Telemetry**: All agent actions must be logged via `EvolutionService.record_evolution_event` for system-wide learning.

## 🛠️ Tools Available
- **`EvolutionService`**: Your primary link to the `.autonomous_system`.
- **`AntigravityBridge`**: Lower-level communication layer with the autonomous hub.
- **Master Metrics**: Access to `IdeaMetric` and `Usage` data for data-driven agent decisions.

## 🚀 Getting Started
1. Review `test_supreme_logic.py` for examples of how to initiate agent runs.
2. Implement your logic in a new module within `app/services/ai/agents/`.
3. Register your agent via the `ai_service.create_agent` method.

*Perpetual Evolution is the standard. Happy coding.*
