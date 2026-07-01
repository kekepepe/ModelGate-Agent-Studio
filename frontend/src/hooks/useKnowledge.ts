import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { generateMemories, getEvolutionSummary, approveMemory, approveSkill } from '../api/knowledge';

const EVOLUTION_KEY = 'evolution-summary';

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
