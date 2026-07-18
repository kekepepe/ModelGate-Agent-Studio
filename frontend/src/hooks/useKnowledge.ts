import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  generateMemories, getEvolutionSummary, approveMemory, approveSkill, disableKnowledgeSource,
  getKnowledgeSources, createKnowledgeSource, syncKnowledgeSource, getKnowledgeDocuments, getKnowledgeChunks,
} from '../api/knowledge';
import type { KnowledgeSourceInput } from '../types/knowledge';

const EVOLUTION_KEY = 'evolution-summary';
const SOURCES_KEY = 'knowledge-sources';

export function useEvolutionSummary(goalId?: string) {
  return useQuery({
    queryKey: [EVOLUTION_KEY, goalId],
    queryFn: () => getEvolutionSummary(goalId),
    refetchInterval: 10000,
  });
}

export function useGenerateMemories() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (goalId: string) => generateMemories(goalId),
    onSuccess: () => qc.invalidateQueries({ queryKey: [EVOLUTION_KEY] }),
  });
}

export function useApproveMemory() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, approved }: { id: string; approved: boolean }) => approveMemory(id, approved),
    onSuccess: () => qc.invalidateQueries({ queryKey: [EVOLUTION_KEY] }),
  });
}

export function useApproveSkill() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, approved }: { id: string; approved: boolean }) => approveSkill(id, approved),
    onSuccess: () => qc.invalidateQueries({ queryKey: [EVOLUTION_KEY] }),
  });
}

export function useDisableKnowledgeSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: disableKnowledgeSource,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: [SOURCES_KEY] });
      qc.invalidateQueries({ queryKey: ['workspace-state'] });
    },
  });
}

export function useKnowledgeSources() {
  return useQuery({
    queryKey: [SOURCES_KEY],
    queryFn: getKnowledgeSources,
    refetchInterval: 10000,
  });
}

export function useCreateKnowledgeSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: KnowledgeSourceInput) => createKnowledgeSource(input),
    onSuccess: () => qc.invalidateQueries({ queryKey: [SOURCES_KEY] }),
  });
}

export function useSyncKnowledgeSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (sourceId: string) => syncKnowledgeSource(sourceId),
    onSuccess: (_, sourceId) => {
      qc.invalidateQueries({ queryKey: [SOURCES_KEY] });
      qc.invalidateQueries({ queryKey: [SOURCES_KEY, sourceId, 'documents'] });
    },
  });
}

export function useKnowledgeDocuments(sourceId: string, enabled: boolean) {
  return useQuery({
    queryKey: [SOURCES_KEY, sourceId, 'documents'],
    queryFn: () => getKnowledgeDocuments(sourceId),
    enabled: enabled && Boolean(sourceId),
  });
}

export function useKnowledgeChunks(documentId: string, enabled: boolean) {
  return useQuery({
    queryKey: [SOURCES_KEY, 'document', documentId, 'chunks'],
    queryFn: () => getKnowledgeChunks(documentId),
    enabled: enabled && Boolean(documentId),
  });
}
