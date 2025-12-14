# PostgreSQL Connection Troubleshooting

## Common Issue: Connection Refused

### Symptom
```
Warning: Failed to initialize PostgreSQL: [Errno 111] Connection refused
```

### Root Cause
Cloud Run is not connected to the VPC, so it cannot reach the PostgreSQL VM on the internal network.

### Quick Fix

Run in Cloud Shell:
```bash
bash scripts/fix-vpc-connection.sh
```

Or manually:
```bash
gcloud run services update pattern-discovery-agent \
  --vpc-connector=dev-nexus-connector \
  --vpc-egress=private-ranges-only \
  --region=us-central1 \
  --project=globalbiting-dev
```

### Verification

1. **Check VPC Connector is attached**:
```bash
gcloud run services describe pattern-discovery-agent \
  --region=us-central1 \
  --format="yaml(spec.template.spec.vpcAccess)"
```

Should show:
```yaml
vpcAccess:
  connector: projects/PROJECT/locations/us-central1/connectors/dev-nexus-connector
  egress: PRIVATE_RANGES_ONLY
```

2. **Check PostgreSQL VM is running**:
```bash
gcloud compute instances list --filter="name:postgres"
```

3. **Test connection from Cloud Run**:
```bash
SERVICE_URL=$(gcloud run services describe pattern-discovery-agent \
  --region=us-central1 --format="value(status.url)")
curl $SERVICE_URL/health
```

### Prevent This Issue

The Terraform configuration has been updated with:

1. **Explicit `depends_on`** to ensure proper ordering
2. **Correct connector reference** using `self_link` for Cloud Run v2 API

```hcl
resource "google_cloud_run_v2_service" "pattern_discovery_agent" {
  depends_on = [
    google_vpc_access_connector.postgres_connector,
    google_compute_instance.postgres
  ]

  template {
    vpc_access {
      # IMPORTANT: Use self_link for Cloud Run v2, not id
      connector = google_vpc_access_connector.postgres_connector.self_link
      egress    = "PRIVATE_RANGES_ONLY"
    }
  }
}
```

**Key Fix**: Changed from `.id` to `.self_link` for the VPC connector reference. Cloud Run v2 requires the full resource path (e.g., `projects/PROJECT/locations/REGION/connectors/NAME`), which is provided by `self_link`.

### Re-apply Terraform

After fixing manually, synchronize Terraform state:

```bash
cd terraform

# Import the current state
terraform import google_cloud_run_v2_service.pattern_discovery_agent \
  projects/globalbiting-dev/locations/us-central1/services/pattern-discovery-agent

# Or force a re-apply
terraform apply -replace=google_cloud_run_v2_service.pattern_discovery_agent
```

## Diagnostic Commands

### Check Full Setup
```bash
# VPC Connector
gcloud compute networks vpc-access connectors list --region=us-central1

# Firewall Rules
gcloud compute firewall-rules list --filter="name~postgres"

# PostgreSQL VM
gcloud compute instances describe dev-nexus-postgres --zone=us-central1-a

# Cloud Run Config
gcloud run services describe pattern-discovery-agent --region=us-central1 \
  --format="yaml(spec.template.spec)"
```

### Check PostgreSQL from VM
```bash
# SSH into PostgreSQL VM
gcloud compute ssh dev-nexus-postgres --zone=us-central1-a

# Check PostgreSQL status
sudo systemctl status postgresql

# Check listening ports
sudo netstat -plnt | grep 5432

# Test local connection
sudo -u postgres psql -c "SELECT version();"

# Check configuration
sudo cat /etc/postgresql/*/main/postgresql.conf | grep listen_addresses
sudo cat /etc/postgresql/*/main/pg_hba.conf | grep -v "^#" | grep -v "^$"
```

### Cloud Run Logs
```bash
# Recent logs
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=pattern-discovery-agent" \
  --limit=50 \
  --format="table(timestamp,severity,textPayload)"

# PostgreSQL-specific logs
gcloud logging read \
  "resource.labels.service_name=pattern-discovery-agent AND textPayload:PostgreSQL" \
  --limit=20
```

## Common Fixes

### Issue: Wrong Terraform Attribute (`.id` vs `.self_link`)

**Symptom**: Terraform applies successfully but `gcloud run services describe` shows `vpcAccess: null`

**Root Cause**: Using `.id` instead of `.self_link` for VPC connector reference in Cloud Run v2 service.

**Fix**: Update `terraform/main.tf`:
```hcl
# WRONG - uses .id
vpc_access {
  connector = google_vpc_access_connector.postgres_connector.id
  egress    = "PRIVATE_RANGES_ONLY"
}

# CORRECT - uses .self_link
vpc_access {
  connector = google_vpc_access_connector.postgres_connector.self_link
  egress    = "PRIVATE_RANGES_ONLY"
}
```

**Why**: Cloud Run v2 API requires the full resource path format:
- `.self_link` returns: `projects/PROJECT/locations/REGION/connectors/NAME` ✅
- `.id` returns: short reference (insufficient for v2 API) ❌

**Apply Fix**:
```bash
cd terraform
terraform apply
```

### Issue: VPC Connector Not Ready
```bash
# Check state
gcloud compute networks vpc-access connectors describe dev-nexus-connector \
  --region=us-central1

# If stuck, delete and recreate via Terraform
terraform destroy -target=google_vpc_access_connector.postgres_connector
terraform apply -target=google_vpc_access_connector.postgres_connector
```

### Issue: Firewall Blocking
```bash
# Verify firewall allows VPC connector CIDR
gcloud compute firewall-rules describe dev-nexus-allow-postgres

# Should include: sourceRanges: 10.8.1.0/28 (VPC connector CIDR)
```

### Issue: PostgreSQL Not Configured for Remote Access
```bash
gcloud compute ssh dev-nexus-postgres --zone=us-central1-a

# Edit postgresql.conf
sudo nano /etc/postgresql/15/main/postgresql.conf
# Change: listen_addresses = '*'

# Edit pg_hba.conf
sudo nano /etc/postgresql/15/main/pg_hba.conf
# Add: host all all 10.8.0.0/16 md5

# Restart
sudo systemctl restart postgresql
```

## Prevention Checklist

After any Terraform changes:

- [ ] VPC connector shows STATE: READY
- [ ] Cloud Run has vpc_access configuration
- [ ] PostgreSQL VM is RUNNING
- [ ] Firewall allows traffic from VPC connector CIDR
- [ ] PostgreSQL listens on 0.0.0.0 or internal IP
- [ ] pg_hba.conf allows connections from VPC CIDR
- [ ] Test endpoint returns HTTP 200

## Support

If issues persist:
1. Run the diagnostic commands above
2. Check Cloud Run logs
3. Verify PostgreSQL VM logs: `sudo journalctl -u postgresql -n 100`
4. Test connectivity from Cloud Shell (inside VPC)
