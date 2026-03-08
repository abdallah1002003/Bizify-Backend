# Kubernetes Deployment for Bizify API

This directory contains all necessary Kubernetes manifests for deploying Bizify API.

## Files Overview

### 1. `deployment.yaml`
- Defines the Bizify API Deployment
- 3 replicas by default (configurable with HPA)
- Health checks (liveness, readiness, startup probes)
- Resource limits and requests
- Security context and pod anti-affinity

### 2. `service.yaml`
- ClusterIP service for internal communication
- Headless service for direct pod communication
- Exposes HTTP and metrics ports

### 3. `configmap.yaml`
- All configuration values (non-sensitive)
- Database, Redis, AI, Email settings
- Logging and monitoring configuration

### 4. `ingress.yaml`
- NGINX ingress controller configuration
- TLS/SSL with cert-manager
- Rate limiting and security headers
- NetworkPolicy for pod-to-pod communication

### 5. `hpa.yaml`
- Horizontal Pod Autoscaler
- Scales based on CPU (70%) and Memory (80%)
- Min 3, Max 10 replicas
- Configured scale-up and scale-down policies

### 6. `rbac.yaml`
- ServiceAccount for the API
- Role and RoleBinding for RBAC
- Minimal permissions model

### 7. `pdb.yaml`
- PodDisruptionBudget
- Ensures minimum 2 pods available during cluster operations

## Prerequisites

Before deploying, ensure you have:

1. **Kubernetes Cluster** (1.24+)
   ```bash
   kubectl cluster-info
   ```

2. **NGINX Ingress Controller**
   ```bash
   kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.0/deploy/static/provider/cloud/deploy.yaml
   ```

3. **Cert-Manager** (for TLS)
   ```bash
   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
   ```

4. **Secrets Created**
   ```bash
   kubectl create secret generic bizify-secrets \
     --from-literal=database-url="postgresql://user:pass@host:5432/bizify" \
     --from-literal=secret-key="your-secret-key" \
     --from-literal=jwt-private-key="$(cat private.pem)" \
     --from-literal=jwt-public-key="$(cat public.pem)" \
     --from-literal=openai-api-key="sk-..." \
     --from-literal=stripe-secret-key="sk_..." \
     --from-literal=sentry-dsn="https://..."
   ```

## Deployment Steps

### 1. Create Namespace (Optional)
```bash
kubectl create namespace bizify
# Then update all manifests to use namespace: bizify
```

### 2. Apply ConfigMap
```bash
kubectl apply -f k8s/configmap.yaml
```

### 3. Create Secrets
```bash
# See Prerequisites section above
```

### 4. Apply RBAC
```bash
kubectl apply -f k8s/rbac.yaml
```

### 5. Apply Deployment
```bash
kubectl apply -f k8s/deployment.yaml
```

### 6. Apply Service
```bash
kubectl apply -f k8s/service.yaml
```

### 7. Apply Ingress
```bash
kubectl apply -f k8s/ingress.yaml
```

### 8. Apply HPA
```bash
kubectl apply -f k8s/hpa.yaml
```

### 9. Apply PDB
```bash
kubectl apply -f k8s/pdb.yaml
```

### All at Once
```bash
kubectl apply -f k8s/
```

## Verification

### Check Deployment Status
```bash
kubectl get deployments
kubectl describe deployment bizify-api
```

### Check Pods
```bash
kubectl get pods -l app=bizify-api
kubectl logs -l app=bizify-api --tail=100 -f
```

### Check Services
```bash
kubectl get svc bizify-api
```

### Check HPA Status
```bash
kubectl get hpa
kubectl describe hpa bizify-api
```

### Port Forward for Local Testing
```bash
kubectl port-forward svc/bizify-api 8001:80
# Now access at http://localhost:8001
```

## Monitoring

### Prometheus Metrics
Metrics are exposed at `/metrics` on port 9090

Add this to Prometheus scrape config:
```yaml
scrape_configs:
  - job_name: 'bizify-api'
    static_configs:
      - targets: ['bizify-api:9090']
```

### Health Checks
```bash
# Liveness check
kubectl exec -it <pod-name> -- curl http://localhost:8001/health

# Metrics check
kubectl exec -it <pod-name> -- curl http://localhost:8001/metrics
```

## Scaling

### Manual Scaling
```bash
kubectl scale deployment bizify-api --replicas=5
```

### HPA Status
```bash
kubectl get hpa --watch
```

## Troubleshooting

### Pods Not Starting
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

### Health Check Failures
```bash
kubectl exec -it <pod-name> -- sh
curl http://localhost:8001/health
```

### Resource Issues
```bash
kubectl top nodes
kubectl top pods -l app=bizify-api
```

## Environment Variables

Key environment variables are sourced from:
- **ConfigMap**: Non-sensitive configuration (redis.host, database.host, etc)
- **Secrets**: Sensitive data (passwords, API keys, etc)

### To Update Configuration
```bash
kubectl edit configmap bizify-config
kubectl rollout restart deployment bizify-api
```

### To Update Secrets
```bash
kubectl edit secret bizify-secrets
kubectl rollout restart deployment bizify-api
```

## Security Best Practices

✅ Implemented:
- Non-root container user (UID 1000)
- Read-only root filesystem
- Security context with capability dropping
- Network policies for pod-to-pod communication
- RBAC with minimal permissions
- TLS/SSL for external traffic
- Request size limits
- Rate limiting

## Rollback

### If Something Goes Wrong
```bash
# Check rollout history
kubectl rollout history deployment bizify-api

# Rollback to previous version
kubectl rollout undo deployment bizify-api

# Rollback to specific revision
kubectl rollout undo deployment bizify-api --to-revision=2
```

## Production Checklist

- [ ] Configure all secrets properly
- [ ] Set appropriate resource limits
- [ ] Configure HPA thresholds based on load testing
- [ ] Set up Prometheus and monitoring
- [ ] Configure log aggregation (ELK, Datadog, etc)
- [ ] Set up alerts for key metrics
- [ ] Test database backups
- [ ] Configure Redis persistence
- [ ] Test disaster recovery procedures
- [ ] Load test the cluster
- [ ] Set up CI/CD pipeline integration

## Support

For issues or questions about Kubernetes deployments, refer to:
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [NGINX Ingress](https://kubernetes.github.io/ingress-nginx/)
- [Cert-Manager](https://cert-manager.io/docs/)
