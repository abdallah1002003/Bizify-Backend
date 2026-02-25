# ADR-005: Event-Driven Stripe Billing via Webhooks

**Date:** 2025-10-20  
**Status:** `Accepted`  
**Deciders:** Backend Team

---

## Context

Bizify uses Stripe for subscription billing and payment processing. We must decide how the backend responds to Stripe events (payment success, subscription changes, invoice creation) — either by polling Stripe APIs or by reacting to Stripe Webhooks.

## Decision Drivers

- **Reliability:** Stripe guarantees at-least-once delivery for webhook events
- **Idempotency:** Webhook retries mean handlers must be safe to call multiple times
- **Decoupling:** Stripe state changes should not require the client to wait for our backend to synchronize
- **Cost:** Stripe API calls are rate-limited; polling is wasteful and slower

## Considered Options

| Option | Description |
|--------|-------------|
| **Webhooks (event-driven)** | Stripe POSTs events to `/api/v1/billing/webhook`; handler updates local DB |
| Polling (pull-based) | Backend periodically calls Stripe REST API to check status |
| Hybrid (webhooks + polling fallback) | Webhooks primary; periodic reconciliation job |

## Decision Outcome

**Chosen option:** Pure event-driven Webhooks, with idempotency enforcement via the `ProcessedEvent` database table.

### Webhook Idempotency Architecture

```
Stripe → POST /api/v1/billing/webhook
         ↓
    Verify Stripe signature (STRIPE_WEBHOOK_SECRET)
         ↓
    Check ProcessedEvent table: event_id already exists?
    ├── YES → Return 200 immediately (no-op)
    └── NO  → Insert ProcessedEvent (unique constraint)
              ↓
         Dispatch to handler (payment_intent.succeeded, etc.)
              ↓
         Commit ProcessedEvent + business changes atomically
```

### Handled Stripe Events

| Event | Effect |
|-------|--------|
| `payment_intent.succeeded` | Mark Payment → `COMPLETED` |
| `payment_intent.payment_failed` | Mark Payment → `FAILED` |
| `customer.subscription.deleted` | Mark Subscription → `CANCELED` |
| `customer.subscription.updated` | Sync status + end_date |
| `invoice.payment_succeeded` | Log successful invoice |
| `checkout.session.completed` | Create local Subscription record |

### Positive Consequences

- No polling overhead — events are pushed by Stripe
- `ProcessedEvent` table ensures exact-once processing even under retries
- Atomic commit of `ProcessedEvent` + business state change prevents partial updates
- Signature verification (`stripe.Webhook.construct_event`) prevents forgery

### Negative Consequences / Trade-offs

- Stripe's webhook delivery can have variable latency (usually <1s, but no SLA guarantee)
- `STRIPE_WEBHOOK_SECRET` must be rotated carefully during key rotation events
- No direct Stripe API calls from backend — Checkout Sessions must be initiated from the frontend with Stripe.js

## Links

- [stripe_webhook_service.py](file:///Users/abdallahabdelrhimantar/Desktop/p7/app/services/billing/stripe_webhook_service.py) — Webhook handlers
- [stripe_idempotency.py](file:///Users/abdallahabdelrhimantar/Desktop/p7/app/services/billing/stripe_idempotency.py) — Idempotency key utility for future outgoing calls
- [ADR-004](./004-redis-rate-limiting.md) — Redis design
