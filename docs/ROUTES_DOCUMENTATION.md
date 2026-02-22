# API Routes Documentation

This file is the practical reference for route groups wired in `app/api/api.py`.

## Base URL

- Local: `http://127.0.0.1:8001/api/v1`

## Authentication Model

- Login endpoint: `POST /auth/login`
- Access token type: Bearer JWT (`Authorization: Bearer <token>`)
- Router-level auth is enforced through `Depends(get_current_active_user)` in `app/api/api.py`.
- Some route files may add extra ownership/admin checks on top of router-level auth.

## Route Groups

| Prefix | Router File | Tag | Router-Level Auth |
|---|---|---|---|
| `/auth` | `app/api/routes/auth.py` | `Auth` | No |
| `/users` | `app/api/routes/users/user.py` | `User` | No |
| `/user_profiles` | `app/api/routes/users/user_profile.py` | `UserProfile` | Yes |
| `/admin_action_logs` | `app/api/routes/users/admin_action_log.py` | `AdminActionLog` | Yes |
| `/partner_profiles` | `app/api/routes/partners/partner_profile.py` | `PartnerProfile` | Yes |
| `/partner_requests` | `app/api/routes/partners/partner_request.py` | `PartnerRequest` | Yes |
| `/ideas` | `app/api/routes/ideation/idea.py` | `Idea` | No |
| `/idea_versions` | `app/api/routes/ideation/idea_version.py` | `IdeaVersion` | Yes |
| `/idea_metrics` | `app/api/routes/ideation/idea_metric.py` | `IdeaMetric` | Yes |
| `/experiments` | `app/api/routes/ideation/experiment.py` | `Experiment` | Yes |
| `/businesses` | `app/api/routes/business/business.py` | `Business` | No |
| `/business_collaborators` | `app/api/routes/business/business_collaborator.py` | `BusinessCollaborator` | Yes |
| `/business_invites` | `app/api/routes/business/business_invite.py` | `BusinessInvite` | Yes |
| `/business_invite_ideas` | `app/api/routes/business/business_invite_idea.py` | `BusinessInviteIdea` | Yes |
| `/idea_access` | `app/api/routes/ideation/idea_access.py` | `IdeaAccess` | Yes |
| `/business_roadmaps` | `app/api/routes/business/business_roadmap.py` | `BusinessRoadmap` | Yes |
| `/roadmap_stages` | `app/api/routes/business/roadmap_stage.py` | `RoadmapStage` | Yes |
| `/agents` | `app/api/routes/ai/agent.py` | `Agent` | Yes |
| `/agent_runs` | `app/api/routes/ai/agent_run.py` | `AgentRun` | Yes |
| `/validation_logs` | `app/api/routes/ai/validation_log.py` | `ValidationLog` | Yes |
| `/embeddings` | `app/api/routes/ai/embedding.py` | `Embedding` | Yes |
| `/chat_sessions` | `app/api/routes/chat/chat_session.py` | `ChatSession` | Yes |
| `/chat_messages` | `app/api/routes/chat/chat_message.py` | `ChatMessage` | Yes |
| `/plans` | `app/api/routes/billing/plan.py` | `Plan` | Yes |
| `/subscriptions` | `app/api/routes/billing/subscription.py` | `Subscription` | Yes |
| `/payment_methods` | `app/api/routes/billing/payment_method.py` | `PaymentMethod` | Yes |
| `/payments` | `app/api/routes/billing/payment.py` | `Payment` | Yes |
| `/usages` | `app/api/routes/billing/usage.py` | `Usage` | Yes |
| `/files` | `app/api/routes/core/file.py` | `File` | Yes |
| `/notifications` | `app/api/routes/core/notification.py` | `Notification` | Yes |
| `/share_links` | `app/api/routes/core/share_link.py` | `ShareLink` | Yes |
| `/idea_comparisons` | `app/api/routes/ideation/idea_comparison.py` | `IdeaComparison` | Yes |
| `/comparison_items` | `app/api/routes/ideation/comparison_item.py` | `ComparisonItem` | Yes |
| `/comparison_metrics` | `app/api/routes/ideation/comparison_metric.py` | `ComparisonMetric` | Yes |

## Common Endpoint Pattern

Most resource routers follow CRUD naming:

- `GET /` list
- `POST /` create
- `GET /{id}` retrieve
- `PUT /{id}` update
- `DELETE /{id}` delete

Always confirm exact behavior from route files because some resources include custom filtering and ownership checks.

## Error Behavior

Common status codes in this codebase:

- `200` success
- `201` created
- `400` validation/business rule error
- `401` missing or invalid token
- `403` forbidden (ownership/admin)
- `404` not found
- `422` schema validation failure
- `500` unexpected server error

## Related Docs

- `ROUTES_QUICK_REFERENCE.md` for fast lookup
- `ROUTES_DEVELOPER_SPEC.md` for implementation conventions
- `ROUTES_ARCHITECTURE_SECURITY.md` for architecture and security model
