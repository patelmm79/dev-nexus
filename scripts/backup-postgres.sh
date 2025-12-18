#!/bin/bash
# PostgreSQL Backup Script for Cloud Run
# Backs up dev-nexus PostgreSQL to GCS daily
# Deploy as Cloud Function or Cloud Scheduler job

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-globalbiting-dev}"
ZONE="us-central1-a"
INSTANCE_NAME="dev-nexus-postgres"
BACKUP_BUCKET="gs://dev-nexus-postgres-backups"
DB_NAME="devnexus"
DB_USER="devnexus"
BACKUP_DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="devnexus_${BACKUP_DATE}.sql.gz"

echo "Starting PostgreSQL backup..."
echo "Backup file: ${BACKUP_FILE}"

# SSH into PostgreSQL VM and run backup
gcloud compute ssh ${INSTANCE_NAME} \
  --zone=${ZONE} \
  --project=${PROJECT_ID} \
  --command="sudo -u postgres pg_dump -d ${DB_NAME} | gzip" \
  > /tmp/${BACKUP_FILE}

# Upload to GCS
echo "Uploading to GCS..."
gsutil cp /tmp/${BACKUP_FILE} ${BACKUP_BUCKET}/${BACKUP_FILE}

# Cleanup local backup
rm /tmp/${BACKUP_FILE}

# Keep only last 30 days of backups (optional cleanup)
echo "Cleaning old backups (keeping last 30 days)..."
gsutil ls ${BACKUP_BUCKET}/ | while read backup; do
  backup_date=$(echo $backup | grep -oP '\d{4}-\d{2}-\d{2}' | head -1)
  if [ ! -z "$backup_date" ]; then
    backup_seconds=$(date -d "$backup_date" +%s 2>/dev/null || echo 0)
    current_seconds=$(date +%s)
    days_old=$(( (current_seconds - backup_seconds) / 86400 ))

    if [ $days_old -gt 30 ]; then
      echo "Deleting old backup: $backup (${days_old} days old)"
      gsutil rm "$backup"
    fi
  fi
done

echo "✅ Backup complete: ${BACKUP_FILE}"
