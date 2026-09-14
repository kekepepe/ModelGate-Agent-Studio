import { describe, expect, it, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import EvolutionReviewPage from '../EvolutionReviewPage';
import type { MemoryDraft, SkillDraft } from '../../types/knowledge';

const approveMemory = vi.fn();
const approveSkill = vi.fn();
const createPreference = vi.fn();

vi.mock('../../hooks/useKnowledge', () => ({
  useEvolutionSummary: () => ({
    data: {
      memory_drafts: [
        {
          id: 'm-1', type: 'experience_memory', title: 'Experience: Provider timeout',
          content: 'Error: Provider timeout\nResolution: Recovered via handoff.',
          confidence: 0.6, tags: ['experience', 'error_solution'], human_approved: null,
          source_goal_id: 'g-1', source_references: {},
        } as unknown as MemoryDraft,
      ],
      skill_drafts: [
        {
          id: 's-1', name: 'Deploy checklist', scenario: 'Shipping to production',
          steps: ['freeze', 'tag', 'ship'], recommended_agents: [], recommended_models: [],
          tools: [], common_failures: [], status: 'approved', human_approved: true,
          success_rate: 0.75, success_count: 3, failure_count: 1,
        } as unknown as SkillDraft,
      ],
      total_memories: 1,
      total_skills: 1,
      pending_review: 1,
    },
    isLoading: false,
  }),
  useApproveMemory: () => ({ mutate: approveMemory, isPending: false }),
  useApproveSkill: () => ({ mutate: approveSkill, isPending: false }),
  useCreatePreference: () => ({ mutate: createPreference, isPending: false }),
  useGenerateMemories: () => ({ mutate: vi.fn(), isPending: false }),
  useKnowledgeSources: () => ({ data: [], isLoading: false }),
  useCreateKnowledgeSource: () => ({ mutate: vi.fn(), isPending: false }),
  useSyncKnowledgeSource: () => ({ mutate: vi.fn(), isPending: false }),
  useDisableKnowledgeSource: () => ({ mutate: vi.fn(), isPending: false }),
  useKnowledgeDocuments: () => ({ data: [], isLoading: false }),
  useKnowledgeChunks: () => ({ data: [], isLoading: false }),
}));

function renderPage() {
  return render(<MemoryRouter><EvolutionReviewPage /></MemoryRouter>);
}

describe('EvolutionReviewPage (V1.2 additions)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('labels experience memories and shows their approval state', () => {
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: /Memories/ }));
    expect(screen.getByText('经验记忆')).toBeInTheDocument();
    expect(screen.getByText('Experience: Provider timeout')).toBeInTheDocument();
  });

  it('creates a preference from the authoring form', () => {
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: /Memories/ }));
    fireEvent.change(screen.getByPlaceholderText(/偏好标题/), { target: { value: 'Always pytest' } });
    fireEvent.change(screen.getByPlaceholderText(/具体内容/), { target: { value: 'Use pytest fixtures.' } });
    fireEvent.click(screen.getByRole('button', { name: '保存' }));
    expect(createPreference).toHaveBeenCalledWith({ title: 'Always pytest', content: 'Use pytest fixtures.' });
  });

  it('shows the skill success rate on skill cards', () => {
    renderPage();
    fireEvent.click(screen.getByRole('button', { name: /Skills/ }));
    expect(screen.getByText(/75% \(3\/4\)/)).toBeInTheDocument();
  });
});
