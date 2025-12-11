# Frontend API Client Implementation

Complete TypeScript API client for connecting to the Pattern Discovery Agent A2A Server.

## Complete API Client Code

```typescript
// src/services/a2aClient.ts
import axios, { AxiosInstance, AxiosError } from 'axios';

// ============================================
// TypeScript Types
// ============================================

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  knowledge_base_repo: string;
  skills_registered: number;
  skills: string[];
}

export interface AgentCard {
  name: string;
  description: string;
  version: string;
  url: string;
  capabilities: {
    streaming: boolean;
    multimodal: boolean;
    authentication: string;
  };
  skills: Skill[];
  metadata: {
    repository: string;
    documentation: string;
    authentication_note: string;
    knowledge_base: string;
    external_agents: Record<string, string>;
    architecture: string;
    skill_count: number;
  };
}

export interface Skill {
  id: string;
  name: string;
  description: string;
  input_schema: Record<string, any>;
  output_schema: Record<string, any>;
  authentication: string;
}

export interface Pattern {
  name: string;
  description: string;
  context: string;
}

export interface TechnicalDecision {
  what: string;
  why: string;
  alternatives: string;
}

export interface ReusableComponent {
  name: string;
  purpose: string;
  location: string;
}

export interface PatternData {
  patterns: Pattern[];
  decisions: TechnicalDecision[];
  reusable_components: ReusableComponent[];
  dependencies: string[];
  problem_domain: string;
  keywords: string[];
  analyzed_at: string;
  commit_sha: string;
}

export interface SimilarRepository {
  repository: string;
  keyword_overlap: number;
  pattern_overlap: number;
  matching_patterns: string[];
  matching_keywords: string[];
}

export interface QueryPatternsResponse {
  success: boolean;
  repository: string;
  patterns: PatternData;
  similar_repositories: SimilarRepository[];
}

export interface Repository {
  name: string;
  latest_patterns: PatternData;
  history_count: number;
  last_updated: string;
}

export interface GetRepositoryListResponse {
  success: boolean;
  repositories: Repository[];
  total_count: number;
}

export interface DeploymentScript {
  name: string;
  description: string;
  commands: string[];
  environment_variables: Record<string, string>;
}

export interface LessonLearned {
  title: string;
  description: string;
  date: string;
  category: string;
  impact: string;
}

export interface DeploymentInfo {
  scripts: DeploymentScript[];
  lessons_learned: LessonLearned[];
  reusable_components: ReusableComponent[];
  ci_cd_platform: string;
  infrastructure: Record<string, any>;
}

export interface GetDeploymentInfoResponse {
  success: boolean;
  repository: string;
  deployment: DeploymentInfo;
}

export interface AddLessonLearnedInput {
  repository: string;
  title: string;
  description: string;
  category: string;
  impact: string;
}

export interface AddLessonLearnedResponse {
  success: boolean;
  message: string;
}

export interface CrossRepoPattern {
  pattern_name: string;
  repositories: string[];
  occurrences: number;
  variations: string[];
}

export interface GetCrossRepoPatternsResponse {
  success: boolean;
  patterns: CrossRepoPattern[];
  total_patterns: number;
}

export interface ExternalAgent {
  name: string;
  url: string;
  status: 'healthy' | 'unhealthy' | 'unknown';
  last_checked: string;
}

export interface HealthCheckExternalResponse {
  success: boolean;
  agents: ExternalAgent[];
}

export interface DocumentationStandard {
  category: string;
  requirement: string;
  severity: 'required' | 'recommended' | 'optional';
}

export interface DocumentationViolation {
  file: string;
  standard: string;
  severity: string;
  message: string;
}

export interface CheckDocumentationStandardsResponse {
  success: boolean;
  repository: string;
  violations: DocumentationViolation[];
  standards_checked: DocumentationStandard[];
  compliance_score: number;
}

// ============================================
// API Client Class
// ============================================

class A2AClient {
  private client: AxiosInstance;
  private authToken?: string;

  constructor(baseURL?: string, authToken?: string) {
    this.client = axios.create({
      baseURL: baseURL || import.meta.env.VITE_API_BASE_URL,
      timeout: parseInt(import.meta.env.VITE_API_TIMEOUT || '30000'),
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.authToken = authToken;

    // Add request interceptor for authentication
    this.client.interceptors.request.use((config) => {
      if (this.authToken) {
        config.headers.Authorization = `Bearer ${this.authToken}`;
      }
      return config;
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response) {
          // Server responded with error status
          console.error('API Error:', error.response.status, error.response.data);
        } else if (error.request) {
          // Request made but no response
          console.error('Network Error:', error.message);
        } else {
          // Error setting up request
          console.error('Request Error:', error.message);
        }
        return Promise.reject(error);
      }
    );
  }

  /**
   * Set authentication token for protected endpoints
   */
  setAuthToken(token: string) {
    this.authToken = token;
  }

  /**
   * Clear authentication token
   */
  clearAuthToken() {
    this.authToken = undefined;
  }

  // ============================================
  // Public Endpoints (No Auth Required)
  // ============================================

  /**
   * Health check endpoint
   */
  async healthCheck(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }

  /**
   * Get agent card with capabilities and skills
   */
  async getAgentCard(): Promise<AgentCard> {
    const response = await this.client.get<AgentCard>('/.well-known/agent.json');
    return response.data;
  }

  /**
   * Query patterns for a specific repository
   */
  async queryPatterns(
    repository: string,
    keywords?: string[]
  ): Promise<QueryPatternsResponse> {
    const response = await this.client.post<QueryPatternsResponse>('/a2a/execute', {
      skill_id: 'query_patterns',
      input: {
        repository,
        keywords: keywords || [],
      },
    });
    return response.data;
  }

  /**
   * Get list of all tracked repositories
   */
  async getRepositoryList(): Promise<GetRepositoryListResponse> {
    const response = await this.client.post<GetRepositoryListResponse>('/a2a/execute', {
      skill_id: 'get_repository_list',
      input: {},
    });
    return response.data;
  }

  /**
   * Get deployment information for a repository
   */
  async getDeploymentInfo(repository: string): Promise<GetDeploymentInfoResponse> {
    const response = await this.client.post<GetDeploymentInfoResponse>('/a2a/execute', {
      skill_id: 'get_deployment_info',
      input: { repository },
    });
    return response.data;
  }

  /**
   * Get cross-repository patterns
   */
  async getCrossRepoPatterns(minOccurrences: number = 2): Promise<GetCrossRepoPatternsResponse> {
    const response = await this.client.post<GetCrossRepoPatternsResponse>('/a2a/execute', {
      skill_id: 'get_cross_repo_patterns',
      input: { min_occurrences: minOccurrences },
    });
    return response.data;
  }

  /**
   * Check health of external agents
   */
  async healthCheckExternal(): Promise<HealthCheckExternalResponse> {
    const response = await this.client.post<HealthCheckExternalResponse>('/a2a/execute', {
      skill_id: 'health_check_external',
      input: {},
    });
    return response.data;
  }

  /**
   * Check documentation standards compliance
   */
  async checkDocumentationStandards(
    repository: string,
    filePaths?: string[]
  ): Promise<CheckDocumentationStandardsResponse> {
    const response = await this.client.post<CheckDocumentationStandardsResponse>('/a2a/execute', {
      skill_id: 'check_documentation_standards',
      input: {
        repository,
        file_paths: filePaths || [],
      },
    });
    return response.data;
  }

  // ============================================
  // Protected Endpoints (Auth Required)
  // ============================================

  /**
   * Add a lesson learned (requires authentication)
   */
  async addLessonLearned(
    input: AddLessonLearnedInput
  ): Promise<AddLessonLearnedResponse> {
    const response = await this.client.post<AddLessonLearnedResponse>('/a2a/execute', {
      skill_id: 'add_lesson_learned',
      input,
    });
    return response.data;
  }

  /**
   * Update dependency information (requires authentication)
   */
  async updateDependencyInfo(
    repository: string,
    dependencyType: 'consumer' | 'derivative',
    dependentRepo: string,
    description: string
  ): Promise<{ success: boolean; message: string }> {
    const response = await this.client.post('/a2a/execute', {
      skill_id: 'update_dependency_info',
      input: {
        repository,
        dependency_type: dependencyType,
        dependent_repo: dependentRepo,
        description,
      },
    });
    return response.data;
  }
}

// ============================================
// Export Singleton Instance
// ============================================

export const a2aClient = new A2AClient();

// Export class for custom instances
export default A2AClient;
```

## React Query Hooks

Create custom hooks for common queries:

```typescript
// src/hooks/usePatterns.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { a2aClient, AddLessonLearnedInput } from '../services/a2aClient';
import toast from 'react-hot-toast';

/**
 * Hook to fetch health status
 */
export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => a2aClient.healthCheck(),
    refetchInterval: 60000, // Refetch every minute
  });
}

/**
 * Hook to fetch agent card
 */
export function useAgentCard() {
  return useQuery({
    queryKey: ['agentCard'],
    queryFn: () => a2aClient.getAgentCard(),
    staleTime: Infinity, // AgentCard rarely changes
  });
}

/**
 * Hook to fetch repository list
 */
export function useRepositories() {
  return useQuery({
    queryKey: ['repositories'],
    queryFn: () => a2aClient.getRepositoryList(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to fetch patterns for a specific repository
 */
export function usePatterns(repository: string, keywords?: string[]) {
  return useQuery({
    queryKey: ['patterns', repository, keywords],
    queryFn: () => a2aClient.queryPatterns(repository, keywords),
    enabled: !!repository, // Only run if repository is provided
  });
}

/**
 * Hook to fetch deployment info
 */
export function useDeploymentInfo(repository: string) {
  return useQuery({
    queryKey: ['deployment', repository],
    queryFn: () => a2aClient.getDeploymentInfo(repository),
    enabled: !!repository,
  });
}

/**
 * Hook to fetch cross-repo patterns
 */
export function useCrossRepoPatterns(minOccurrences: number = 2) {
  return useQuery({
    queryKey: ['crossRepoPatterns', minOccurrences],
    queryFn: () => a2aClient.getCrossRepoPatterns(minOccurrences),
  });
}

/**
 * Hook to fetch external agent health
 */
export function useExternalAgents() {
  return useQuery({
    queryKey: ['externalAgents'],
    queryFn: () => a2aClient.healthCheckExternal(),
    refetchInterval: 120000, // Refetch every 2 minutes
  });
}

/**
 * Hook to check documentation standards
 */
export function useDocumentationStandards(repository: string, filePaths?: string[]) {
  return useQuery({
    queryKey: ['documentationStandards', repository, filePaths],
    queryFn: () => a2aClient.checkDocumentationStandards(repository, filePaths),
    enabled: !!repository,
  });
}

/**
 * Mutation hook to add lesson learned
 */
export function useAddLessonLearned() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: AddLessonLearnedInput) => a2aClient.addLessonLearned(input),
    onSuccess: (data, variables) => {
      // Invalidate and refetch deployment info
      queryClient.invalidateQueries({ queryKey: ['deployment', variables.repository] });
      toast.success('Lesson learned added successfully!');
    },
    onError: (error: Error) => {
      toast.error(`Failed to add lesson: ${error.message}`);
    },
  });
}

/**
 * Mutation hook to update dependency info
 */
export function useUpdateDependency() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: {
      repository: string;
      dependencyType: 'consumer' | 'derivative';
      dependentRepo: string;
      description: string;
    }) => a2aClient.updateDependencyInfo(
      params.repository,
      params.dependencyType,
      params.dependentRepo,
      params.description
    ),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['patterns', variables.repository] });
      toast.success('Dependency information updated!');
    },
    onError: (error: Error) => {
      toast.error(`Failed to update dependency: ${error.message}`);
    },
  });
}
```

## Usage Examples

### Simple Component Using Health Check

```typescript
// src/components/HealthIndicator.tsx
import { useHealth } from '../hooks/usePatterns';
import { Chip } from '@mui/material';
import { CheckCircle, Error } from '@mui/icons-material';

export default function HealthIndicator() {
  const { data, isLoading, isError } = useHealth();

  if (isLoading) return <Chip label="Checking..." />;
  if (isError) return <Chip icon={<Error />} label="Error" color="error" />;

  return (
    <Chip
      icon={<CheckCircle />}
      label={data?.status || 'Unknown'}
      color={data?.status === 'healthy' ? 'success' : 'warning'}
    />
  );
}
```

### Repository List Component

```typescript
// src/components/RepositoryList.tsx
import { useRepositories } from '../hooks/usePatterns';
import {
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Alert,
} from '@mui/material';

export default function RepositoryList() {
  const { data, isLoading, isError, error } = useRepositories();

  if (isLoading) return <CircularProgress />;
  if (isError) return <Alert severity="error">{error.message}</Alert>;

  return (
    <List>
      {data?.repositories.map((repo) => (
        <ListItem key={repo.name}>
          <ListItemText
            primary={repo.name}
            secondary={`Last updated: ${new Date(repo.last_updated).toLocaleDateString()}`}
          />
        </ListItem>
      ))}
    </List>
  );
}
```

### Add Lesson Learned Form

```typescript
// src/components/AddLessonForm.tsx
import { useState } from 'react';
import { useAddLessonLearned } from '../hooks/usePatterns';
import {
  TextField,
  Button,
  MenuItem,
  Box,
  CircularProgress,
} from '@mui/material';

interface AddLessonFormProps {
  repository: string;
  onSuccess?: () => void;
}

export default function AddLessonForm({ repository, onSuccess }: AddLessonFormProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('deployment');
  const [impact, setImpact] = useState('medium');

  const mutation = useAddLessonLearned();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await mutation.mutateAsync({
      repository,
      title,
      description,
      category,
      impact,
    });

    // Reset form
    setTitle('');
    setDescription('');
    onSuccess?.();
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <TextField
        label="Title"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        required
        fullWidth
      />

      <TextField
        label="Description"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        required
        multiline
        rows={4}
        fullWidth
      />

      <TextField
        select
        label="Category"
        value={category}
        onChange={(e) => setCategory(e.target.value)}
        fullWidth
      >
        <MenuItem value="deployment">Deployment</MenuItem>
        <MenuItem value="architecture">Architecture</MenuItem>
        <MenuItem value="testing">Testing</MenuItem>
        <MenuItem value="security">Security</MenuItem>
      </TextField>

      <TextField
        select
        label="Impact"
        value={impact}
        onChange={(e) => setImpact(e.target.value)}
        fullWidth
      >
        <MenuItem value="low">Low</MenuItem>
        <MenuItem value="medium">Medium</MenuItem>
        <MenuItem value="high">High</MenuItem>
      </TextField>

      <Button
        type="submit"
        variant="contained"
        disabled={mutation.isPending}
        startIcon={mutation.isPending && <CircularProgress size={20} />}
      >
        {mutation.isPending ? 'Adding...' : 'Add Lesson'}
      </Button>
    </Box>
  );
}
```

## Error Handling

```typescript
// src/utils/errorHandler.ts
import { AxiosError } from 'axios';
import toast from 'react-hot-toast';

export function handleApiError(error: unknown) {
  if (error instanceof AxiosError) {
    if (error.response) {
      // Server error
      const message = error.response.data?.error || error.response.data?.message || 'Server error';
      toast.error(`API Error: ${message}`);
    } else if (error.request) {
      // Network error
      toast.error('Network error. Please check your connection.');
    } else {
      // Request setup error
      toast.error('Request error. Please try again.');
    }
  } else if (error instanceof Error) {
    toast.error(error.message);
  } else {
    toast.error('An unexpected error occurred');
  }
}
```

## Testing

```typescript
// src/services/__tests__/a2aClient.test.ts
import { describe, it, expect, vi } from 'vitest';
import A2AClient from '../a2aClient';
import axios from 'axios';

vi.mock('axios');

describe('A2AClient', () => {
  it('should fetch health status', async () => {
    const mockData = { status: 'healthy', service: 'pattern-discovery-agent' };
    vi.mocked(axios.create).mockReturnValue({
      get: vi.fn().mockResolvedValue({ data: mockData }),
    } as any);

    const client = new A2AClient('http://localhost:8080');
    const result = await client.healthCheck();

    expect(result).toEqual(mockData);
  });

  it('should handle errors gracefully', async () => {
    vi.mocked(axios.create).mockReturnValue({
      get: vi.fn().mockRejectedValue(new Error('Network error')),
    } as any);

    const client = new A2AClient('http://localhost:8080');

    await expect(client.healthCheck()).rejects.toThrow('Network error');
  });
});
```

## Next Steps

1. Copy API client code to your frontend project
2. Install required dependencies
3. Configure environment variables
4. Create React Query hooks for each endpoint
5. Build UI components using the hooks
6. Add error handling and loading states
7. Test API integration thoroughly

Refer to `FRONTEND_COMPONENTS.md` for complete UI component examples.
