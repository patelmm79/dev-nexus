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
2. **Correct connector reference** using manual string interpolation

```hcl
resource "google_cloud_run_v2_service" "pattern_discovery_agent" {
  depends_on = [
    google_vpc_access_connector.postgres_connector,
    google_compute_instance.postgres
  ]

  template {
    vpc_access {
      # IMPORTANT: Manually construct full path for Cloud Run v2
      connector = "projects/${var.project_id}/locations/${var.region}/connectors/${google_vpc_access_connector.postgres_connector.name}"
      egress    = "PRIVATE_RANGES_ONLY"
    }
  }
}
```

**Key Fix**: Manually construct the full resource path. Cloud Run v2 requires exact format: `projects/PROJECT/locations/REGION/connectors/NAME`

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

### Issue: PostgreSQL VM Cannot Download Packages (Network Unreachable)

**Symptom**: Startup script fails with errors like:
```
Cannot initiate the connection to us-central1.gce.archive.ubuntu.com:80
Network is unreachable
```

**Root Cause**: VM has no internet access. No external IP and no Cloud NAT configured.

**Quick Fix - Add External IP Temporarily**:
```bash
# Stop VM
gcloud compute instances stop dev-nexus-postgres --zone=us-central1-a --project=globalbiting-dev

# Add external IP
gcloud compute instances add-access-config dev-nexus-postgres \
  --zone=us-central1-a \
  --project=globalbiting-dev

# Start VM (startup script runs again)
gcloud compute instances start dev-nexus-postgres --zone=us-central1-a --project=globalbiting-dev

# Monitor progress
gcloud compute instances tail-serial-port-output dev-nexus-postgres \
  --zone=us-central1-a \
  --project=globalbiting-dev
```

**Permanent Fix - Use Cloud NAT** (now included in Terraform):
- Cloud NAT allows private VMs to access internet for package downloads
- No external IP needed (more secure)
- Terraform now includes `google_compute_router_nat` resource

After fixing internet access, PostgreSQL will install automatically via startup script.

## Common Fixes

### Issue: Wrong Terraform Attribute for VPC Connector

**Symptom**: Terraform applies successfully but `gcloud run services describe` shows `vpcAccess: null`

**Root Cause**: Using `.id` or `.self_link` attributes don't work reliably. Must manually construct the full resource path.

**Fix**: Update `terraform/main.tf`:
```hcl
# WRONG - uses .id or .self_link (unreliable)
vpc_access {
  connector = google_vpc_access_connector.postgres_connector.id
  egress    = "PRIVATE_RANGES_ONLY"
}

# CORRECT - manually construct full path
vpc_access {
  connector = "projects/${var.project_id}/locations/${var.region}/connectors/${google_vpc_access_connector.postgres_connector.name}"
  egress    = "PRIVATE_RANGES_ONLY"
}
```

**Why**: Cloud Run v2 API requires the exact full resource path format:
- Format: `projects/PROJECT_ID/locations/REGION/connectors/CONNECTOR_NAME`
- Resource attributes (`.id`, `.self_link`) don't always provide correct format
- Manual string interpolation ensures correct format ✅

**Apply Fix**:
```bash
cd terraform
terraform apply
```

### Issue: 403 Forbidden on Health Check

**Symptom**: `curl $SERVICE_URL/health` returns "403 Forbidden" error

**Root Cause**: Cloud Run service requires authentication (default: `allow_unauthenticated = false`)

**Option 1: Enable Public Access (Development)**

Update `terraform/terraform.tfvars`:
```hcl
allow_unauthenticated = true
```

Then apply:
```bash
cd terraform
terraform apply
```

**Option 2: Use Authenticated Requests (Production)**

Generate an identity token and include in request:
```bash
TOKEN=$(gcloud auth print-identity-token)
curl -H "Authorization: Bearer $TOKEN" $SERVICE_URL/health
```

**Note**: These are two separate authentication controls:
- `allow_unauthenticated` (Terraform) - Controls Cloud Run IAM access
- `REQUIRE_AUTH_FOR_WRITE` (env var) - Controls A2A skill-level auth

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
