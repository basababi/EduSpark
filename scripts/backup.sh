#!/bin/bash
set -e

# Configuration
DB_HOST=${DATABASE_HOST:-db}
DB_USER=${DATABASE_USER:-eduspark}
DB_NAME=${DATABASE_NAME:-eduspark}
BACKUP_DIR=${BACKUP_DIR:-/backups/eduspark}
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Full backup
BACKUP_FILE="$BACKUP_DIR/eduspark_$(date +%Y%m%d_%H%M%S).sql.gz"
pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" | gzip > "$BACKUP_FILE"
echo "✓ Backup created: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"

# Verify backup
gunzip -t "$BACKUP_FILE" && echo "✓ Backup verified"

# Clean old backups (keep last 30 days)
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete
echo "✓ Cleaned backups older than $RETENTION_DAYS days"
