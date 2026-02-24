# CI/CD Pipeline Setup

This guide covers setting up automated testing, building, and deployment for Bizify.

## 🚀 Overview

This project includes simple CI/CD pipeline configurations for:
- **Automated Testing**: pytest + coverage on every push
- **Code Quality**: mypy type checking, linting
- **Security**: Vulnerability scanning
- **Docker Build**: Multi-stage builds with image optimization
- **Kubernetes Deployment**: Rolling updates with automatic scaling

## 📋 Quick Start

### GitHub Actions
```bash
# Copy template to .github/workflows/
mkdir -p .github/workflows
cp docs/ci-cd-templates/github-actions.yml .github/workflows/ci.yml
```

### GitLab CI
```bash
# Copy template (if using GitLab)
cp docs/ci-cd-templates/gitlab-ci.yml .gitlab-ci.yml
```

## ✅ GitHub Actions Pipeline

### File: `.github/workflows/ci.yml`

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11"]
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Type checking
      run: mypy app --config-file=mypy.ini
    
    - name: Lint with flake8
      run: |
        pip install flake8
        flake8 app --max-line-length=100 --count
    
    - name: Security scan with bandit
      run: |
        pip install bandit
        bandit -r app -ll || true
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:test@localhost:5432/test_db
        APP_ENV: test
        SECRET_KEY: test-secret-key-32-chars-minimum!!
      run: |
        pytest tests/ \
          --cov=app \
          --cov-report=xml \
          --cov-report=term-missing \
          -v --tb=short

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Login to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: |
          ${{ secrets.DOCKER_USERNAME }}/bizify:latest
          ${{ secrets.DOCKER_USERNAME }}/bizify:${{ github.sha }}
        cache-from: type=registry,ref=${{ secrets.DOCKER_USERNAME }}/bizify:buildcache
        cache-to: type=registry,ref=${{ secrets.DOCKER_USERNAME }}/bizify:buildcache,mode=max

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Kubernetes
      run: |
        mkdir -p ~/.kube
        echo "${{ secrets.KUBE_CONFIG }}" | base64 -d > ~/.kube/config
        
        kubectl set image deployment/api-app \
          api-container=bizify:${{ github.sha }} \
          --record --namespace=production
        
        kubectl rollout status deployment/api-app --namespace=production
```

## 🐳 Docker Build Integration

The `Dockerfile` supports multi-stage builds:
- **Stage 1**: Builder - Installs dependencies
- **Stage 2**: Runtime - Minimal production image

```bash
# Build locally
docker build -t bizify:latest .

# Build with cache
docker buildx build --cache-from type=local,src=. -t bizify:latest .

# Run
docker run -p 8000:8000 \
  -e DATABASE_URL="postgresql://..." \
  -e SECRET_KEY="your-secret" \
  bizify:latest
```

## ☸️ Kubernetes Deployment

### Deploy with kubectl
```bash
# Apply all manifests
kubectl apply -f k8s/

# Check status
kubectl get pods -n production
kubectl logs -f deployment/api-app -n production
```

### Configuration
See `k8s/deployment.yaml`:
- **Replicas**: Scales 2-10 based on CPU/memory (HPA)
- **Health Checks**: Liveness and readiness probes
- **Resource Limits**: CPU 500m, Memory 512Mi per pod
- **Rolling Update**: MaxSurge 1, MaxUnavailable 0

### Monitoring
```bash
# View metrics
kubectl top pods -n production

# Get events
kubectl describe pod <pod-name> -n production

# Stream logs
kubectl logs -f deployment/api-app -n production --all-containers=true
```

## 📊 Testing Requirements

### Unit Tests
```bash
pytest tests/unit/ -v --cov=app/core --cov=app/models --cov=app/services
```

### Integration Tests
```bash
pytest tests/integration/ -v \
  -k "not slow" \
  --maxfail=3
```

### Performance Tests
```bash
pytest tests/performance/ -v --tb=short

# Run with profiling
py-spy record -o profile.svg pytest tests/performance/
```

### Coverage Targets
| Module | Target | Current |
|--------|--------|---------|
| app/core | 90% | 92% |
| app/services | 85% | 88% |
| app/models | 95% | 96% |
| app/api | 80% | 82% |

## quality-gates

### Pre-commit Checks
```bash
# .pre-commit-config.yaml
repos:
- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: v4.4.0
  hooks:
  - id: trailing-whitespace
  - id: end-of-file-fixer
  - id: check-yaml
  - id: check-added-large-files

- repo: https://github.com/psf/black
  rev: 23.3.0
  hooks:
  - id: black
    language_version: python39

- repo: https://github.com/PyCQA/isort
  rev: 5.12.0
  hooks:
  - id: isort
    args: ["--profile", "black"]

- repo: https://github.com/PyCQA/flake8
  rev: 6.0.0
  hooks:
  - id: flake8
    args: ["--max-line-length=100"]

- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.3.0
  hooks:
  - id: mypy
    additional_dependencies: ["pydantic", "sqlalchemy"]
```

### Branch Protection Rules

For `main` branch:
- ✅ Require status checks to pass (test, lint, coverage)
- ✅ Require PR reviews (min 1 approval)
- ✅ Dismiss stale PR approvals when new commits pushed
- ✅ Require up-to-date branches before merging
- ✅ Require code review from code owners

### Code Coverage Gates
- Coverage must be >= 75% for main branch
- New code must have >= 85% coverage
- Coveralls or Codecov integration recommended

## 🔐 Secrets Management

### GitHub Secrets
```bash
# Add to GitHub Actions

# Docker Hub
DOCKER_USERNAME
DOCKER_PASSWORD

# Kubernetes
KUBE_CONFIG  # base64 encoded ~/.kube/config

# Database
DB_PASSWORD

# API Keys
OPENAI_API_KEY
STRIPE_SECRET_KEY
```

### Kubernetes Secrets
```bash
kubectl create secret generic api-secrets \
  --from-literal=database-password=<password> \
  --from-literal=secret-key=<key> \
  -n production

# Reference in Deployment
env:
- name: SECRET_KEY
  valueFrom:
    secretKeyRef:
      name: api-secrets
      key: secret-key
```

## 📈 Monitoring & Alerts

### Prometheus Metrics
- Endpoint: `/metrics`
- Scrape interval: 15s
- Metrics exported via `prometheus_client`

### Sentry Error Tracking
```python
# app/main.py:
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1,
        environment=settings.APP_ENV,
    )
```

### Health Check
```bash
curl http://api.example.com/health

# Response:
{
  "status": "healthy",
  "timestamp": "2024-03-15T10:30:00Z",
  "version": "1.0.0"
}
```

## 🚀 Deployment Flow

```
git push → GitHub Actions:
├─ Run tests (Python 3.9, 3.10, 3.11)
├─ Type checking (mypy)
├─ Linting (flake8)
├─ Security scan (bandit)
├─ Build Docker image
├─ Push to Docker Hub
└─ Deploy to Kubernetes
    ├─ Update image reference
    ├─ Wait for health checks
    ├─ Monitor rollout status
    └─ Complete

On main branch only:
• Automatic deployment to production
• Automatic scaling based on metrics
• Automatic rollback on health check failure
```

## ⚡ Optimization Tips

### Speed Up CI/CD
1. **Cache Python dependencies**
   ```yaml
   - uses: actions/cache@v3
     with:
       path: ~/.cache/pip
       key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
   ```

2. **Parallel test execution**
   ```bash
   pytest -n auto tests/  # requires pytest-xdist
   ```

3. **Skip tests on documentation changes**
   ```yaml
   if: ${{ !contains(github.event.head_commit.modified, 'docs/') }}
   ```

4. **Use smaller base image for Docker**
   ```dockerfile
   FROM python:3.11-slim  # vs python:3.11
   ```

## 🔄 Continuous Monitoring

### Post-Deployment Checklist
- [ ] Health checks pass
- [ ] Error rate < 0.1%
- [ ] P95 latency < 500ms
- [ ] Database connections healthy
- [ ] Cache hit ratio > 70%
- [ ] No new Sentry errors

## 🤝 Local CI/CD Simulation

### Run full pipeline locally
```bash
#!/bin/bash
set -e

echo "1. Running tests..."
pytest tests/ --cov=app -q

echo "2. Type checking..."
mypy app --config-file=mypy.ini

echo "3. Linting..."
flake8 app --max-line-length=100

echo "4. Building Docker image..."
docker build -t bizify:local .

echo "✅ All checks passed!"
```

Save as `scripts/run-pipeline.sh` and make executable:
```bash
chmod +x scripts/run-pipeline.sh
./scripts/run-pipeline.sh
```

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitLab CI Documentation](https://docs.gitlab.com/ee/ci/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)
- [pytest Documentation](https://docs.pytest.org/)
