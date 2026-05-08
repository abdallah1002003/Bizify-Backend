# Bizify Database Schema Documentation

This document provides a comprehensive overview of the Bizify database schema, organized by domain. All tables include standard `id` (UUID), `created_at`, and `updated_at` columns unless otherwise specified.

## 1. Core User Management

### `users`
Represents a system user.
- **Fields:** `email`, `password_hash`, `google_id`, `full_name`, `role` (ADMIN, USER, ENTREPRENEUR, MENTOR, SUPPLIER, MANUFACTURER), `is_active`, `is_verified`, `failed_login_attempts`, `locked_until`, `last_activity`, `revoked_at`, `last_password_change`
- **Relationships:** `profile`, `ideas`, `businesses`, `subscriptions`, `payment_methods`, `payments`, `usages`, `notifications`, `notification_settings`, `privacy_settings`, `files`, `partner_profile`, `admin_logs`, `comparisons`, `share_links`, `chat_sessions`, `group_messages`, `verification_codes`

### `user_profiles`
Detailed profile information for a user.
- **Fields:** `user_id`, `bio`, `skills_json`, `guide_status`, `interests_json`, `preferences_json`, `risk_profile_json`, `onboarding_completed`, `background_json`, `personality_json`, `personalization_profile`

### `privacy_settings`
User privacy preferences.
- **Fields:** `user_id`, `visibility` (public, private, team_only), `show_contact_info`

### `account_verifications`
OTP tokens for account verification, password reset, or email change.
- **Fields:** `user_id`, `otp_hash`, `verification_type`, `expires_at`

## 2. Idea & Business Management

### `ideas`
A business idea in the system.
- **Fields:** `owner_id`, `business_id` (optional), `title`, `description`, `status` (DRAFT, VALIDATED, CONVERTED), `ai_score`, `budget`, `skills` (JSON), `feasibility`, `is_score_outdated`, `is_archived`, `archived_at`, `converted_at`
- **Relationships:** `versions`, `metrics`, `experiments`, `share_links`, `chat_sessions`, `comparison_items`

### `businesses`
A validated business built from an idea.
- **Fields:** `idea_id`, `owner_id`, `stage` (EARLY, BUILDING, SCALING), `context_json`, `is_archived`, `archived_at`
- **Relationships:** `groups`, `roadmap`, `partner_requests`, `embeddings`, `chat_sessions`, `share_links`

## 3. Collaboration & Groups

### `groups`
Organizational group within a business.
- **Fields:** `business_id`, `name`, `description`, `default_role`, `is_chat_enabled`
- **Relationships:** `members`, `invites`, `join_requests`, `messages`

### `group_members`
A user's membership and role in a group.
- **Fields:** `group_id`, `user_id`, `role` (OWNER, EDITOR, VIEWER), `status` (ACTIVE, REMOVAL_PENDING), `joined_at`

### `group_invites` & `group_join_requests`
Workflows for adding users to groups.
- **Invites:** `group_id`, `email`, `token`, `role`, `status` (PENDING, ACCEPTED, EXPIRED), `invited_by`, `expires_at`
- **Requests:** `group_id`, `user_id`, `role`, `status` (pending, approved, rejected)

### Association Tables (Many-to-Many)
Control which ideas each member/invite/request has access to within a group.

| Table | Columns | Description |
|---|---|---|
| `group_member_idea_access` | `member_id` → `group_members.id`, `idea_id` → `ideas.id` | Ideas accessible to a specific group member |
| `group_invite_idea_access` | `invite_id` → `group_invites.id`, `idea_id` → `ideas.id` | Ideas pre-granted to an invited user |
| `group_request_idea_access` | `request_id` → `group_join_requests.id`, `idea_id` → `ideas.id` | Ideas requested as part of a join request |

### `group_messages`
Real-time user-to-user chat within a group.
- **Fields:** `group_id`, `sender_id`, `content`

### `share_links`
Public or private shared links for an Idea or Business.
- **Fields:** `idea_id`, `business_id`, `created_by`, `token`, `is_public`, `expires_at`

## 4. Skills & Partners

### `skill_categories` & `predefined_skills` & `user_skills`
Categorized list of skills and what users claim.
- **Categories:** `name`, `description`
- **Predefined Skills:** `name`, `category_id`
- **User Skills:** `user_id`, `skill_name`, `is_custom`, `predefined_skill_id`, `category_id`

### `partner_profiles` & `partner_requests`
Mentor, supplier, or manufacturer profiles and collaboration requests.
- **Profiles:** `user_id`, `partner_type`, `company_name`, `description`, `services_json`, `experience_json`, `documents_json`, `approval_status`, `approved_by`, `approved_at`
- **Requests:** `business_id`, `partner_id`, `requested_by`, `status`

## 5. Roadmap & Guidance

### `business_roadmaps` & `roadmap_stages`
Step-by-step plan for a business.
- **Roadmaps:** `business_id`, `completion_percentage`
- **Stages:** `roadmap_id`, `order_index`, `stage_type`, `status` (LOCKED, ACTIVE, COMPLETED), `output_json`, `completed_at`

### `guidance_stages` & `guidance_concepts`
System-provided guidance content.
- **Stages:** `name`, `description`, `sequence_order`
- **Concepts:** `stage_id`, `title`, `concept_explanation`, `platform_support_explanation`, `sequence_order`, `is_available`

### `feature_concept_mappings` & `user_concept_states`
Connecting platform UI features to concepts and tracking user reading progress.

## 6. AI & Agents

### `agents` & `agent_runs`
AI agents and their execution records.
- **Agents:** `name`, `phase`
- **Runs:** `stage_id`, `agent_id`, `input_data`, `output_data`, `confidence_score`, `status`, `execution_time_ms`

### `embeddings`
Vector embeddings of business context for RAG.
- **Fields:** `business_id`, `agent_id`, `content`, `vector`

### `chat_sessions` & `chat_messages`
Conversations with the AI.
- **Sessions:** `user_id`, `business_id`, `idea_id`, `session_type`, `conversation_summary_json`
- **Messages:** `session_id`, `role` (USER, AI), `content`

### `documents`
Processed files with extracted text for AI.
- **Fields:** `filename`, `content_type`, `extracted_text`, `user_id`

## 7. Idea Analysis & Evaluation

### `idea_versions`
Versioned snapshots of an idea's state.
- **Fields:** `idea_id`, `created_by`, `snapshot_json`

### `idea_metrics`
Numerical metrics tracked over time for an idea.
- **Fields:** `idea_id`, `created_by`, `name`, `value`, `type`, `recorded_at`

### `idea_comparisons` & `comparison_items` & `comparison_metrics`
Grouping ideas to compare them against standard metrics.

### `experiments`
Tests to validate hypotheses for an idea.
- **Fields:** `idea_id`, `created_by`, `hypothesis`, `status`, `result_summary`

## 8. Billing & Resources

### `plans`
Available subscription tiers.
- **Fields:** `name`, `price` (Numeric 10,2), `features_json`, `is_active`

### `subscriptions`
User subscriptions to a plan.
- **Fields:** `user_id`, `plan_id`, `status` (ACTIVE, CANCELED), `start_date`, `end_date`, `paypal_subscription_id`

### `payment_methods`
Saved payment tokens for a user.
- **Fields:** `user_id`, `provider`, `token_ref`, `last4`, `is_default`

### `payments`
Payment transactions (supports PayPal and Paymob).
- **Fields:** `user_id`, `subscription_id`, `payment_method_id`, `amount`, `currency`, `status`, `paypal_order_id`, `paypal_capture_id`, `paymob_order_id`, `paymob_transaction_id`

### `usages`
Tracking resource limits (e.g., AI tokens, storage).
- **Fields:** `user_id`, `resource_type`, `used`, `limit_value`

## 9. Logs & System Tools

### `notifications`
System alerts sent to users.
- **Fields:** `user_id`, `title`, `content`, `message`, `type`, `status` (unread, read, dismissed, archived), `delivery_status` (pending, sent, failed), `retry_count`, `expires_at`
- **Index:** Composite on `(user_id, status, expires_at)` for fast active-notification queries

### `notification_settings`
Per-user notification preferences (1-to-1 with `users`, PK = `user_id`).
- **Fields:** `user_id`, `is_enabled`, `email_enabled`, `sms_enabled`, `push_enabled`, `marketing_enabled`, `team_updates_enabled`, `billing_alerts_enabled`

### `audit_logs`
General record of user actions for compliance.
- **Fields:** `user_id` (nullable), `action`, `details` (JSON), `ip_address`

### `security_logs`
Security-related events (login attempts, lockouts, etc.).
- **Fields:** `user_id` (nullable), `event_type`, `details` (JSON), `ip_address`

### `admin_action_logs`
Audit trail for actions performed by admins.
- **Fields:** `admin_id`, `action_type`, `target_entity`, `target_id`

### `validation_logs`
Output of the AI agent's self-validation step after each run.
- **Fields:** `agent_run_id`, `confidence_score`, `critique_json`, `threshold_passed`

### `export_jobs`
Background jobs for data exports.
- **Fields:** `user_id`, `scope`, `format`, `status`, `storage_path`, `task_id`, `error_details`

### `token_blacklist`
Revoked JWT tokens.

### `files`
User uploaded files (images, attachments).
- **Fields:** `owner_id`, `file_path`, `file_type`, `size`, `uploaded_at`
