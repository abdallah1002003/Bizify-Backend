# Bizify — Background & Real-Time Flows

Bizify utilizes background workers and real-time streaming protocols to keep the main HTTP API responsive and enable interactive collaboration.

---

## 1. Data Export Flow (Background Processing)

Data exports (JSON, PDF, DOCX) can take time. Bizify uses **Celery** and **Redis** to run these asynchronously.

```mermaid
sequenceDiagram
    participant User
    participant API as Export API
    participant DB as Database
    participant Celery as Celery Worker
    participant Files as storage/exports

    User->>API: POST /api/v1/export/
    API->>DB: create export_jobs row PENDING
    API->>Celery: queue process_export_task(job_id)
    API->>DB: store Celery task_id
    Celery->>DB: set status PROCESSING
    Celery->>DB: collect profile, skills, ideas
    Celery->>Files: write JSON, PDF, or DOCX
    Celery->>DB: set status COMPLETED and storage_path
    User->>API: GET /api/v1/export/{job_id}/download
    API->>Files: stream completed file
```

---

## 2. Group Chat Flow (WebSockets)

Group chat provides low-latency, real-time collaboration using FastAPI's **WebSocket** implementation backed by an in-memory `GroupConnectionManager`.

```mermaid
sequenceDiagram
    participant Client
    participant WS as /groups/{group_id}/ws
    participant Auth as JWT decoder
    participant GroupSvc as GroupService
    participant MsgSvc as GroupMessageService
    participant Manager as GroupConnectionManager
    participant DB as Database

    Client->>WS: connect with token query param
    WS->>Auth: decode JWT
    WS->>GroupSvc: validate user can access chat-enabled group
    WS->>Manager: register socket by group_id/user_id
    Client->>WS: send text
    WS->>MsgSvc: create_message
    MsgSvc->>DB: persist group_messages row
    WS->>Manager: broadcast JSON payload
    Manager-->>Client: message event
```

---

## 3. Real-Time Notification Flow (SSE)

Instead of bi-directional WebSockets, notifications use **Server-Sent Events (SSE)**, which are easier to implement on the frontend (using `EventSource`) and perfect for one-way server-to-client updates.

```mermaid
sequenceDiagram
    participant Client
    participant SSE as /notifications/stream
    participant Service as NotificationService
    participant Manager as SSE ConnectionManager
    participant DB as Database

    Client->>SSE: open stream with bearer auth
    SSE->>Manager: create queue for current user
    Service->>DB: create notifications row
    Service->>Manager: push notification payload
    Manager-->>SSE: queue event
    SSE-->>Client: data: JSON
```

---

## 4. External AI Pipeline Flow (Polling)

Integration with the Bizify AI engine involves triggering a remote process and polling for results until completion.

```mermaid
sequenceDiagram
    participant User
    participant API as /api/v1/ai
    participant Profile as UserProfile/UserSkill data
    participant Pipeline as External AI Pipeline
    participant DB as Database

    User->>API: POST /ai/analyze
    API->>Profile: load background_json, personality_json, user_skills
    API->>Pipeline: send normalized user_profile, career_profile, skills
    Pipeline-->>API: analysis trigger response
    User->>API: GET /ai/analyze/status
    API->>Pipeline: poll status by user_id
    User->>API: GET /ai/analyze/results
    API->>Pipeline: fetch profile, problems, idea, chat history
    API->>DB: store results in personalization_profile
```
