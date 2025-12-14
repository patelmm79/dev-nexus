# Authentication Proxy Server

A secure proxy server that handles authentication between your frontend and the A2A server. The frontend never sees service account credentials.

## Architecture

```
┌──────────┐         ┌────────────┐         ┌────────────┐
│ Frontend │ ──────> │ Auth Proxy │ ──────> │ A2A Server │
│ (no auth)│         │ (+ SA creds)│         │            │
└──────────┘         └────────────┘         └────────────┘
```

## Features

- ✅ Secure service account authentication
- ✅ CORS support for frontend access
- ✅ Automatic token refresh
- ✅ Health checks
- ✅ Request logging
- ✅ Error handling

## Setup

### 1. Install Dependencies

```bash
cd auth-proxy
pip install -r requirements.txt
```

### 2. Create Service Account

If you don't have a service account yet:

```bash
# Create service account
gcloud iam service-accounts create a2a-proxy \
  --display-name="A2A Proxy Service Account" \
  --project=YOUR_PROJECT_ID

# Get the email
SA_EMAIL=$(gcloud iam service-accounts list \
  --filter="displayName:A2A Proxy" \
  --format="value(email)")

# Download credentials
gcloud iam service-accounts keys create service-account.json \
  --iam-account=$SA_EMAIL
```

### 3. Configure Allowed Service Accounts

On your A2A server, add the service account email to the allowed list:

```bash
# On A2A server
export ALLOWED_SERVICE_ACCOUNTS="a2a-proxy@YOUR_PROJECT.iam.gserviceaccount.com"
```

Or update your Cloud Run deployment:

```bash
gcloud run services update pattern-discovery-agent \
  --update-env-vars ALLOWED_SERVICE_ACCOUNTS="a2a-proxy@YOUR_PROJECT.iam.gserviceaccount.com" \
  --region=us-central1
```

### 4. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env with your values
nano .env
```

Example `.env`:

```bash
SERVICE_ACCOUNT_FILE=service-account.json
A2A_SERVER_URL=https://pattern-discovery-agent-xxxxx.run.app
PROXY_PORT=8000
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### 5. Run the Proxy

```bash
# Development
python server.py

# Or with uvicorn directly
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Test the Proxy

```bash
# Health check
curl http://localhost:8000/health

# List available skills
curl http://localhost:8000/api/skills

# Execute a skill
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "add_deployment_info",
    "input": {
      "repository": "test/repo",
      "deployment_info": {
        "ci_cd_platform": "github_actions"
      }
    }
  }'
```

## Frontend Integration

### JavaScript/React Example

```javascript
// api.js
const API_BASE_URL = 'http://localhost:8000';

export async function executeSkill(skillId, input) {
  const response = await fetch(`${API_BASE_URL}/api/execute`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      skill_id: skillId,
      input: input
    })
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}

export async function getSkills() {
  const response = await fetch(`${API_BASE_URL}/api/skills`);
  return response.json();
}

// Usage
async function addRepository() {
  try {
    const result = await executeSkill('add_deployment_info', {
      repository: 'owner/repo',
      deployment_info: {
        ci_cd_platform: 'github_actions',
        infrastructure: {
          cloud_run_service: 'my-service'
        }
      }
    });

    console.log('Success:', result);
  } catch (error) {
    console.error('Error:', error);
  }
}
```

### TypeScript Example

```typescript
// types.ts
export interface SkillRequest {
  skill_id: string;
  input: Record<string, any>;
}

export interface SkillResponse {
  success: boolean;
  message?: string;
  error?: string;
  [key: string]: any;
}

// api.ts
const API_BASE_URL = 'http://localhost:8000';

export async function executeSkill(
  skillId: string,
  input: Record<string, any>
): Promise<SkillResponse> {
  const response = await fetch(`${API_BASE_URL}/api/execute`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      skill_id: skillId,
      input: input
    })
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}
```

### Vue.js Example

```javascript
// composables/useA2A.js
import { ref } from 'vue';

export function useA2A() {
  const loading = ref(false);
  const error = ref(null);

  async function executeSkill(skillId, input) {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch('http://localhost:8000/api/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          skill_id: skillId,
          input: input
        })
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Skill execution failed');
      }

      return data;
    } catch (e) {
      error.value = e.message;
      throw e;
    } finally {
      loading.value = false;
    }
  }

  return {
    executeSkill,
    loading,
    error
  };
}
```

## API Endpoints

### `POST /api/execute`

Execute an A2A skill with authentication.

**Request:**
```json
{
  "skill_id": "add_deployment_info",
  "input": {
    "repository": "owner/repo",
    "deployment_info": { ... }
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Deployment info added for owner/repo",
  "repository": "owner/repo"
}
```

### `GET /api/skills`

List all available skills from the A2A server.

**Response:**
```json
{
  "skills": [
    {
      "skill_id": "add_deployment_info",
      "name": "Add Deployment Info",
      "description": "Add or initialize deployment information",
      "requires_auth": true,
      "tags": ["deployment", "repository"]
    }
  ],
  "total": 13
}
```

### `GET /api/agent`

Get the agent card from the A2A server.

### `GET /health`

Health check endpoint.

## Deployment

### Deploy to Cloud Run

```bash
# Build and deploy
gcloud run deploy a2a-proxy \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account a2a-proxy@YOUR_PROJECT.iam.gserviceaccount.com \
  --set-env-vars A2A_SERVER_URL=https://pattern-discovery-agent-xxxxx.run.app \
  --set-env-vars ALLOWED_ORIGINS="https://your-frontend.vercel.app"
```

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .
COPY service-account.json .

CMD ["python", "server.py"]
```

Build and run:

```bash
docker build -t a2a-proxy .
docker run -p 8000:8000 \
  -e A2A_SERVER_URL=http://host.docker.internal:8080 \
  a2a-proxy
```

## Security Notes

- ✅ Service account credentials stay on the server
- ✅ Frontend never sees credentials
- ✅ ID tokens are generated per-request and expire after 1 hour
- ✅ CORS restricts which frontends can access the proxy
- ⚠️ **Never commit `service-account.json` to version control**
- ⚠️ Add `service-account.json` to `.gitignore`

## Troubleshooting

### "Service account file not found"

Make sure `SERVICE_ACCOUNT_FILE` points to the correct path:

```bash
export SERVICE_ACCOUNT_FILE=/path/to/service-account.json
```

### "Authentication failed"

Verify the service account is in the A2A server's allowed list:

```bash
# Check A2A server environment
gcloud run services describe pattern-discovery-agent \
  --region=us-central1 \
  --format="value(spec.template.spec.containers[0].env)"
```

### CORS errors in frontend

Add your frontend URL to `ALLOWED_ORIGINS`:

```bash
export ALLOWED_ORIGINS="http://localhost:3000,http://localhost:5173"
```

### Connection timeout

Increase timeout in `server.py`:

```python
async with httpx.AsyncClient(timeout=120.0) as client:
```

## Logs

The proxy logs all requests for debugging:

```
2024-01-15 10:30:00 - INFO - Proxying request for skill: add_deployment_info
2024-01-15 10:30:01 - INFO - A2A response: 200 for skill add_deployment_info
```

## Development

### Run with hot reload

```bash
uvicorn server:app --reload --port 8000
```

### Run tests

```bash
pytest tests/
```

## License

Same as parent project.
