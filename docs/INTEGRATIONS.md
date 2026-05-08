# Bizify — External Integrations

Bizify relies on several external platforms to provide full functionality. Here is the breakdown of all third-party system integrations.

| Integration | Core Files | Purpose |
|---|---|---|
| **Google OAuth** | `google_client.py`<br>`auth_service.py` | Builds the auth URL, exchanges the authorization code, fetches the user's Google profile, and links it to or creates a Bizify user account. |
| **SMTP Email** | `mail.py` | Sends transactional emails, including OTP verification codes, password resets, group invites, and join request status updates. Uses Gmail SMTP via TLS. |
| **Redis** | `cache.py`<br>`celery_app.py` | Provides fast JSON caching operations and serves as the message broker and result backend for Celery tasks. |
| **Celery** | `celery_app.py`<br>`export_service.py` | Runs long-running background tasks independently from the HTTP thread, specifically for the data export jobs on the `export_queue`. |
| **PayPal** | `paypal_client.py`<br>`payment_service.py` | Handles international subscription payments. Interacts with the PayPal Orders API to create orders, capture funds, and process signed webhooks for status updates. |
| **Paymob** | `paymob_client.py`<br>`payment_service.py` | Handles local Egyptian card payments (Visa/Mastercard). Generates iframe checkout URLs and verifies HMAC-signed transaction webhooks for security. |
| **Supabase Storage** | `partner_service.py` | Stores partner application documents securely. Utilized when Supabase credentials are provided, serving as a scalable cloud alternative to local file storage. |
| **External AI Pipeline** | `ai_pipeline_service.py` | Connects to the core Bizify AI engine. Sends the user's profile and skills for analysis, and fetches the generated profile, problems, business ideas, and AI chat history. |
