# ADR-002: Use PostgreSQL with pgvector for Database and Vector Search

**Date:** 2025-08-15  
**Status:** `Accepted`  
**Deciders:** Backend Team

---

## Context

Bizify needs a primary relational database to store users, subscriptions, ideas, businesses, and AI chat history. Additionally, the AI features (semantic search, idea similarity, embedding search) require vector storage and efficient similarity queries.

The key question: use a single database for both relational data and vector search, or split into two separate systems?

## Decision Drivers

- **Operational Simplicity:** Fewer services = lower operational overhead
- **Consistency:** Relational data and vectors in the same ACID transaction boundary
- **Cost:** Managed PostgreSQL is widely available and cheaper than dedicated vector DBs
- **AI Features:** Embedding search for ideas, semantic similarity, RAG pipelines

## Considered Options

| Option | Description |
|--------|-------------|
| **PostgreSQL + pgvector** | Single DB with native vector extension |
| PostgreSQL + Pinecone | Relational DB + dedicated managed vector DB |
| PostgreSQL + Weaviate | Relational DB + self-hosted vector DB |
| MongoDB Atlas + Vector | Document DB with built-in vector search |

## Decision Outcome

**Chosen option:** PostgreSQL 16 with `pgvector` extension, because it consolidates relational and vector data in one ACID-compliant system without requiring a second managed service.

### Positive Consequences

- Single connection pool, single backup strategy, single restore point
- Vectors live in the same transaction as the entities they describe (no sync lag)
- `pgvector` supports IVFFlat and HNSW indexes for ANN (Approximate Nearest Neighbor) queries
- SQLAlchemy 2.0 supports `Vector` column type via `pgvector` Python package
- Alembic migrations cover vector column schema changes

### Negative Consequences / Trade-offs

- `pgvector` at high scale (>10M vectors) may be slower than Pinecone/Weaviate
- Requires PostgreSQL 14+ with the `pgvector` extension installed
- HNSW indexing is memory-intensive for very large embedding dimensions

## Migration Path

If vector scale exceeds pgvector capabilities (>10M vectors, sub-10ms P99 requirement), migrate to dedicated Pinecone with async sync via an event-driven pipeline. The `embedding_service.py` interface abstracts the storage backend.

## Links

- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [ADR-001](./001-fastapi-framework.md) — Framework choice
- [embedding_service.py](file:///Users/abdallahabdelrhimantar/Desktop/p7/app/services/ai/embedding_service.py)
