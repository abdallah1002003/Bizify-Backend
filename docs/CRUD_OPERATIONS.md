# Bizify — CRUD Operations Reference

All data access goes through **Repository classes** that extend a shared `BaseRepository`.
Each repository is a singleton instance imported directly (e.g. `idea_repo`, `user_repo`).

---

## Base Repository — Shared Operations

All repositories inherit the following generic operations from `BaseRepository`:

| Method | Signature | Description |
|---|---|---|
| `get` | `(db, id)` | Fetch a single record by primary key |
| `get_multi` | `(db, skip, limit)` | Paginated list of records |
| `create` | `(db, obj_in, commit, refresh)` | Create a new record from a schema or dict |
| `update` | `(db, db_obj, obj_in, commit, refresh)` | Partial update using `exclude_unset` |
| `save` | `(db, db_obj, commit, refresh)` | Persist an already-modified model instance |
| `remove` | `(db, id, commit)` | Delete by primary key |
| `delete_instance` | `(db, db_obj, commit)` | Delete a loaded model instance |

> **Pattern:** `commit=False` uses `db.flush()` to defer the transaction, useful inside multi-step service operations.

---

## 1. Users — `user_repo`

| Method | Description |
|---|---|
| `get_by_email(db, email)` | Fetch user by email address |
| `get_by_google_id(db, google_id)` | Fetch user by Google OAuth ID |
| `get_active_user(db, user_id)` | Fetch active + verified user by ID |
| `get_by_role(db, role)` | List all users with a given role |
| `get_first_by_role(db, role)` | First user matching a role |
| `count_all(db)` | Total number of users |
| `count_inactive(db)` | Total number of inactive users |

---

## 2. User Profiles — `profile_repo`

| Method | Description |
|---|---|
| `get_by_user_id(db, user_id)` | Fetch profile for a user |
| `get_or_create(db, user_id)` | Fetch or lazily create a blank default profile (upsert) |

---

## 3. Ideas — `idea_repo`

| Method | Description |
|---|---|
| `get_by_owner(db, user_id)` | All ideas owned by a user |
| `get_by_business(db, business_id)` | All ideas linked to a business |
| `get_by_ids_in_business(db, idea_ids, business_id)` | Fetch specific ideas scoped to a business boundary |
| `count_all(db)` | Total idea count |
| `mark_scores_outdated(db, owner_id)` | Bulk-flag all of a user's ideas for AI score recalculation |

---

## 4. Groups — `group_repo`

### Group Queries

| Method | Description |
|---|---|
| `get_by_id(db, group_id)` | Fetch group by ID |
| `get_by_business_id(db, business_id)` | All groups belonging to a business |
| `get_user_owned_groups(db, user_id)` | Groups where the user is the business owner |
| `get_user_member_groups(db, user_id)` | Groups where the user is an active member |

### Member Queries

| Method | Description |
|---|---|
| `get_active_members(db, group_id)` | All active members of a group |
| `get_active_members_for_user(db, user_id)` | All active memberships for a user across groups |
| `get_member_by_user_and_group(db, group_id, user_id)` | Single membership record |
| `get_member_by_id(db, member_id)` | Membership by primary key |
| `is_active_member(db, group_id, user_id)` | Boolean membership check |
| `is_member_of_business(db, business_id, user_id)` | Active membership check scoped to a business |

### Member Mutations

| Method | Description |
|---|---|
| `create_member(db, member)` | Save a new GroupMember record |
| `save_member(db, member)` | Persist updates to an existing member |
| `remove_member(db, member)` | Delete a membership record |

### Invites

| Method | Description |
|---|---|
| `get_pending_invite_by_token(db, token)` | Fetch a PENDING invite by its secret token |
| `create_invite(db, invite)` | Save a new GroupInvite |
| `save_invite(db, invite)` | Persist updates to an existing invite |

### Join Requests

| Method | Description |
|---|---|
| `get_pending_join_request(db, request_id)` | Fetch a PENDING join request by ID |
| `create_join_request(db, request)` | Save a new GroupJoinRequest |
| `save_join_request(db, request)` | Persist updates to an existing join request |

---

## 5. Skills

### User Skills — `skill_repo`

| Method | Description |
|---|---|
| `get_by_user(db, user_id)` | All skills for a user |
| `get_by_user_and_name(db, user_id, skill_name)` | Duplicate check — case-insensitive name match |
| `get_by_user_and_id(db, user_id, skill_id)` | Fetch skill scoped to user (IDOR protection) |

### Skill Categories — `skill_category_repo`

| Method | Description |
|---|---|
| `get_all_with_skills(db)` | All categories with their predefined skills (eager-loaded) |
| `get_by_name(db, name)` | Category by name |

### Predefined Skills — `predefined_skill_repo`

| Method | Description |
|---|---|
| `get_by_category(db, category_id)` | Skills belonging to a category, ordered by name |
| `search_by_name(db, query)` | Case-insensitive full-text search across all predefined skills |

---

## 6. Partners — `partner_repo`

| Method | Description |
|---|---|
| `get_by_user_id(db, user_id)` | Partner profile for a given user |
| `get_by_profile_id(db, profile_id)` | Partner profile by primary key |
| `get_all(db)` | All partner profiles |
| `get_pending(db)` | Profiles awaiting admin approval |
| `get_approved(db)` | Only approved profiles |
| `get_filtered(db, status)` | Filter by any `ApprovalStatus` value |

---

## 7. Billing

### Plans — `plan_repo`

| Method | Description |
|---|---|
| `get_active_plans(db)` | All currently active subscription plans |
| `get_active_by_id(db, plan_id)` | Single active plan by ID |

### Subscriptions — `subscription_repo`

| Method | Description |
|---|---|
| `get_active_by_user(db, user_id)` | The user's current active subscription |
| `get_by_paypal_subscription(db, paypal_sub_id)` | Lookup by PayPal subscription ID |
| `create_or_update(db, user_id, plan_id)` | Upsert — update existing or create new active subscription |
| `cancel(db, subscription)` | Mark subscription as CANCELED and set `end_date` |

### Payments — `payment_repo`

| Method | Description |
|---|---|
| `get_by_user(db, user_id)` | All payments for a user, newest first |
| `get_by_paypal_order(db, order_id)` | Lookup by PayPal order ID |
| `get_by_paypal_capture(db, capture_id)` | Lookup by PayPal capture ID |
| `get_by_paymob_transaction(db, transaction_id)` | Lookup by Paymob transaction ID |
| `get_by_paymob_order(db, paymob_order_id)` | Lookup by Paymob order ID |
| `create_payment(db, ...)` | Create a successful PayPal payment record |
| `create_paymob_payment(db, ...)` | Create a pending Paymob payment (completed via webhook) |

---

## 8. Notifications — `notification_repo`

| Method | Description |
|---|---|
| `get_active_for_user(db, user_id, skip, limit)` | Active (non-expired, non-archived) notifications, newest first |
| `get_by_id(db, notification_id)` | Single notification by ID |
| `count_for_user(db, user_id)` | Total notification count for a user |
| `bulk_update_status(db, user_id, ids, status)` | Batch status update (e.g. mark all as READ) |
| `delete_one(db, user_id, notification_id)` | Delete a single notification (ownership enforced) |
| `delete_bulk(db, user_id, ids)` | Delete multiple notifications (ownership enforced) |
| `delete_all_for_user(db, user_id)` | Wipe all notifications for a user |
| `get_or_create_settings(db, user_id)` | Fetch or create default notification settings |
| `update_settings(db, user_id, update_data)` | Partial update of notification preferences |
| `run_maintenance(db, now)` | Archive expired notifications; delete stale records older than 30 days |

---

## 9. Guidance System — `guidance_repo`

| Method | Description |
|---|---|
| `get_all_stages(db)` | All guidance stages in sequence order |
| `get_concepts_by_stage(db, stage_id)` | Concepts for a stage, ordered by sequence |
| `get_concept_by_id(db, concept_id)` | Single concept by ID |
| `get_user_progress(db, user_id)` | User's last-viewed concept (progress bookmark) |
| `upsert_user_progress(db, user_id, concept_id)` | Update or create the user's progress state |
| `get_concept_by_feature_key(db, feature_key)` | Resolve a UI feature key → guidance concept (powers the in-app `?` help button) |

---

## 10. Other Repositories

| Repo | Key Operations |
|---|---|
| `auth_repo` | `get_by_email`, `get_by_otp`, `create_verification_code`, `invalidate_codes` |
| `business_repo` | Inherits `BaseRepository` for `Business` model |
| `document_repo` | `get_by_user`, `get_by_id` for uploaded documents |
| `export_repo` | `create_job`, `get_by_user`, `update_status`, `get_expired` for background export jobs |
| `message_repo` | `get_group_messages(db, group_id, limit)` for group chat history |
| `privacy_repo` | `get_or_create(db, user_id)`, `update(db, user_id, data)` for privacy settings |
| `admin_repo` | `get_all_users`, `toggle_user_status`, `approve_partner`, `reject_partner` |

---

## Design Conventions

| Convention | Detail |
|---|---|
| **Singleton instances** | Each repo is a module-level instance (e.g. `idea_repo = IdeaRepository(Idea)`) |
| **Deferred commits** | All mutations accept `commit: bool = True`; `commit=False` uses `flush()` for multi-step transactions |
| **Ownership scoping** | Queries scope by `user_id` where relevant to prevent IDOR vulnerabilities |
| **Upsert pattern** | Used in `profile_repo.get_or_create`, `subscription_repo.create_or_update`, `guidance_repo.upsert_user_progress` |
| **Bulk operations** | `notification_repo` uses SQLAlchemy `update()` and `delete()` core statements for efficiency |
