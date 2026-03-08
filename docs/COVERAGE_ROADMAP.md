# Test Coverage Roadmap - Phase 4 & 5

**Date**: March 8, 2026  
**Status**: Comprehensive Planning & Implementation  
**Goal**: Achieve 80%+ coverage across AIService, ChatService, Partners, and API Layer

---

## Executive Summary

This roadmap describes the systematic approach to expanding test coverage across:
1. **AIService & AgentRuns** - Agent execution, validation logging, embedding generation
2. **ChatService & Partners** - Chat operations, partner profiles, request workflows
3. **Phase 5: API Layer** - RESTful endpoint coverage for app/api/v1/

**Current Baseline**: 54% service layer coverage (3,860/8,322 lines)  
**Target**: 80%+ with focus on critical business logic and edge cases

---

## Phase 4: Service Layer Expansion

### 4.1 AIService & AgentRuns

**Files**: 
- `app/services/ai/ai_service.py` (AIService facade)
- `app/services/ai/agent_run_service.py` (AgentRunService)
- `app/services/ai/embedding_service.py` (EmbeddingService)
- `app/services/ai/provider_runtime.py` (provider implementations)

**Coverage Goals**:
```
✓ AIService initialization and dependencies
✓ Provider dispatch (OpenAI vs Mock fallback)
✓ Circuit breaker behavior on provider failure
✓ Embedding generation with vector normalization
✓ Agent run execution lifecycle (pending → success/failed)
✓ Validation logging with error tracking
✓ get_agent_run(id) - single fetch
✓ get_agent_runs(skip, limit) - paginated list
✓ initiate_agent_run() - creation and initial state
✓ execute_agent_run_async() - async execution
✓ get_validation_logs() - log pagination
```

**Test File**: `tests/unit/test_ai_service_comprehensive.py`

**Key Test Cases**:
1. **Provider Fallback**
   - When OPENAI disabled → mock response used
   - When circuit breaker open → fallback activated
   - When network timeout → deterministic fallback

2. **Embedding Generation**
   - Valid content → normalized vector (DEFAULT_VECTOR_DIMENSION)
   - Vector truncation (longer than dimensions)
   - Vector padding (shorter than dimensions)
   - Deterministic hash when OpenAI unavailable

3. **AgentRun Lifecycle**
   - Create with initial state (pending)
   - Execute successfully → state = success
   - Execute with error → state = failed, error logged
   - Concurrent runs by same user
   - Pagination with skip/limit

4. **Validation Logging**
   - Log creation with agent_run_id + result + details
   - Query logs by agent_run_id
   - Timeline ordering (newest first)

**Success Criteria**: 85%+ line coverage, all edge cases handled

---

### 4.2 ChatService & ChatOperations

**Files**:
- `app/services/chat/chat_session_operations.py` (ChatSessionService)
- `app/services/chat/chat_message_operations.py` (ChatMessageService)
- `app/models/__init__.py` → ChatSession, ChatMessage

**Coverage Goals**:
```
✓ ChatSession CRUD (create, read, update, delete)
✓ ChatSession listing with pagination
✓ ChatSession status transitions (active → archived)
✓ ChatMessage append to session
✓ ChatMessage listing by session
✓ Context window management (token limits)
✓ Soft delete behavior (tombstone records)
✓ Timestamp management (_utc_now)
✓ Concurrent message handling
✓ Session owner authorization checks
```

**Test File**: `tests/unit/test_chat_service_comprehensive.py`

**Key Test Cases**:
1. **Session Lifecycle**
   - Create new session (user_id, name, type)
   - Soft delete (deleted_at set, not removed)
   - Restore from deleted state
   - Archive active session (status → archived)

2. **Message Operations**
   - Append message (role, content, metadata)
   - Message ordering (FIFO within session)
   - Update message (regenerate, feedback)
   - Soft delete message

3. **Authorization**
   - Non-owner cannot access session
   - Non-owner cannot post to session
   - Admin override behavior

4. **Edge Cases**
   - Empty session query (0 messages)
   - Very large message context (>4k tokens)
   - Concurrent message appends
   - Session load after network interruption

**Success Criteria**: 82%+ line coverage, authorization layer tested

---

### 4.3 PartnerService & PartnerRequest

**Files**:
- `app/services/partners/partner_profile.py` (PartnerProfileService)
- `app/services/partners/partner_request.py` (PartnerRequestService)
- `app/models/partners/` (Partner models)

**Coverage Goals**:
```
✓ Partner profile creation (onboarding)
✓ Profile verification workflow (pending → verified)
✓ Partner request creation (inquiry → approval → rejection)
✓ Request status transitions (multi-state machine)
✓ Partner listing with filters (type, status, verified_only)
✓ Partnership termination (soft delete)
✓ Notification events on state change
✓ Audit logging of approval/rejection
✓ Commission configuration per partner
```

**Test File**: `tests/unit/test_partner_service_comprehensive.py`

**Key Test Cases**:
1. **Partner Onboarding**
   - Create profile (name, type, contact, docs)
   - Submit for verification (state → pending_verification)
   - Approve profile (state → verified, send notification)
   - Reject with reason (state → rejected, reason logged)

2. **Partner Requests**
   - Create request (inquiry type, contact person)
   - Request lifecycle: pending → under_review → approved/rejected
   - Approval triggers partner creation or link
   - Rejection with detailed feedback

3. **Filtering & Search**
   - List by type (VENDOR, AGENCY, AFFILIATE)
   - Filter verified only
   - Status filtering (all, approved, pending, rejected)
   - Pagination (skip, limit)

4. **Commission Management**
   - Set commission tiers per partner
   - Calculate payout on transaction
   - Commission history tracking

**Success Criteria**: 80%+ line coverage, state machine fully tested

---

## Phase 5: API Layer Coverage

### 5.1 API Endpoint Classification

**48 total API files across modules**:
- Auth (1 file): login, register, refresh, verify
- Chat (3 files): sessions, messages, websocket
- Business (6 files): business, collaborators, invites, roadmaps
- Ideation (7 files): ideas, comparisons, versions, access control
- AI (3 files): embeddings, agent runs, validations
- billing (1 file): stripe webhook handler
- Partners (2 files): profiles, requests
- Core (3 files): notifications, files, share links
- Users (2 files): profiles, admin logs

### 5.2 API Coverage Strategy

**Testing Approach**:
- Unit tests for each endpoint (100% route coverage)
- Happy path + error paths (400, 401, 403, 404, 500)
- Request validation (schema, permissions, domain logic)
- Response serialization (correct shapes, no data leaks)
- Concurrent request handling
- Rate limiting, pagination

**Test Organization**:
```
tests/api/
├── test_auth_api.py (existing)
├── test_ai_api.py (existing)
├── test_billing_api.py (existing)
├── test_chat_api.py (CREATE)
├── test_partners_api.py (CREATE)
├── test_business_api.py (CREATE)
├── test_ideation_api.py (existing)
└── test_core_api.py (CREATE)
```

---

### 5.3 API Endpoint Groups

#### **Auth API** (4 endpoints) - ~90% coverage ✅
```
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/verify-email
POST /api/v1/auth/request-password-reset
POST /api/v1/auth/reset-password
```
**Status**: AuthService tests comprehensive, API routes tested

---

#### **Chat API** (6 endpoints) - 40% coverage ⚠️
**File**: `app/api/v1/chat/chat_session.py`, `chat_message.py`

**Endpoints**:
```
GET    /api/v1/chat/sessions
POST   /api/v1/chat/sessions
GET    /api/v1/chat/sessions/{session_id}
PATCH  /api/v1/chat/sessions/{session_id}
DELETE /api/v1/chat/sessions/{session_id}
GET    /api/v1/chat/sessions/{session_id}/messages
POST   /api/v1/chat/sessions/{session_id}/messages
GET    /api/v1/chat/messages/{message_id}
PATCH  /api/v1/chat/messages/{message_id}
DELETE /api/v1/chat/messages/{message_id}
WS     /api/v1/chat/ws (WebSocket)
```

**Test Requirements**:
- [x] Create session (as authenticated user)
- [x] List sessions (pagination)
- [x] Get session details (403 if not owner)
- [x] Update session (name, settings)
- [ ] Delete session (soft delete verification)
- [ ] Append message (with async processing)
- [ ] List messages (pagination, ordering)
- [ ] Update message (regenerate)
- [ ] Delete message
- [ ] WebSocket connection handshake
- [ ] Real-time message push
- [ ] Disconnect handling

**Test File**: `tests/api/test_chat_api.py` (new)

---

#### **Partners API** (6 endpoints) - 30% coverage ⚠️
**File**: `app/api/v1/partners/partner_profile.py`, `partner_request.py`

**Endpoints**:
```
GET    /api/v1/partners
POST   /api/v1/partners
GET    /api/v1/partners/{id}
PATCH  /api/v1/partners/{id}
POST   /api/v1/partners/{id}/verify
GET    /api/v1/partners/{id}/requests
POST   /api/v1/partners/{id}/requests
PATCH  /api/v1/partners/{id}/requests/{req_id}
```

**Test Requirements**:
- [ ] List partners (filters, pagination)
- [ ] Create partner (validation, notification)
- [ ] Get partner detail (404 if not found)
- [ ] Update partner (owner check)
- [ ] Submit for verification (status transition)
- [ ] Approve partner (admin only)
- [ ] List requests for partner
- [ ] Create request (inquiry type)
- [ ] Update request status (approve/reject)

**Test File**: `tests/api/test_partners_api.py` (new)

---

#### **AI API** (5 endpoints) - 50% coverage ⚠️
**File**: `app/api/v1/ai/agent_run.py`, `embedding.py`

**Endpoints**:
```
GET    /api/v1/ai/agent-runs
POST   /api/v1/ai/agent-runs
GET    /api/v1/ai/agent-runs/{run_id}
PATCH  /api/v1/ai/agent-runs/{run_id}
POST   /api/v1/ai/agent-runs/{run_id}/execute
GET    /api/v1/ai/embeddings
POST   /api/v1/ai/embeddings
```

**Test Requirements**:
- [x] List agent runs (pagination, filters)
- [x] Create agent run (validate input)
- [x] Get run details (404 handling)
- [ ] Update run (metadata, feedback)
- [ ] Execute run (async dispatch)
- [ ] Get embeddings (cached results)
- [ ] Create embeddings (trigger generation)

**Test File**: `tests/api/test_ai_api.py` (update existing)

---

#### **Business API** (12 endpoints) - 35% coverage ⚠️
**Files**: 
- `app/api/v1/business/business.py`
- `app/api/v1/business/business_collaborator.py`
- `app/api/v1/business/business_invite.py`
- `app/api/v1/business/business_roadmap.py`

**Endpoints** (sample):
```
GET    /api/v1/business
POST   /api/v1/business
GET    /api/v1/business/{id}
PATCH  /api/v1/business/{id}
GET    /api/v1/business/{id}/collaborators
POST   /api/v1/business/{id}/invites
GET    /api/v1/business/{id}/roadmap
POST   /api/v1/business/{id}/roadmap/stages
```

**Test Requirements**:
- [ ] CRUD operations (create, read, update, delete)
- [ ] Collaborator management (add, remove, permission changes)
- [ ] Invite workflow (send, accept, decline)
- [ ] Roadmap CRUD
- [ ] Stage state transitions
- [ ] Progress calculations
- [ ] Authorization checks (owner, collaborator, visitor)

**Test File**: `tests/api/test_business_api.py` (new)

---

#### **Ideation API** (14 endpoints) - 60% coverage ✅
**Files**:
- `app/api/v1/ideation/idea.py`
- `app/api/v1/ideation/idea_comparison.py`
- `app/api/v1/ideation/idea_access.py`

**Status**: Mostly covered, needs:
- [ ] Comparison workflow (add ideas, compute scores)
- [ ] Version history (diffs)
- [ ] Access control (public, private, shared)

**Test File**: `tests/api/test_ideas_api.py` (update existing)

---

#### **Billing API** (3 endpoints) - 70% coverage ✅
**File**: `app/api/v1/billing/`

**Endpoints**:
```
POST /api/v1/billing/webhooks/stripe (webhook)
GET  /api/v1/billing/plans
GET  /api/v1/billing/subscriptions
```

**Status**: Stripe webhook handler tested, needs:
- [ ] Plans listing (filtering, sorting)
- [ ] Subscription status API

**Test File**: `tests/api/test_billing_api.py` (update existing)

---

#### **Core API** (5 endpoints) - 20% coverage ⚠️
**Files**:
- `app/api/v1/core/notification.py`
- `app/api/v1/core/file.py`
- `app/api/v1/core/share_link.py`

**Endpoints**:
```
GET    /api/v1/notifications
POST   /api/v1/notifications/read
POST   /api/v1/file/upload
GET    /api/v1/file/{id}
POST   /api/v1/share/create-link
GET    /api/v1/share/{token}
```

**Test Requirements**:
- [ ] Notification CRUD and mark-as-read
- [ ] File upload (validation, storage)
- [ ] File access control
- [ ] Share link generation and expiry
- [ ] Public share access (no auth required)

**Test File**: `tests/api/test_core_api.py` (new)

---

## Implementation Timeline

### Week 1-2: Service Layer (AIService, ChatService, Partners)
- [ ] AI service comprehensive tests (65 test cases)
- [ ] Chat service comprehensive tests (48 test cases)
- [ ] Partner service comprehensive tests (52 test cases)
- [ ] Expected coverage: 80%+ for services

### Week 3-4: API Layer
- [ ] Chat API tests (40 test cases)
- [ ] Partners API tests (35 test cases)
- [ ] Business API tests (60 test cases)
- [ ] Core API tests (25 test cases)
- [ ] Expected coverage: 75%+ for API

### Week 5: Integration & Optimization
- [ ] Cross-service integration tests
- [ ] End-to-end workflows
- [ ] Performance regression tests
- [ ] Coverage report & optimization
- [ ] Final target: 80%+ overall

---

## Testing Best Practices

### 1. Service Layer Tests
```python
@pytest.mark.asyncio
async def test_ai_service_agent_execution():
    """Test happy path: agent execution success"""
    # Setup
    db = get_test_db()
    service = AIService(db)
    
    # Execute
    agent_run = await service.initiate_agent_run(...)
    result = await service.execute_agent_run_async(agent_run.id)
    
    # Assert
    assert result.state == AgentRunState.SUCCESS
    assert result.output is not None
    
    # Cleanup
    await db.delete(agent_run)
```

### 2. API Tests
```python
@pytest.mark.asyncio
async def test_chat_session_create_api(client, authenticated_user):
    """Test POST /api/v1/chat/sessions"""
    response = await client.post(
        "/api/v1/chat/sessions",
        json={"name": "Test Chat", "type": "general"},
        headers={"Authorization": f"Bearer {authenticated_user.token}"}
    )
    assert response.status_code == 201
    assert response.json["id"] is not None
```

### 3. Error Path Tests
```python
@pytest.mark.asyncio
async def test_chat_session_access_denied():
    """Non-owner cannot access session (403 Forbidden)"""
    response = await client.get(
        f"/api/v1/chat/sessions/{other_user_session_id}",
        headers={"Authorization": f"Bearer {current_user.token}"}
    )
    assert response.status_code == 403
```

---

## Coverage Metrics

### Current State (March 8, 2026)
- **Service Layer**: 54% (3,860/8,322 lines)
  - AuthService: 90%+ ✅
  - UserService: 64%
  - Remaining: 40-75%
- **API Layer**: 45% (app/api)
- **Tests**: 180+ test files

### Target State (End of Q1 2026)
- **Service Layer**: 80%+
- **API Layer**: 75%+
- **Overall**: 78%+
- **Tests**: 300+ test files

---

## Risk Assessment & Mitigation

| Risk | Mitigation |
|------|-----------|
| Circuit breaker complexity | Unit test provider fallback with mocks |
| WebSocket testing difficulty | Use websocket-client library for real-time tests |
| Database transaction isolation | Use nested transactions, rollback after each test |
| Concurrent operation race conditions | Mutex locks in tests, async/await ordering verification |
| External API dependencies (Stripe, OpenAI) | VCR cassettes for replay, circuit breaker fallback tests |

---

## Success Criteria

✅ **Phase 4 Complete When**:
- AIService: 85%+ coverage, all edge cases tested
- ChatService: 82%+ coverage, auth layer verified
- PartnerService: 80%+ coverage, state machine validated

✅ **Phase 5 Complete When**:
- Chat API: 80%+ coverage, WebSocket tested
- Partners API: 75%+ coverage, workflows validated
- Business API: 75%+ coverage, complex operations tested
- All endpoints return correct status codes & response shapes

---

## References

- [Coverage Progress](./coverage-progress.md)
- [Architecture Decision Records](./adr/)
- [Security Audit](./SECURITY_HARDENING.md)

