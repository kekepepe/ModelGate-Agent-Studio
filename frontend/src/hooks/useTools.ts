import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { ToolFilters, ToolUpdateData, ToolCallFilters } from '../types/tool';
import * as api from '../api/tools';

const TOOLS_KEY = 'tools';
const TOOL_KEY = 'tool';
const TOOL_CALLS_KEY = 'toolCalls';

export function useTools(filters: ToolFilters = {}) {
  return useQuery({
    queryKey: [TOOLS_KEY, filters],
    queryFn: () => api.getTools(filters),
  });
}

export function useTool(toolId: string) {
  return useQuery({
    queryKey: [TOOL_KEY, toolId],
    queryFn: () => api.getTool(toolId),
    enabled: !!toolId,
  });
}

export function useCreateTool() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.createTool,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [TOOLS_KEY] });
    },
  });
}

export function useUpdateTool(toolId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ToolUpdateData) => api.updateTool(toolId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [TOOLS_KEY] });
      qc.invalidateQueries({ queryKey: [TOOL_KEY, toolId] });
    },
  });
}

export function useDeleteTool() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.deleteTool,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [TOOLS_KEY] });
    },
  });
}

export function useToggleTool() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: api.toggleTool,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [TOOLS_KEY] });
    },
  });
}

export function useToolCalls(filters: ToolCallFilters = {}) {
  return useQuery({
    queryKey: [TOOL_CALLS_KEY, filters],
    queryFn: () => api.getToolCalls(filters),
  });
}

export function useToolCall(callId: string) {
  return useQuery({
    queryKey: [TOOL_CALLS_KEY, callId],
    queryFn: () => api.getToolCall(callId),
    enabled: !!callId,
  });
}
