import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { AgentUpdateData, AgentFilters } from '../types/agent';
import * as api from '../api/agents';

const AGENTS_KEY = 'agents';
const AGENT_KEY = 'agent';
const TEMPLATES_KEY = 'agent-templates';

export function useAgents(filters: AgentFilters = {}) {
  return useQuery({
    queryKey: [AGENTS_KEY, filters],
    queryFn: () => api.getAgents(filters),
  });
}

export function useAgent(agentId: string) {
  return useQuery({
    queryKey: [AGENT_KEY, agentId],
    queryFn: () => api.getAgent(agentId),
    enabled: !!agentId,
  });
}

export function useCreateAgent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.createAgent,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [AGENTS_KEY] });
    },
  });
}

export function useUpdateAgent(agentId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: AgentUpdateData) => api.updateAgent(agentId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [AGENTS_KEY] });
      qc.invalidateQueries({ queryKey: [AGENT_KEY, agentId] });
    },
  });
}

export function useUpdateAgentStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ agentId, isEnabled }: { agentId: string; isEnabled: boolean }) =>
      api.updateAgentStatus(agentId, isEnabled),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [AGENTS_KEY] });
    },
  });
}

export function useAgentTemplates() {
  return useQuery({
    queryKey: [TEMPLATES_KEY],
    queryFn: api.getAgentTemplates,
  });
}
