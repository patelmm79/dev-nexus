# Auth Proxy Quick Start

Get your authentication proxy running in 5 minutes!

## Prerequisites

- Python 3.8+
- Google Cloud service account JSON file
- A2A server running (local or Cloud Run)

## Step 1: Setup (2 minutes)

```bash
cd auth-proxy

# Windows
setup.bat

# Mac/Linux
bash setup.sh
```

## Step 2: Get Service Account (3 minutes)

### Option A: Use existing service account

If you already have a service account JSON file, copy it:

```bash
cp /path/to/your-service-account.json service-account.json
```

### Option B: Create new service account

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"

# Create service account
gcloud iam service-accounts create a2a-proxy \
  --display-name="A2A Proxy" \
  --project=$PROJECT_ID

# Get email
export SA_EMAIL=$(gcloud iam service-accounts list \
  --filter="displayName:A2A Proxy" \
  --format="value(email)" \
  --project=$PROJECT_ID)

# Create key
gcloud iam service-accounts keys create service-account.json \
  --iam-account=$SA_EMAIL \
  --project=$PROJECT_ID

echo "Service account created: $SA_EMAIL"
```

## Step 3: Configure (30 seconds)

Edit `.env`:

```bash
# For local A2A server
SERVICE_ACCOUNT_FILE=service-account.json
A2A_SERVER_URL=http://localhost:8080
PROXY_PORT=8000

# For Cloud Run A2A server
SERVICE_ACCOUNT_FILE=service-account.json
A2A_SERVER_URL=https://your-service-xxxxx.run.app
PROXY_PORT=8000
```

## Step 4: Allow Service Account (1 minute)

Add your service account to the A2A server's allowed list:

### Local A2A server:

```bash
export ALLOWED_SERVICE_ACCOUNTS="a2a-proxy@your-project.iam.gserviceaccount.com"
python scripts/pattern_analyzer.py  # Restart A2A server
```

### Cloud Run A2A server:

```bash
gcloud run services update pattern-discovery-agent \
  --update-env-vars ALLOWED_SERVICE_ACCOUNTS="a2a-proxy@your-project.iam.gserviceaccount.com" \
  --region=us-central1 \
  --project=your-project-id
```

## Step 5: Start Proxy (10 seconds)

```bash
python server.py
```

You should see:

```
✓ Service account authentication verified
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 6: Test (30 seconds)

Open a new terminal:

```bash
# Test health
curl http://localhost:8000/health

# List skills
curl http://localhost:8000/api/skills

# Test execution
python test_proxy.py
```

## Step 7: Use in Frontend

```javascript
// Your frontend code
const result = await fetch('http://localhost:8000/api/execute', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    skill_id: 'add_deployment_info',
    input: {
      repository: 'owner/repo',
      deployment_info: {
        ci_cd_platform: 'github_actions'
      }
    }
  })
});

console.log(await result.json());
```

## Troubleshooting

### "Service account file not found"

```bash
# Check file exists
ls -l service-account.json

# If not, check SERVICE_ACCOUNT_FILE in .env
cat .env | grep SERVICE_ACCOUNT_FILE
```

### "Authentication failed"

Make sure the service account email is in ALLOWED_SERVICE_ACCOUNTS on the A2A server:

```bash
# For Cloud Run, check current config
gcloud run services describe pattern-discovery-agent \
  --region=us-central1 \
  --format="yaml(spec.template.spec.containers[0].env)"
```

### "Connection refused"

Make sure A2A server is running:

```bash
# Check if A2A server is accessible
curl http://localhost:8080/health
# or
curl https://your-service-xxxxx.run.app/health
```

### CORS errors

Add your frontend URL to ALLOWED_ORIGINS in `.env`:

```bash
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,https://your-frontend.com
```

Then restart the proxy.

## Next Steps

- ✅ Read [README.md](README.md) for full documentation
- ✅ See [../CLAUDE.md](../CLAUDE.md) for system architecture
- ✅ Deploy to production (see README.md "Deployment" section)

## Security Checklist

- [ ] `service-account.json` is in `.gitignore`
- [ ] Never commit credentials to git
- [ ] Use HTTPS in production
- [ ] Restrict ALLOWED_ORIGINS to your domains only
- [ ] Rotate service account keys regularly

## Support

Having issues? Check:
1. [README.md](README.md) - Full documentation
2. [Test output](#step-6-test-30-seconds) - Run `python test_proxy.py`
3. Proxy logs - Check terminal where `python server.py` is running
4. A2A server logs - Check A2A server terminal or Cloud Run logs

---

**You're all set! 🎉**

Your frontend can now securely call authenticated A2A skills without exposing credentials.
