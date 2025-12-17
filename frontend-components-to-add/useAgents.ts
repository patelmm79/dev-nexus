/**
 * Custom hooks for agent and skill management
 * Place in: dev-nexus-frontend/src/hooks/useAgents.ts
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { useCallback } from 'react';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

export interface Skill {
  id: string;
  name: string;
  description: string;
  tags: string[];
  requires_authentication: boolean;
  input_schema: Record<string, any>;
  examples: Array<{ input: any; description: string }>;
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

export interface SkillExecutionRequest {
  skill_id: string;
  input: Record<string, any>;
}

export interface SkillExecutionResponse {
  success: boolean;
  skill_id: string;
  error?: string;
  [key: string]: any; // Skill-specific response fields
}

/**
 * Fetch the AgentCard (all available skills and metadata)
 */
export function useAgentCard() {
  return useQuery<AgentCard>({
    queryKey: ['agentCard'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE_URL}/.well-known/agent.json`);
      return response.data;
    },
    staleTime: Infinity, // AgentCard rarely changes
    retry: 2,
  });
}

/**
 * Execute a skill with given input
 */
export function useExecuteSkill() {
  const queryClient = useQueryClient();
  const authToken = localStorage.getItem('a2a_auth_token');

  return useMutation<SkillExecutionResponse, Error, SkillExecutionRequest>({
    mutationFn: async (request) => {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
      }

      const response = await axios.post<SkillExecutionResponse>(
        `${API_BASE_URL}/a2a/execute`,
        request,
        { headers, timeout: 30000 }
      );

      return response.data;
    },
    onSuccess: () => {
      // Invalidate related queries after skill execution
      queryClient.invalidateQueries({ queryKey: ['patterns'] });
      queryClient.invalidateQueries({ queryKey: ['repositories'] });
    },
  });
}

/**
 * Get a specific skill by ID
 */
export function useSkillById(skillId: string | null) {
  const { data: agentCard } = useAgentCard();

  return {
    skill: agentCard?.skills.find((s) => s.id === skillId),
    isLoading: !agentCard,
  };
}

/**
 * Search and filter skills
 */
export function useSkillSearch(query: string = '') {
  const { data: agentCard, isLoading } = useAgentCard();

  const filteredSkills = agentCard?.skills.filter((skill) => {
    const searchText = query.toLowerCase();
    return (
      skill.name.toLowerCase().includes(searchText) ||
      skill.description.toLowerCase().includes(searchText) ||
      skill.id.toLowerCase().includes(searchText) ||
      skill.tags.some((tag) => tag.toLowerCase().includes(searchText))
    );
  }) || [];

  return {
    skills: filteredSkills,
    isLoading,
    totalCount: agentCard?.skills.length || 0,
  };
}

/**
 * Group skills by category
 */
export function useSkillsByCategory() {
  const { data: agentCard } = useAgentCard();

  const grouped = {
    Query: [] as Skill[],
    Repository: [] as Skill[],
    Knowledge: [] as Skill[],
    Integration: [] as Skill[],
    Documentation: [] as Skill[],
    Monitoring: [] as Skill[],
  };

  agentCard?.skills.forEach((skill) => {
    if (skill.tags.includes('search') || skill.tags.includes('query')) {
      grouped.Query.push(skill);
    } else if (skill.tags.includes('repository')) {
      grouped.Repository.push(skill);
    } else if (skill.tags.includes('knowledge') || skill.tags.includes('learning')) {
      grouped.Knowledge.push(skill);
    } else if (skill.tags.includes('integration') || skill.tags.includes('external')) {
      grouped.Integration.push(skill);
    } else if (skill.tags.includes('documentation')) {
      grouped.Documentation.push(skill);
    } else if (skill.tags.includes('monitoring') || skill.tags.includes('health')) {
      grouped.Monitoring.push(skill);
    }
  });

  // Remove empty categories
  return Object.fromEntries(Object.entries(grouped).filter(([, skills]) => skills.length > 0));
}

/**
 * Get execution history from localStorage
 */
export function useExecutionHistory() {
  const getHistory = useCallback(() => {
    try {
      const history = localStorage.getItem('skill_execution_history');
      return history ? JSON.parse(history) : [];
    } catch {
      return [];
    }
  }, []);

  const addToHistory = useCallback((request: SkillExecutionRequest, response: SkillExecutionResponse) => {
    try {
      const history = getHistory();
      history.push({
        timestamp: new Date().toISOString(),
        request,
        response,
      });
      // Keep only last 50 executions
      if (history.length > 50) {
        history.shift();
      }
      localStorage.setItem('skill_execution_history', JSON.stringify(history));
    } catch (error) {
      console.error('Failed to save execution history:', error);
    }
  }, [getHistory]);

  const clearHistory = useCallback(() => {
    localStorage.removeItem('skill_execution_history');
  }, []);

  return { getHistory, addToHistory, clearHistory };
}

/**
 * Fetch recent actions feed with pagination
 */
export function useRecentActions(
  limit: number = 20,
  offset: number = 0,
  actionTypes?: string[],
  repository?: string
) {
  return useQuery<SkillExecutionResponse>({
    queryKey: ['recentActions', limit, offset, actionTypes, repository],
    queryFn: async () => {
      const input: Record<string, any> = { limit, offset };
      if (actionTypes && actionTypes.length > 0) {
        input.action_types = actionTypes;
      }
      if (repository) {
        input.repository = repository;
      }

      const response = await axios.post<SkillExecutionResponse>(
        `${API_BASE_URL}/a2a/execute`,
        {
          skill_id: 'get_recent_actions',
          input,
        }
      );

      return response.data;
    },
    staleTime: 30000, // 30 seconds
    retry: 2,
  });
}
