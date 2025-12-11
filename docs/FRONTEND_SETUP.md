# Frontend Setup Guide

Complete guide for building the React frontend for the Pattern Discovery Agent System.

## Overview

This guide walks through creating a separate frontend repository that connects to the dev-nexus A2A API server to provide visual exploration of patterns, configuration management, and system monitoring.

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Frontend (New Repository)                      │
│  - React 18 + TypeScript                        │
│  - Vite build tool                              │
│  - TanStack Query for API calls                 │
│  - Material-UI components                       │
│  - Recharts for visualizations                  │
│  - Deployed to Vercel/Netlify                   │
└─────────────────┬───────────────────────────────┘
                  │
                  │ HTTPS + CORS
                  │ A2A Protocol
                  │
┌─────────────────▼───────────────────────────────┐
│  Backend (This Repository)                      │
│  - FastAPI A2A Server                           │
│  - Pattern Discovery Engine                     │
│  - Deployed to Cloud Run                        │
└─────────────────────────────────────────────────┘
```

## Prerequisites

- Node.js 18+ and npm/yarn/pnpm
- Git
- Code editor (VS Code recommended)
- Backend API URL (local or Cloud Run)

## Step 1: Create New Repository

```bash
# Create new directory for frontend
mkdir dev-nexus-frontend
cd dev-nexus-frontend

# Initialize git
git init

# Create React + TypeScript project with Vite
npm create vite@latest . -- --template react-ts

# Or use alternative scaffolding
# npx create-react-app . --template typescript
```

## Step 2: Install Dependencies

```bash
# Core dependencies
npm install \
  react-router-dom \
  @tanstack/react-query \
  axios \
  zustand \
  @mui/material @mui/icons-material @emotion/react @emotion/styled \
  recharts \
  react-force-graph-2d \
  date-fns \
  react-hot-toast

# Dev dependencies
npm install -D \
  @types/react-router-dom \
  eslint \
  prettier \
  @typescript-eslint/parser \
  @typescript-eslint/eslint-plugin
```

### Technology Stack Explained

| Package | Purpose |
|---------|---------|
| `react-router-dom` | Client-side routing (Dashboard, Patterns, Settings pages) |
| `@tanstack/react-query` | API calls, caching, automatic refetching |
| `axios` | HTTP client for A2A API |
| `zustand` | Lightweight state management |
| `@mui/material` | UI component library (Google Material Design) |
| `recharts` | Chart library for metrics visualization |
| `react-force-graph-2d` | Interactive network graph for pattern relationships |
| `date-fns` | Date formatting utilities |
| `react-hot-toast` | Toast notifications |

## Step 3: Environment Configuration

Create `.env` file in project root:

```env
# Backend API URL
VITE_API_BASE_URL=http://localhost:8080
VITE_API_TIMEOUT=30000

# Optional: Authentication token (if using A2A auth)
# VITE_A2A_AUTH_TOKEN=your-token-here

# Environment
VITE_ENV=development
```

Create `.env.production`:

```env
VITE_API_BASE_URL=https://your-cloud-run-service.run.app
VITE_API_TIMEOUT=30000
VITE_ENV=production
```

## Step 4: Project Structure

Create the following directory structure:

```
dev-nexus-frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── assets/              # Images, icons
│   ├── components/          # Reusable UI components
│   │   ├── common/          # Buttons, inputs, cards
│   │   ├── patterns/        # Pattern-specific components
│   │   ├── repository/      # Repository components
│   │   └── layout/          # Layout components (navbar, sidebar)
│   ├── pages/               # Full page components
│   │   ├── Dashboard.tsx
│   │   ├── Repositories.tsx
│   │   ├── Patterns.tsx
│   │   ├── Configuration.tsx
│   │   ├── Deployment.tsx
│   │   └── Agents.tsx
│   ├── services/            # API clients
│   │   └── a2aClient.ts
│   ├── hooks/               # Custom React hooks
│   │   ├── usePatterns.ts
│   │   ├── useRepositories.ts
│   │   └── useHealth.ts
│   ├── store/               # Zustand stores
│   │   └── appStore.ts
│   ├── types/               # TypeScript types
│   │   └── index.ts
│   ├── utils/               # Helper functions
│   │   ├── formatters.ts
│   │   └── validators.ts
│   ├── App.tsx              # Main app component
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles
├── .env
├── .env.production
├── .gitignore
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## Step 5: API Client Implementation

See `FRONTEND_API_CLIENT.md` for complete API client code with TypeScript types.

Quick example:

```typescript
// src/services/a2aClient.ts
import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

class A2AClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // Health check
  async healthCheck() {
    const response = await this.client.get('/health');
    return response.data;
  }

  // Query patterns
  async queryPatterns(repository: string, keywords?: string[]) {
    const response = await this.client.post('/a2a/execute', {
      skill_id: 'query_patterns',
      input: { repository, keywords },
    });
    return response.data;
  }

  // Get all repositories
  async getRepositories() {
    const response = await this.client.post('/a2a/execute', {
      skill_id: 'get_repository_list',
      input: {},
    });
    return response.data;
  }

  // Add more methods for other A2A skills...
}

export const a2aClient = new A2AClient();
```

## Step 6: React Query Setup

```typescript
// src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);
```

## Step 7: Routing Setup

```typescript
// src/App.tsx
import { Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Repositories from './pages/Repositories';
import Patterns from './pages/Patterns';
import Configuration from './pages/Configuration';
import Deployment from './pages/Deployment';
import Agents from './pages/Agents';

const theme = createTheme({
  palette: {
    mode: 'dark', // or 'light'
    primary: {
      main: '#1976d2',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="repositories" element={<Repositories />} />
          <Route path="patterns" element={<Patterns />} />
          <Route path="configuration" element={<Configuration />} />
          <Route path="deployment" element={<Deployment />} />
          <Route path="agents" element={<Agents />} />
        </Route>
      </Routes>
    </ThemeProvider>
  );
}

export default App;
```

## Step 8: Key Components

### Dashboard Page

```typescript
// src/pages/Dashboard.tsx
import { useQuery } from '@tanstack/react-query';
import { Grid, Card, CardContent, Typography } from '@mui/material';
import { a2aClient } from '../services/a2aClient';

export default function Dashboard() {
  const { data: health, isLoading } = useQuery({
    queryKey: ['health'],
    queryFn: () => a2aClient.healthCheck(),
  });

  const { data: repositories } = useQuery({
    queryKey: ['repositories'],
    queryFn: () => a2aClient.getRepositories(),
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Pattern Discovery Dashboard
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6">Service Status</Typography>
              <Typography variant="h3" color="success.main">
                {health?.status}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6">Repositories</Typography>
              <Typography variant="h3">
                {repositories?.repositories?.length || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6">Skills Registered</Typography>
              <Typography variant="h3">
                {health?.skills_registered || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </div>
  );
}
```

### Pattern Visualization Component

See `FRONTEND_COMPONENTS.md` for complete component examples including:
- Interactive pattern network graph
- Repository list with search/filter
- Configuration editor forms
- Deployment info viewer

## Step 9: Build and Development

```bash
# Development server with hot reload
npm run dev

# Open browser to http://localhost:5173

# Build for production
npm run build

# Preview production build locally
npm run preview

# Type checking
npm run type-check

# Linting
npm run lint
```

## Step 10: Deployment

### Deploy to Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel

# Or connect GitHub repo in Vercel dashboard
# Vercel will auto-deploy on git push
```

Configuration in `vercel.json`:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "env": {
    "VITE_API_BASE_URL": "https://your-cloud-run-service.run.app"
  }
}
```

### Deploy to Netlify

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
netlify deploy --prod

# Or connect GitHub repo in Netlify dashboard
```

Configuration in `netlify.toml`:

```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

## Step 11: Update Backend CORS

Update your production backend's `CORS_ORIGINS` environment variable to include your frontend URL:

```bash
# In your backend .env file
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://dev-nexus-frontend.vercel.app

# Or set in Cloud Run
gcloud run services update pattern-discovery-agent \
  --region=us-central1 \
  --update-env-vars CORS_ORIGINS="http://localhost:3000,http://localhost:5173,https://dev-nexus-frontend.vercel.app"
```

## Features to Implement

### Phase 1: Core Features (MVP)
- ✅ Dashboard with health metrics
- ✅ Repository list and details
- ✅ Pattern query and display
- ✅ Basic configuration editor

### Phase 2: Visualizations
- 🔲 Interactive pattern similarity graph
- 🔲 Repository relationship network
- 🔲 Pattern evolution timeline
- 🔲 Metrics charts and trends

### Phase 3: Advanced Features
- 🔲 Real-time pattern monitoring
- 🔲 Configuration management UI
- 🔲 Deployment info viewer
- 🔲 Agent health dashboard
- 🔲 Documentation standards checker UI
- 🔲 Lesson learned browser

### Phase 4: Integrations
- 🔲 GitHub OAuth login
- 🔲 Notification preferences
- 🔲 Webhook management
- 🔲 External agent communication UI

## Best Practices

1. **Error Handling**: Always wrap API calls in try-catch with user-friendly error messages
2. **Loading States**: Show loading spinners/skeletons during data fetching
3. **Optimistic Updates**: Use React Query mutations for better UX
4. **Type Safety**: Define TypeScript types for all API responses
5. **Code Splitting**: Use lazy loading for route components
6. **Performance**: Memoize expensive computations with useMemo
7. **Accessibility**: Follow WCAG guidelines, use semantic HTML

## Troubleshooting

### CORS Errors

If you see CORS errors in browser console:

1. Verify backend CORS_ORIGINS includes your frontend URL
2. Check that credentials are properly configured
3. Ensure backend server is running and accessible

### API Connection Issues

1. Verify VITE_API_BASE_URL in `.env` is correct
2. Test API directly with curl: `curl http://localhost:8080/health`
3. Check browser network tab for failed requests
4. Verify API is deployed and accessible from internet

### Build Errors

1. Clear node_modules and reinstall: `rm -rf node_modules && npm install`
2. Check Node.js version compatibility
3. Verify all TypeScript types are correctly defined

## Next Steps

1. Review complete API client code in `FRONTEND_API_CLIENT.md`
2. Review component examples in `FRONTEND_COMPONENTS.md`
3. Set up CI/CD pipeline for automated deployment
4. Implement authentication if using protected A2A skills
5. Add monitoring and error tracking (Sentry, LogRocket)

## Resources

- [React Documentation](https://react.dev)
- [Vite Documentation](https://vitejs.dev)
- [Material-UI Documentation](https://mui.com)
- [TanStack Query Documentation](https://tanstack.com/query)
- [A2A Protocol Specification](https://github.com/patelmm79/dev-nexus/blob/main/docs/A2A_PROTOCOL.md)

## Support

For issues or questions:
- Open issue in dev-nexus repository
- Check existing documentation in `/docs`
- Review API endpoints at `http://localhost:8080/` (when server is running)
