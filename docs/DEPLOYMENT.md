# Bizify — Deployment Guide

This document outlines best practices and configurations for deploying the Bizify backend to a production environment. 

## 1. Production Architecture Recommendations

For production, the development server (`uvicorn ... --reload`) should be replaced with a robust process manager and a reverse proxy.

- **Process Manager**: Use **Gunicorn** with `UvicornWorker` classes to manage multiple worker processes.
- **Reverse Proxy**: Use **Nginx** or **Traefik** to handle SSL termination, static file serving (if any), and request routing.
- **Database**: Connect to a managed PostgreSQL service (like Supabase or AWS RDS).
- **Background Tasks**: Run **Celery** workers as a separate background process.

---

## 2. Docker Deployment (Recommended)

Dockerizing the application ensures consistency between development and production. 

### Example `Dockerfile`

```dockerfile
# Use official Python runtime as a parent image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies (e.g., for psycopg2)
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install python dependencies using uv or pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run with Gunicorn using Uvicorn workers
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

---

## 3. Docker Compose (App + Redis + Celery)

To deploy the API, Redis, and the Celery worker together, use `docker-compose.yml`:

```yaml
version: '3.8'

services:
  web:
    build: .
    command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - redis

  worker:
    build: .
    command: celery -A app.core.celery_app.celery_app worker -Q export_queue --loglevel=info
    env_file:
      - .env
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

---

## 4. Nginx Reverse Proxy Configuration

Nginx acts as the front door, forwarding API requests to Gunicorn and handling WebSocket connections properly.

### Example `nginx.conf`
```nginx
server {
    listen 80;
    listen 443 ssl;
    server_name api.bizify.com;

    # SSL Certs here
    # ssl_certificate /etc/letsencrypt/live/api.bizify.com/fullchain.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Special handling for WebSockets (Group Chat) and SSE (Notifications)
    location /api/v1/groups/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

---

## 5. Production Readiness Checklist & Environment Security

Before going to production, you must ensure that your environment is properly configured. **Never hardcode sensitive keys in your codebase or include them in shared PDF documentation.** Use placeholders (e.g., `<your-secret-here>`) in documentation and keep the real values securely in your production `.env` file.

### Safe to Document (Non-Secret)
- `DATABASE_URL`: Connection string to your PostgreSQL instance.
- `FRONTEND_URL`: The real frontend URL required to configure CORS correctly.
- `PAYPAL_MODE`: Set to `live` instead of `sandbox`.
- `SMTP_HOST` / `SMTP_PORT`: Only the server connection details.
- `REDIS_HOST` / `REDIS_PORT`: Local or managed Redis connection info.
- `SUPABASE_URL`: The API URL for your Supabase project.

### DANGEROUS (Keep Secret in `.env`)
- `SECRET_KEY`: **CRITICAL.** If compromised, attackers can forge JWT tokens. Change the default to a strong random string.
- `PAYPAL_CLIENT_SECRET`: If compromised, attackers can steal or manipulate payments.
- `PAYMOB_HMAC_SECRET`: Required to securely verify Paymob webhooks.
- `SMTP_PASSWORD`: If compromised, attackers can send spam using your domain.
- `SUPABASE_KEY`: Full write/read access to your Supabase storage.
- `GOOGLE_CLIENT_SECRET`: If compromised, attackers can spoof OAuth logins.

### Infrastructure Checklist
1. **Migrations:** Run `alembic upgrade head` on the production database.
2. **SSL/TLS:** Enable HTTPS on your Nginx server using Let's Encrypt or a custom certificate.
3. **Monitoring:** Integrate an error tracking tool like Sentry or AWS CloudWatch to monitor unhandled exceptions.
4. **Redis Persistence:** Configure Redis to persist data to disk (AOF/RDB) so background tasks aren't lost if the server restarts.
5. **Celery Concurrency:** Adjust the number of Celery workers based on your server's CPU cores to handle export tasks efficiently.
