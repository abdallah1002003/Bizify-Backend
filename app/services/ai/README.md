# AI Agent Development Environment 🤖🧠

Welcome. This environment supports development of AI agents for the **Idea-Spark777** ecosystem.

## 🏗️ Architectural Overview

The AI domain is centralized in `app/services/ai/ai_service.py` (The AI Master Service). It handles:
- **Agent Templating**: Registration of new agent definitions.
- **Run Orchestration**: Managing the lifecycle of agent executions (Pending -> Running -> Success/Failed).
- **Validation Loops**: Capturing agent critiques and confidence scores.
- **Embedding Integration**: Handling vectorization of business context.

## 🧬 Development Protocol: Supreme Agents

To build a new agent, inherit from the `BaseAgent` class (found in `app/services/ai/base_agent.py`).

### Key Interfaces
1. **Context Injection**: Agents can retrieve business/idea context directly from the database using provided services.
2. **Telemetry**: Agent actions should be logged via `BaseAgent.log_telemetry`.

## 🛠️ Tools Available
- **Master Metrics**: Access to `IdeaMetric` and `Usage` data for data-driven agent decisions.

## 🚀 Getting Started
1. Review `test_supreme_logic.py` for examples of how to initiate agent runs.
2. Implement your logic in a new module within `app/services/ai/agents/`.
3. Register your agent via the `ai_service.create_agent` method.

## 🔌 Current Runtime (Prepared for AI Expert)

The backend is wired with a pluggable runtime in `provider_runtime.py`:

- `AI_PROVIDER=mock` keeps deterministic local behavior for tests and offline dev.
- `AI_PROVIDER=openai` enables live calls for chat execution and embeddings.
- `execute_agent_run_sync` still keeps the same lifecycle and validation logging.
- Embeddings are always normalized to 1536 dimensions to match `pgvector`.

### Handoff Points for Expert Integration

1. If you keep OpenAI runtime, tune prompts/models in `provider_runtime.py`.
2. Move sync execution to queue/background worker for production load.
3. Keep DB writes through existing service methods so billing/validation logs remain consistent.
