# Bizify Database Schema (Mermaid ER Diagrams)

## 1. User Domain

```mermaid
erDiagram
    users {
        uuid id PK
        string email UK
        string password_hash
        string google_id UK
        string full_name
        enum role "ENTREPRENEUR | MENTOR | SUPPLIER | MANUFACTURER | ADMIN"
        boolean is_active
        boolean is_verified
        datetime created_at
        datetime updated_at
        int failed_login_attempts
        datetime locked_until
        datetime last_activity
        datetime revoked_at
        datetime last_password_change
    }

    user_profiles {
        uuid id PK
        uuid user_id FK
        text bio
        json skills_json
        json questionnaire_json
        enum guide_status "NOT_STARTED | COMPLETED | POSTPONED | SKIPPED"
        boolean onboarding_completed
        datetime updated_at
    }

    account_verifications {
        uuid id PK
        uuid user_id FK
        string otp_hash
        enum verification_type "ACCOUNT_VERIFICATION | PASSWORD_RESET | EMAIL_CHANGE"
        datetime expires_at
        datetime created_at
    }

    token_blacklist {
        string token PK
        datetime blacklisted_at
    }

    users ||--o| user_profiles : "1:1"
    users ||--o{ account_verifications : "1:N"
```

## 2. Business Domain

```mermaid
erDiagram
    businesses {
        uuid id PK
        uuid idea_id FK "nullable"
        uuid owner_id FK
        enum stage "EARLY | BUILDING | SCALING"
        json context_json
        boolean is_archived
        datetime archived_at
        datetime created_at
        datetime updated_at
    }

    ideas {
        uuid id PK
        uuid owner_id FK
        uuid business_id FK "nullable"
        string title
        text description
        enum status "DRAFT | VALIDATED | CONVERTED"
        float ai_score
        float budget
        json skills
        float feasibility
        boolean is_score_outdated
        boolean is_archived
        datetime archived_at
        datetime created_at
        datetime updated_at
        datetime converted_at
    }

    partner_profiles {
        uuid id PK
        uuid user_id FK
        enum partner_type "MENTOR | SUPPLIER | MANUFACTURER"
        string company_name
        text description
        json services_json
        json experience_json
        json documents_json
        enum approval_status "PENDING | APPROVED | REJECTED"
        uuid approved_by FK
        datetime approved_at
        datetime created_at
    }

    partner_requests {
        uuid id PK
        uuid business_id FK
        uuid partner_id FK
        uuid requested_by FK
        enum status "PENDING | ACCEPTED | REJECTED"
        datetime created_at
    }

    users ||--o{ businesses : "owner_id"
    users ||--o{ ideas : "owner_id"
    users ||--o| partner_profiles : "user_id"
    businesses ||--o{ partner_requests : "business_id"
    partner_profiles ||--o{ partner_requests : "partner_id"
    businesses |o--o| ideas : "conversion"
    ideas |o--o| businesses : "belongs_to"
```

## 3. Group Domain

```mermaid
erDiagram
    groups {
        uuid id PK
        uuid business_id FK
        string name
        string description
        enum default_role "VIEWER | EDITOR | OWNER"
        boolean is_chat_enabled
        datetime created_at
        datetime updated_at
    }

    group_members {
        uuid id PK
        uuid group_id FK
        uuid user_id FK
        enum role "VIEWER | EDITOR | OWNER"
        enum status "ACTIVE | REMOVAL_PENDING"
        datetime joined_at
    }

    group_invites {
        uuid id PK
        uuid group_id FK
        string email
        string token UK
        enum role "VIEWER | EDITOR | OWNER"
        enum status "PENDING | ACCEPTED | EXPIRED"
        uuid invited_by FK
        datetime expires_at
        datetime created_at
    }

    group_join_requests {
        uuid id PK
        uuid group_id FK
        uuid user_id FK
        enum role "VIEWER | EDITOR | OWNER"
        enum status "PENDING | APPROVED | REJECTED"
        datetime created_at
        datetime updated_at
    }

    group_messages {
        uuid id PK
        uuid group_id FK
        uuid sender_id FK
        text content
        datetime created_at
    }

    businesses ||--o| groups : "1:1"
    groups ||--o{ group_members : "1:N"
    groups ||--o{ group_invites : "1:N"
    groups ||--o{ group_join_requests : "1:N"
    groups ||--o{ group_messages : "1:N"
    users ||--o{ group_members : "user_id"
    users ||--o{ group_messages : "sender_id"
```

## 4. Subscription & Billing Domain

```mermaid
erDiagram
    plans {
        uuid id PK
        string name
        numeric price
        json features_json
        boolean is_active
    }

    subscriptions {
        uuid id PK
        uuid user_id FK
        uuid plan_id FK
        enum status "ACTIVE | CANCELED"
        datetime start_date
        datetime end_date
        string paypal_subscription_id
    }

    payments {
        uuid id PK
        uuid user_id FK
        uuid subscription_id FK "nullable"
        uuid payment_method_id FK "nullable"
        numeric amount
        string currency
        string status
        string paypal_order_id
        string paypal_capture_id
        string paymob_order_id
        string paymob_transaction_id
        datetime created_at
    }

    payment_methods {
        uuid id PK
        uuid user_id FK
        string provider
        string token_ref
        string last4
        boolean is_default
        datetime created_at
    }

    plans ||--o{ subscriptions : "1:N"
    users ||--o{ subscriptions : "1:N"
    users ||--o{ payments : "1:N"
    users ||--o{ payment_methods : "1:N"
    subscriptions ||--o{ payments : "1:N"
    payment_methods ||--o{ payments : "1:N"
```

## 5. AI / Roadmap Domain

```mermaid
erDiagram
    business_roadmaps {
        uuid id PK
        uuid business_id FK
        float completion_percentage
        datetime created_at
    }

    roadmap_stages {
        uuid id PK
        uuid roadmap_id FK
        int order_index
        enum stage_type "READINESS | RESEARCH | STRATEGY | MARKET | FUNCTIONS | ECONOMICS | LEGAL | MVP | BRANDING | GTM | OPERATIONS"
        enum status "LOCKED | ACTIVE | COMPLETED"
        json output_json
        datetime completed_at
    }

    agents {
        uuid id PK
        string name
        string phase
    }

    agent_runs {
        uuid id PK
        enum ai_type "BUSINESS_ROADMAP | ROADMAP_STAGE | CHAT_SESSION | ..."
        uuid roadmap_id FK "nullable"
        uuid stage_id FK "nullable"
        uuid chat_session_id FK "nullable"
        uuid chat_message_id FK "nullable"
        uuid idea_id FK "nullable"
        uuid idea_metric_id FK "nullable"
        uuid idea_comparison_id FK "nullable"
        uuid comparison_item_id FK "nullable"
        uuid comparison_metric_id FK "nullable"
        uuid experiment_id FK "nullable"
        uuid agent_id FK "nullable"
        json input_data
        json output_data
        float confidence_score
        enum status "SUCCESS | FAILED | WARNING"
        int execution_time_ms
        json critique_json
        boolean threshold_passed
        datetime created_at
    }

    chat_sessions {
        uuid id PK
        uuid user_id FK
        uuid business_id FK "nullable"
        uuid idea_id FK "nullable"
        enum session_type "IDEA_CHAT | BUSINESS_CHAT | STAGE_CHAT | GENERAL"
        json conversation_summary_json
        datetime created_at
    }

    chat_messages {
        uuid id PK
        uuid session_id FK
        enum role "USER | AI"
        text content
        datetime created_at
    }

    businesses ||--o| business_roadmaps : "1:1"
    business_roadmaps ||--o{ roadmap_stages : "1:N"
    business_roadmaps ||--o{ agent_runs : "1:N"
    roadmap_stages ||--o{ agent_runs : "1:N"
    agents ||--o{ agent_runs : "1:N"
    chat_sessions ||--o{ chat_messages : "1:N"
    chat_sessions ||--o{ agent_runs : "1:N"
    chat_messages ||--o{ agent_runs : "1:N"
```

## 6. Notifications & Settings Domain

```mermaid
erDiagram
    notifications {
        uuid id PK
        uuid user_id FK
        string title
        text content
        text message
        string type
        enum status "UNREAD | READ | DISMISSED | ARCHIVED"
        enum delivery_status "PENDING | SENT | FAILED"
        int retry_count
        datetime expires_at
        datetime created_at
    }

    notification_settings {
        uuid user_id PK, FK
        boolean is_enabled
        boolean email_enabled
        boolean sms_enabled
        boolean push_enabled
        boolean marketing_enabled
        boolean team_updates_enabled
        boolean billing_alerts_enabled
    }

    privacy_settings {
        uuid user_id PK, FK
        enum visibility "PUBLIC | PRIVATE | TEAM_ONLY"
        boolean show_contact_info
    }

    users ||--o{ notifications : "1:N"
    users ||--o| notification_settings : "1:1"
    users ||--o| privacy_settings : "1:1"
```

## 7. Full Entity Relationship Diagram

```mermaid
erDiagram
    users ||--o| user_profiles : has
    users ||--o{ account_verifications : has
    users ||--o| partner_profiles : has
    users ||--o{ businesses : owns
    users ||--o{ ideas : owns
    users ||--o{ subscriptions : has
    users ||--o{ payment_methods : has
    users ||--o{ payments : makes
    users ||--o{ notifications : receives
    users ||--o| notification_settings : configures
    users ||--o| privacy_settings : configures
    users ||--o{ group_members : joins
    users ||--o{ group_messages : sends

    businesses ||--o{ ideas : contains
    businesses ||--o| groups : has_one
    businesses ||--o| business_roadmaps : has_roadmap
    businesses ||--o{ partner_requests : receives

    groups ||--o{ group_members : has
    groups ||--o{ group_invites : has
    groups ||--o{ group_join_requests : has
    groups ||--o{ group_messages : has

    ideas ||--o{ idea_versions : versions
    ideas ||--o{ idea_metrics : metrics
    ideas ||--o{ experiments : experiments
    ideas ||--o{ chat_sessions : chats

    plans ||--o{ subscriptions : priced_by
    subscriptions ||--o{ payments : billed_by
    payment_methods ||--o{ payments : used_in

    business_roadmaps ||--o{ roadmap_stages : consists_of
    business_roadmaps ||--o{ agent_runs : tracked_by
    roadmap_stages ||--o{ agent_runs : processed_by
    agents ||--o{ agent_runs : executed_by

    chat_sessions ||--o{ chat_messages : has
    chat_sessions ||--o{ agent_runs : triggers

    partner_profiles ||--o{ partner_requests : receives

    users {
        uuid id PK
        string email
        string full_name
        enum role
    }
```

## Enum Reference

```mermaid
mindmap
  root((Enums))
    UserRole
      ADMIN
      ENTREPRENEUR
      MENTOR
      SUPPLIER
      MANUFACTURER
    GuideStatus
      NOT_STARTED
      COMPLETED
      POSTPONED
      SKIPPED
    PartnerType
      MENTOR
      SUPPLIER
      MANUFACTURER
    GroupRole
      OWNER
      EDITOR
      VIEWER
    IdeaStatus
      DRAFT
      VALIDATED
      CONVERTED
    StageType
      READINESS
      RESEARCH
      STRATEGY
      MARKET
      FUNCTIONS
      ECONOMICS
      MVP
      BRANDING
      GTM
      OPERATIONS
    NotificationStatus
      UNREAD
      READ
      ARCHIVED
    SubscriptionStatus
      ACTIVE
      CANCELED
```

## Table List

| # | Table | Domain |
|---|-------|--------|
| 1 | `users` | User |
| 2 | `user_profiles` | User |
| 3 | `account_verifications` | User |
| 4 | `token_blacklist` | User |
| 5 | `businesses` | Business |
| 6 | `ideas` | Business |
| 7 | `idea_versions` | AI |
| 8 | `idea_metrics` | AI |
| 9 | `experiments` | AI |
| 10 | `partner_profiles` | Business |
| 11 | `partner_requests` | Business |
| 12 | `groups` | Group |
| 13 | `group_members` | Group |
| 14 | `group_member_idea_access` | Group (assoc) |
| 15 | `group_invites` | Group |
| 16 | `group_invite_idea_access` | Group (assoc) |
| 17 | `group_join_requests` | Group |
| 18 | `group_request_idea_access` | Group (assoc) |
| 19 | `group_messages` | Group |
| 20 | `plans` | Billing |
| 21 | `subscriptions` | Billing |
| 22 | `payments` | Billing |
| 23 | `payment_methods` | Billing |
| 24 | `business_roadmaps` | AI |
| 25 | `roadmap_stages` | AI |
| 26 | `agents` | AI |
| 27 | `agent_runs` | AI |
| 28 | `chat_sessions` | AI |
| 29 | `chat_messages` | AI |
| 30 | `idea_comparisons` | AI |
| 31 | `comparison_items` | AI |
| 32 | `comparison_metrics` | AI |
| 33 | `embeddings` | AI |
| 34 | `documents` | AI |
| 35 | `notifications` | Notification |
| 36 | `notification_settings` | Notification |
| 37 | `privacy_settings` | Notification |
| 38 | `share_links` | Utility |
| 39 | `export_jobs` | Utility |
| 40 | `files` | Utility |
| 41 | `usages` | Utility |
| 42 | `audit_logs` | Logging |
| 43 | `admin_action_logs` | Logging |
| 44 | `security_logs` | Logging |
