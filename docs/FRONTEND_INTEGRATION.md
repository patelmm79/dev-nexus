# Frontend Integration Guide - Component Sensibility System

## Overview

This document describes how to integrate the Component Sensibility Agent with the **dev-nexus-frontend** React application at https://github.com/patelmm79/dev-nexus-frontend.

The Component Sensibility System analyzes components across repositories to detect duplication and recommend consolidation to canonical locations. The frontend provides:
- **Component Detection**: Visualize duplicated components and similarity scores
- **Canonical Scoring**: Interactive breakdown of multi-factor location scoring
- **Consolidation Planning**: Manage 4-phase consolidation plans with effort estimates
- **Dependency Graph**: Network visualization showing component dependencies

## Architecture

### High-Level Data Flow

```
User Opens /components
        ↓
React Frontend
        ↓
API Client (componentSensibility.ts)
        ↓
A2A Protocol (http://localhost:8080/a2a/execute)
        ↓
Component Sensibility Skills
        ├─ detect_misplaced_components
        ├─ analyze_component_centrality
        └─ recommend_consolidation_plan
        ↓
Returns: Misplaced components, canonical scores, plans
        ↓
React Components visualize results
```

### Frontend File Structure

```
dev-nexus-frontend/
├── src/
│   ├── pages/
│   │   └── Components/
│   │       ├── index.tsx                    # Main /components page
│   │       ├── ComponentDetection.tsx       # Component detection UI
│   │       ├── ScoringBreakdown.tsx         # Canonical scoring details
│   │       ├── ConsolidationPlan.tsx        # 4-phase consolidation planner
│   │       └── ComponentDependencyGraph.tsx # Dependency visualization
│   ├── components/
│   │   ├── ComponentCard.tsx                # Reusable component card
│   │   ├── ScoreFactorBreakdown.tsx         # Score factor visualization
│   │   └── PlanPhaseCard.tsx                # Consolidation phase card
│   ├── api/
│   │   └── componentSensibility.ts          # A2A protocol client
│   ├── types/
│   │   └── component.ts                     # TypeScript types
│   └── hooks/
│       └── useComponentSensibility.ts       # React hook for API calls
├── tailwind.config.js                       # Styling configuration
└── package.json
```

## React Components

### 1. ComponentDetection.tsx

**Purpose**: Main interface for detecting misplaced components

**Features**:
- Repository selector dropdown
- Component type filter (API Client, Infrastructure, Business Logic, Deployment)
- Similarity threshold slider (0.0 - 1.0)
- Results table with similarity scores
- Canonical location recommendations

**Props**:
```typescript
interface ComponentDetectionProps {
  repositories: string[];
  onComponentSelected: (component: Component) => void;
  defaultRepository?: string;
}
```

**Example Output**:
```typescript
{
  misplaced_components: [
    {
      component_name: "GitHubAPIClient",
      current_location: "patelmm79/agentic-log-attacker",
      similar_components: [
        {
          component_name: "GitHubAPIClient",
          repository: "patelmm79/dev-nexus",
          similarity_score: 0.85
        }
      ],
      canonical_recommendation: {
        repository: "patelmm79/dev-nexus",
        canonical_score: 0.82,
        current_score: 0.45
      }
    }
  ]
}
```

### 2. ScoringBreakdown.tsx

**Purpose**: Interactive visualization of canonical location scoring

**Features**:
- 6-factor breakdown (Purpose, Usage, Centrality, Maintenance, Complexity, First-Impl)
- Weighted contribution visualization (bars/gauges)
- Score comparison across candidate repositories
- Detailed reasoning for each factor

**Props**:
```typescript
interface ScoringBreakdownProps {
  componentName: string;
  currentLocation: string;
  candidateLocations: string[];
}
```

**Component**: Shows side-by-side scoring for each candidate with visual weight indicators

### 3. ConsolidationPlan.tsx

**Purpose**: 4-phase consolidation plan viewer and manager

**Features**:
- Phase cards (Analyze, Merge, Update Consumers, Monitor)
- Effort estimates per phase (2-3 hrs, 3-4 hrs, etc.)
- Actionable task lists
- Affected repositories list
- Success criteria
- Plan status tracking (pending, approved, in-progress, completed)

**Props**:
```typescript
interface ConsolidationPlanProps {
  componentName: string;
  fromRepository: string;
  toRepository: string;
  includeImpactAnalysis?: boolean;
}
```

### 4. ComponentDependencyGraph.tsx

**Purpose**: Network graph showing component dependencies

**Features**:
- Force-directed graph using D3.js or Cytoscape.js
- Node: Repository with component count
- Edge: Component dependency (width = usage count)
- Color coding by repository purpose (infrastructure=blue, application=green)
- Interactive zoom, pan, node selection
- Legend showing edge weights

**Props**:
```typescript
interface ComponentDependencyGraphProps {
  repositories: string[];
  components: Component[];
  height?: string; // default: "600px"
}
```

### 5. Reusable Components

**ComponentCard.tsx**:
- Displays single component with metadata
- Shows component type badge, LOC, complexity
- Link to canonical recommendation

**ScoreFactorBreakdown.tsx**:
- Shows one scoring factor with weight and contribution
- Used within ScoringBreakdown

**PlanPhaseCard.tsx**:
- Shows single consolidation phase
- Expandable task list
- Status indicator

## API Client Integration

### File: src/api/componentSensibility.ts

```typescript
import { apiClient } from './base'; // existing API client

export interface ComponentSensibilityAPI {
  // Detect misplaced components
  detectMisplaced(params: {
    repository?: string;
    component_types?: string[];
    min_similarity_score?: number;
    include_diverged?: boolean;
    top_k_matches?: number;
  }): Promise<DetectMisplacedResponse>;

  // Analyze canonical location scoring
  analyzeCentrality(params: {
    component_name: string;
    current_location: string;
    candidate_locations?: string[];
  }): Promise<AnalyzeCentralityResponse>;

  // Get consolidation plan
  getConsolidationPlan(params: {
    component_name: string;
    from_repository: string;
    to_repository?: string;
    include_impact_analysis?: boolean;
    include_deep_analysis?: boolean;
  }): Promise<ConsolidationPlanResponse>;
}

export const componentSensibilityAPI: ComponentSensibilityAPI = {
  async detectMisplaced(params) {
    return apiClient.post('/a2a/execute', {
      skill_id: 'detect_misplaced_components',
      input: params
    });
  },

  async analyzeCentrality(params) {
    return apiClient.post('/a2a/execute', {
      skill_id: 'analyze_component_centrality',
      input: params
    });
  },

  async getConsolidationPlan(params) {
    return apiClient.post('/a2a/execute', {
      skill_id: 'recommend_consolidation_plan',
      input: params
    });
  }
};
```

### React Hook: useComponentSensibility.ts

```typescript
import { useState, useCallback } from 'react';
import { componentSensibilityAPI } from '../api/componentSensibility';

export const useComponentSensibility = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [misplaced, setMisplaced] = useState(null);
  const [scores, setScores] = useState(null);
  const [plan, setPlan] = useState(null);

  const detectMisplaced = useCallback(async (repository: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await componentSensibilityAPI.detectMisplaced({
        repository,
        min_similarity_score: 0.7
      });
      setMisplaced(result);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const analyzeCentrality = useCallback(async (
    componentName: string,
    currentLocation: string
  ) => {
    setLoading(true);
    setError(null);
    try {
      const result = await componentSensibilityAPI.analyzeCentrality({
        component_name: componentName,
        current_location: currentLocation
      });
      setScores(result);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getConsolidationPlan = useCallback(async (
    componentName: string,
    fromRepo: string,
    toRepo: string
  ) => {
    setLoading(true);
    setError(null);
    try {
      const result = await componentSensibilityAPI.getConsolidationPlan({
        component_name: componentName,
        from_repository: fromRepo,
        to_repository: toRepo,
        include_impact_analysis: true
      });
      setPlan(result);
      return result;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    error,
    misplaced,
    scores,
    plan,
    detectMisplaced,
    analyzeCentrality,
    getConsolidationPlan
  };
};
```

## TypeScript Types

### File: src/types/component.ts

```typescript
// Component detection response
export interface DetectMisplacedResponse {
  success: boolean;
  misplaced_components: MisplacedComponent[];
  error?: string;
}

export interface MisplacedComponent {
  component_name: string;
  current_location: string;
  current_files?: string[];
  similar_components: SimilarComponent[];
  canonical_recommendation: CanonicalRecommendation;
}

export interface SimilarComponent {
  component_name: string;
  repository: string;
  files?: string[];
  similarity_score: number;
  match_type?: string;
  differences?: string[];
}

export interface CanonicalRecommendation {
  repository: string;
  canonical_score: number;
  current_score: number;
  reasoning: string;
}

// Centrality analysis response
export interface AnalyzeCentralityResponse {
  success: boolean;
  analysis: {
    best_location: string;
    best_score: number;
    all_scores: Record<string, ScoreDetail>;
  };
  error?: string;
}

export interface ScoreDetail {
  canonical_score: number;
  factors: FactorScores;
  weights: FactorWeights;
  reasoning: string;
}

export interface FactorScores {
  repository_purpose: number;
  usage_count: number;
  dependency_centrality: number;
  maintenance_activity: number;
  component_complexity: number;
  first_implementation: number;
}

export interface FactorWeights {
  repository_purpose: number;    // 0.30
  usage_count: number;           // 0.30
  dependency_centrality: number; // 0.20
  maintenance_activity: number;  // 0.10
  component_complexity: number;  // 0.05
  first_implementation: number;  // 0.05
}

// Consolidation plan response
export interface ConsolidationPlanResponse {
  success: boolean;
  recommendation_id: string;
  consolidation_plan: ConsolidationPlan;
  impact_analysis?: ImpactAnalysis;
  deep_analysis?: DeepAnalysis;
  error?: string;
}

export interface ConsolidationPlan {
  phase_1: Phase;
  phase_2: Phase;
  phase_3: Phase;
  phase_4: Phase;
  total_estimated_effort: string;
}

export interface Phase {
  name: string;
  description: string;
  estimated_hours: string;
  tasks: string[];
  affected_repositories?: string[];
  success_criteria?: string[];
}

export interface ImpactAnalysis {
  affected_repositories: string[];
  risk_level: string;
  dependency_chain: string[];
}

export interface DeepAnalysis {
  api_compatibility: number;
  behavioral_differences: string[];
  feature_gaps: string[];
}
```

## Navigation Integration

### Update main routing in dev-nexus-frontend:

```typescript
// src/router.tsx or src/App.tsx
import { lazy } from 'react';

const ComponentsPage = lazy(() => import('./pages/Components'));

export const routes = [
  {
    path: '/patterns',
    component: PatternsPage,
    label: 'Patterns'
  },
  {
    path: '/components',    // NEW
    component: ComponentsPage,
    label: 'Components'
  },
  {
    path: '/settings',
    component: SettingsPage,
    label: 'Settings'
  }
];
```

### Navigation Menu Update:

```tsx
// src/components/Sidebar.tsx
<nav>
  <Link to="/patterns">Patterns</Link>
  <Link to="/components">Components</Link>  {/* NEW */}
  <Link to="/settings">Settings</Link>
</nav>
```

## Styling

### Tailwind Configuration Integration

The components should use the existing Tailwind configuration from dev-nexus-frontend. Key classes used:

- **Colors**: Inherit from existing theme (blue for infrastructure, green for apps)
- **Spacing**: Use standard Tailwind spacing scale
- **Typography**: Match existing header/body styles
- **Cards**: Use existing card component styles
- **Buttons**: Use existing button variants

Example component styling:

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
  <div className="bg-white rounded-lg shadow-md p-6">
    {/* Content */}
  </div>
</div>
```

## Setup Instructions

### 1. Add Dependencies to dev-nexus-frontend

```bash
npm install d3 @types/d3 cytoscape --save
# or for graph visualization
npm install react-force-graph --save
```

### 2. Configure API Base URL

Ensure `src/api/base.ts` points to the A2A server:

```typescript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';
```

### 3. Add Environment Variable

Create `.env.local`:

```
REACT_APP_API_URL=http://localhost:8080
```

### 4. Copy Component Files

Copy the React components from this integration guide into `src/pages/Components/` and `src/components/`

### 5. Import and Register Routes

Update your routing to include the Components page

## Usage Examples

### Detecting Misplaced Components

```tsx
function ComponentsPage() {
  const { detectMisplaced, misplaced, loading, error } = useComponentSensibility();

  const handleDetect = async (repo: string) => {
    await detectMisplaced(repo);
  };

  return (
    <div>
      <ComponentDetection
        repositories={['dev-nexus', 'agentic-log-attacker']}
        onComponentSelected={handleAnalyze}
      />
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600">{error}</p>}
      {misplaced && <ResultsTable components={misplaced.misplaced_components} />}
    </div>
  );
}
```

### Analyzing Canonical Scores

```tsx
function AnalysisPage({ component, currentLocation }: Props) {
  const { analyzeCentrality, scores, loading } = useComponentSensibility();

  useEffect(() => {
    analyzeCentrality(component.name, currentLocation);
  }, [component, currentLocation]);

  if (loading) return <div>Loading scoring analysis...</div>;

  return (
    <ScoringBreakdown
      componentName={component.name}
      currentLocation={currentLocation}
      candidateLocations={Object.keys(scores.analysis.all_scores)}
    />
  );
}
```

### Viewing Consolidation Plans

```tsx
function PlanningPage({ component }: Props) {
  const { getConsolidationPlan, plan, loading } = useComponentSensibility();

  const handleShowPlan = async (fromRepo: string, toRepo: string) => {
    await getConsolidationPlan(component.name, fromRepo, toRepo);
  };

  return (
    <div>
      <button onClick={() => handleShowPlan(component.current_location, recommended.repository)}>
        View Plan
      </button>
      {plan && <ConsolidationPlan {...plan.consolidation_plan} />}
    </div>
  );
}
```

## Error Handling

### Common Error Scenarios

**API Unavailable**:
```tsx
{error === 'Failed to connect to A2A server' && (
  <div className="bg-red-50 p-4 rounded">
    <p>Component analysis service is unavailable</p>
    <p className="text-sm text-gray-600">Ensure the A2A server is running on port 8080</p>
  </div>
)}
```

**Repository Not Found**:
```tsx
{error?.includes('Repository not found') && (
  <div className="bg-yellow-50 p-4 rounded">
    <p>Repository not found in knowledge base</p>
  </div>
)}
```

**No Components Detected**:
```tsx
{misplaced.length === 0 && (
  <div className="text-center py-8">
    <p className="text-gray-600">No misplaced components found</p>
  </div>
)}
```

## Performance Considerations

### Optimization Strategies

1. **Lazy Load Graph Visualization**
   - Defer D3/Cytoscape.js loading until user navigates to graph tab

2. **Memoize Component Results**
   - Cache API responses to avoid repeated queries

3. **Pagination for Large Result Sets**
   - Show first 20 components, load more on demand

4. **Debounce Similarity Threshold Changes**
   - Wait 500ms before re-running detection as user adjusts slider

### Example Optimization:

```tsx
const memoizedScores = useMemo(() => scores, [scores]);
const debouncedDetect = useCallback(
  debounce((threshold) => detectMisplaced({ min_similarity_score: threshold }), 500),
  [detectMisplaced]
);
```

## Deprecation: pattern_dashboard.html

### Migration Path

The standalone `pattern_dashboard.html` is **deprecated** as of Phase 4 and should not be used. All functionality has been integrated into dev-nexus-frontend:

**Old Way** (Deprecated):
```
Open pattern_dashboard.html → Load knowledge_base.json → View patterns in isolation
```

**New Way** (Recommended):
```
Open dev-nexus-frontend → Navigate to /patterns or /components → Integrated UI
```

### Migration Steps

1. **Backup**: `git mv pattern_dashboard.html pattern_dashboard.html.deprecated`
2. **Update Documentation**: Remove references to pattern_dashboard.html
3. **Redirect Users**: Update README with link to dev-nexus-frontend
4. **Monitor Usage**: Check logs to ensure no one is using deprecated file
5. **Archive**: After 1 month, delete pattern_dashboard.html.deprecated

## Testing

### Component Testing Example

```typescript
// src/pages/Components/__tests__/ComponentDetection.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ComponentDetection from '../ComponentDetection';
import * as api from '../../api/componentSensibility';

jest.mock('../../api/componentSensibility');

test('detects misplaced components', async () => {
  (api.componentSensibilityAPI.detectMisplaced as jest.Mock).mockResolvedValue({
    success: true,
    misplaced_components: [...]
  });

  render(<ComponentDetection repositories={['dev-nexus']} />);

  fireEvent.click(screen.getByText('Detect'));

  await waitFor(() => {
    expect(screen.getByText('GitHubAPIClient')).toBeInTheDocument();
  });
});
```

## Troubleshooting

### A2A Server Connection Issues

**Problem**: "Failed to connect to A2A server"

**Solutions**:
1. Ensure A2A server is running: `python a2a/server.py`
2. Check frontend points to correct API URL
3. Verify CORS is enabled for frontend origin
4. Check firewall allows port 8080

### No Repositories in Dropdown

**Problem**: Repository list is empty

**Solutions**:
1. Ensure knowledge base is loaded
2. Check KnowledgeBaseManager is initialized
3. Verify KNOWLEDGE_BASE_REPO environment variable is set

## References

- [dev-nexus-frontend Repository](https://github.com/patelmm79/dev-nexus-frontend)
- [Component Sensibility Documentation](./COMPONENT_SENSIBILITY.md)
- [A2A Protocol Reference](../CLAUDE.md#a2a-server-mode)
- [Architecture Overview](../CLAUDE.md#core-architecture)
