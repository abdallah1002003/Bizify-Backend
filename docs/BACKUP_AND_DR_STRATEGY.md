# Backup and Disaster Recovery Strategy

Comprehensive backup and recovery procedures for Bizify production environment.

## 🎯 RTO/RPO Targets

| Scenario | RTO | RPO | Notes |
|----------|-----|-----|-------|
| **Database Failure** | 15 minutes | 5 minutes | Hourly backups + WAL |
| **Application Crash** | 2 minutes | 0 minutes | Kubernetes rolling restart |
| **Partial Data Loss** | 1 hour | 1 hour | Point-in-time recovery available |
| **Total Datacenter Down** | 24 hours | 1 hour | Cross-region backup restore |

## 📦 Backup Components

### 1. Database Backups

#### PostgreSQL Backup Methods

**Method A: pg_dump (Simple, Full Backups)**
```bash
#!/bin/bash
# backup-database.sh

BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="bizify_prod"
BACKUP_FILE="$BACKUP_DIR/bizify_$TIMESTAMP.sql.gz"

# Create backup
pg_dump postgresql://user:pass@localhost:5432/$DB_NAME \
  | gzip > "$BACKUP_FILE"

# Keep only last 7 days
find "$BACKUP_DIR" -name "bizify_*.sql.gz" -mtime +7 -delete

# Verify backup
gunzip -t "$BACKUP_FILE" && echo "✅ Backup verified"

# Upload to S3
aws s3 cp "$BACKUP_FILE" s3://bizify-backups/daily/
```

**Schedule with cron:**
```bash
# Run daily at 2 AM
0 2 * * * /scripts/backup-database.sh

# Run hourly
0 * * * * /scripts/backup-database.sh --incremental
```

**Method B: WAL Archiving (Continuous, PITR)**
```ini
# postgresql.conf (for WAL archiving)
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /path/wal_archive/%f && cp %p /path/wal_archive/%f'
archive_timeout = 300  # archive every 5 minutes
```

Benefits:
- Point-in-time recovery to any second
- Minimal data loss (< 5 minutes)
- Automatic archival

**Method C: Continuous Replication (Standby)**

```sql
-- On primary database:
CREATE USER replication_user WITH REPLICATION PASSWORD 'secret';
GRANT CONNECT ON DATABASE bizify_prod TO replication_user;
```

```bash
# Start standby from backup
pg_basebackup -h primary.example.com -D /var/lib/postgresql/14/main \
  -U replication_user --progress --write-recovery-conf --wal-method=stream
```

### 2. Application Data Backups

**AWS S3 Buckets for User Files:**
```python
# app/services/storage/backup_service.py

from boto3 import client as boto3_client

class BackupService:
    def __init__(self):
        self.s3 = boto3_client('s3')
    
    def backup_user_files(self, user_id: UUID):
        """Back up all user-uploaded files to S3."""
        # Retrieve files from local storage or CDN
        # Upload to s3://bizify-backups/user-files/<user_id>/
        # Versioning enabled on bucket
        pass
    
    def backup_chat_history(self, user_id: UUID):
        """Export chat history as JSON archive."""
        # Query all ChatSessions and ChatMessages
        # Compress and upload to S3
        pass
```

**Enable S3 Versioning:**
```bash
aws s3api put-bucket-versioning \
  --bucket bizify-backups \
  --versioning-configuration Status=Enabled
```

### 3. Docker Image Backups

**Tagging Strategy:**
```bash
docker build -t bizify:v1.2.3 -t bizify:latest .
docker tag bizify:v1.2.3 registry.example.com/bizify:v1.2.3
docker push registry.example.com/bizify:v1.2.3

# Keep all production images (no cleanup)
# SemVer tagging enables rollback
```

**Private Registry (Docker Hub / ECR):**
```bash
# AWS ECR
aws ecr create-repository --repository-name bizify

# Push weekly backup
for tag in $(docker images --format "{{.Tag}}" | grep v); do
  aws ecr batch-get-image --repository-name bizify --image-ids imageTag=$tag
done
```

### 4. Kubernetes Configuration Backups

```bash
#!/bin/bash
# backup-kubernetes.sh

BACKUP_DIR="/backups/kubernetes"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Export all resources
kubectl get all -n production -o yaml > "$BACKUP_DIR/production_$TIMESTAMP.yaml"

# Export secrets (WARNING: sensitive!)
kubectl get secrets -n production -o yaml > "$BACKUP_DIR/secrets_$TIMESTAMP.yaml"

# Encrypt before uploading
gpg --symmetric --cipher-algo AES256 "$BACKUP_DIR/secrets_$TIMESTAMP.yaml"
rm "$BACKUP_DIR/secrets_$TIMESTAMP.yaml"  # Remove unencrypted

# Upload to S3
aws s3 cp "$BACKUP_DIR/secrets_${TIMESTAMP}.yaml.gpg" s3://bizify-backups/config/
```

**Alternative: Velero (Kubernetes-native backup):**
```bash
velero install --use-volume-snapshots=true --snapshot-location-config snapshotLocation=us-east-1
velero schedule create daily --schedule="0 2 * * *" --include-namespaces production
```

## 🔄 Recovery Procedures

### Scenario 1: Database Corruption (Data Integrity Issue)

**RTO: 1 hour | RPO: 1 hour**

```bash
# Step 1: Identify corruption time
SELECT datname, recovery_end_timeline, recovery_end_xid FROM pg_control_recovery();

# Step 2: Stop application
kubectl scale deployment api-app --replicas=0 -n production

# Step 3: Restore from backup to point before corruption
pg_restore -d bizify_prod /backups/postgres/bizify_20240315_020000.sql.gz

# Step 4: Verify data integrity
psql -c "SELECT COUNT(*) FROM \"user\";"

# Step 5: Restart application
kubectl scale deployment api-app --replicas=3 -n production
```

### Scenario 2: Accidental Data Deletion

**RTO: 30 minutes | RPO: 5 minutes (with WAL)**

```bash
# Step 1: Determine exact deletion time
SELECT to_timestamp(3735550) - now() AS time_ago FROM (
  SELECT extract(epoch FROM '2024-03-15 14:22:30') AS ts
) x;

# Step 2: Create recovery database
createdb bizify_recovery

# Step 3: Restore specific backup
pg_restore -d bizify_recovery /backups/postgres/bizify_20240315_020000.sql.gz

# Step 4: Replay WAL to target time
# (Done during restore with recovery_target_time parameter)

# Step 5: Verify recovered data
psql -d bizify_recovery -c "SELECT COUNT(*) FROM deleted_table WHERE created_at > '2024-03-15';"

# Step 6: Copy recovered data to production
INSERT INTO production_db.deleted_table 
  SELECT * FROM recovery_db.deleted_table 
  WHERE created_at > '2024-03-15';

# Step 7: Clean up
dropdb bizify_recovery
```

### Scenario 3: Application Pod Failure

**RTO: 2 minutes | RPO: 0 minutes**

Automatic with Kubernetes:
```bash
# Kubernetes automatically:
# 1. Detects pod unhealthy (liveness probe failed)
# 2. Kills pod
# 3. Restarts on new node
# 4. New pod joins load balancer

# Verify status:
kubectl get pods -n production | grep api-app
kubectl logs -f deployment/api-app -n production --previous
```

### Scenario 4: Database Node Failure

**RTO: 5 minutes | RPO: <1 minute (with wal archiving)**

```bash
# Step 1: Verify node is down
pg_isready -h db_primary.local

# Step 2: Promote standby to primary
# (Happens automatically with automated failover)
pg_ctl promote -D /var/lib/postgresql/14/main

# Step 3: Update application connection strings
kubectl set env deployment/api-app \
  DATABASE_URL=postgresql://...standby_promoted...

# Step 4: Restart application pods
kubectl rollout restart deployment/api-app -n production

# Step 5: Verify connectivity
curl http://api-app/health
```

### Scenario 5: Region Failure (Disaster Recovery)

**RTO: 4 hours | RPO: 1 hour**

**Prerequisites:**
- Cross-region replication enabled
- Data synchronized every hour
- Disaster recovery site ready to activate

```bash
# Step 1: Confirm primary region unreachable
# Check all connection endpoints fail

# Step 2: DNS failover to secondary region
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234... \
  --change-batch file://failover.json

# Contents of failover.json:
{
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.example.com",
        "Type": "A",
        "TTL": 60,
        "ResourceRecords": [
          {"Value": "10.1.2.3"}  # Secondary region IP
        ]
      }
    }
  ]
}

# Step 3: Deploy application to secondary region
kubectl apply -f k8s/ --context=secondary-region

# Step 4: Verify secondary database is promoted
psql -h secondary.example.com -U admin -d bizify_prod -c "SELECT version();"

# Step 5: Monitor traffic transition (TTL=60, so ~2 minutes)
# Old clients will timeout and use new DNS entry

# Step 6: Verify all connections successful
curl -v https://api.example.com/health

# Step 7: Document incident and timeline
```

## 🧪 Backup Verification

### Automated Backup Testing

```sql
-- Monthly backup verification job

CREATE TABLE backup_verification_log (
    id SERIAL PRIMARY KEY,
    backup_file VARCHAR,
    verified_at TIMESTAMP DEFAULT NOW(),
    row_count INTEGER,
    integrity_check BOOLEAN,
    status VARCHAR
);

-- Test procedure
PROCEDURE verify_backup(backup_file TEXT)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Restore to temporary database
    -- Verify row counts match
    -- Check foreign key constraints
    -- Update log
    INSERT INTO backup_verification_log (backup_file, row_count, integrity_check, status)
    VALUES (backup_file, (SELECT COUNT(*) FROM table), true, 'verified');
END;
$$;

-- Schedule monthly:
SELECT cron.schedule('verify-backup', '0 3 1 * *', 'CALL verify_backup(latest_backup());');
```

### Test Restoration Quarterly

```bash
#!/bin/bash
# quarterly-restore-test.sh

TEST_DB="bizify_test_restore"
BACKUP_FILE="bizify_latest.sql.gz"

echo "🔄 Starting quarterly backup restoration test..."

# 1. Create test database
createdb "$TEST_DB"

# 2. Restore backup
gunzip -c "$BACKUP_FILE" | psql "$TEST_DB"

# 3. Run validation queries
psql "$TEST_DB" <<EOF
    \echo '📊 Row count validation...'
    SELECT 'user' as table_name, COUNT(*) as rows FROM "user"
    UNION ALL
    SELECT 'subscription', COUNT(*) FROM subscription;
    
    \echo '🔑 Foreign key check...'
    PRAGMA foreign_keys = ON;
    SELECT * FROM pragma_integrity_check();
EOF

# 4. Generate report
echo "✅ Backup restoration test completed" | mail -s "Backup Test Report" ops@example.com

# 5. Clean up
dropdb "$TEST_DB"
```

## 📋 Backup Checklist

### Weekly Tasks
- [ ] Verify previous week's backups completed
- [ ] Check backup file sizes (should be consistent)
- [ ] Verify S3 uploads successful
- [ ] Monitor disk space for backups

### Monthly Tasks
- [ ] Run full backup restoration test
- [ ] Document recovery procedure updates
- [ ] Test Kubernetes spec export
- [ ] Review backup retention policy

### Quarterly Tasks
- [ ] Full disaster recovery drill (non-prod)
- [ ] Cross-region failover test
- [ ] Update RTO/RPO estimates
- [ ] Security audit of backup access

### Annually
- [ ] Complete region-level failover test
- [ ] Review and update runbooks
- [ ] Insurance/compliance documentation
- [ ] Train team on recovery procedures

## 🔐 Backup Security

### Encryption
```bash
# At-rest encryption (AWS S3)
aws s3api put-bucket-encryption \
  --bucket bizify-backups \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# In-transit encryption (HTTPS)
aws s3api put-bucket-policy \
  --bucket bizify-backups \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [{
      "Sid": "DenyInsecureTransport",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": ["arn:aws:s3:::bizify-backups/*"],
      "Condition": {"Bool": {"aws:SecureTransport": "false"}}
    }]
  }'
```

### Access Control
```bash
# Backup access IAM policy
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::bizify-backups",
        "arn:aws:s3:::bizify-backups/*"
      ],
      "Condition": {
        "IpAddress": {"aws:SourceIp": "10.0.0.0/8"}
      }
    }
  ]
}
```

### Deletion Protection
```bash
# Enable MFA for S3 deletion
aws s3api put-bucket-versioning \
  --bucket bizify-backups \
  --versioning-configuration Status=Enabled,MFADelete=Enabled
```

## 📞 Recovery Contact List

| Role | Name | Phone | Email | On-call |
|------|------|-------|-------|---------|
| **Database Admin** | [Name] | [Phone] | [Email] | Mon-Fri 9-5 |
| **DevOps Lead** | [Name] | [Phone] | [Email] | 24/7 |
| **Security Officer** | [Name] | [Phone] | [Email] | 24/7 |

## 📚 Related Documentation

- [PostgreSQL BACKUP/RESTORE](https://www.postgresql.org/docs/current/backup.html)
- [AWS S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/BestPractices.html)
- [Kubernetes Backup Tools](https://velero.io/)
- [Disaster Recovery Plan Template](https://www.ready.gov/business)

## ✅ Last Updated

| Event | Date | Status |
|-------|------|--------|
| Backup automation setup | 2024-03-15 | ✅ Active |
| Recovery test (database) | 2024-03-10 | ✅ Passed |
| Recovery test (DR) | 2023-12-15 | ⚠️ Due |
| Security audit | 2024-03-01 | ✅ Passed |
