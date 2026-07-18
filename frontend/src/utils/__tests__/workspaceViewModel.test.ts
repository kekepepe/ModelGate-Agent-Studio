import { describe, expect, it } from 'vitest';
import type { WorkspaceState } from '../../types/workspace';
import { getTeamPreset } from '../../types/team';
import { buildWorkspaceViewModel } from '../workspaceViewModel';

const state: WorkspaceState = {
  goal: { id: 'g-1', title: 'Ship', status: 'running', team_preset: 'code-delivery' },
  agents: [
    { id: 'reviewer', name: 'Reviewer', role: 'reviewer', status: 'idle', default_model_id: 'review-model', is_enabled: true },
    { id: 'planner', name: 'Planner', role: 'planner', status: 'idle', default_model_id: 'plan-model', is_enabled: true },
    { id: 'coder', name: 'Coder', role: 'coder', status: 'running', default_model_id: 'code-model', is_enabled: true },
  ],
  tasks: [
    { id: 't-1', goal_id: 'g-1', title: 'Plan', status: 'completed_verified', assigned_agent_id: 'planner', tokens_used: 20, priority: 100, flow_position: 1, dependencies: [] },
    { id: 't-2', goal_id: 'g-1', title: 'Build', status: 'running', assigned_agent_id: 'coder', tokens_used: 40, priority: 90, flow_position: 2, dependencies: ['t-1'] },
    { id: 't-3', goal_id: 'g-1', title: 'Review', status: 'pending', assigned_agent_id: 'reviewer', tokens_used: 0, priority: 80, flow_position: 3, dependencies: ['t-2'] },
  ],
  workers: [
    { id: 'w-2', agent_id: 'coder', model_id: 'code-model', model_name: 'DeepSeek Coder', status: 'running', total_tokens_used: 40 },
  ],
  handoffs: [],
};

describe('buildWorkspaceViewModel', () => {
  it('keeps preset station order while deriving truthful station states', () => {
    const result = buildWorkspaceViewModel(state, getTeamPreset('code-delivery'));

    expect(result.stations.map((station) => station.agent.id)).toEqual(['planner', 'coder', 'reviewer']);
    expect(result.stations.map((station) => station.status)).toEqual(['done', 'running', 'waiting']);
    expect(result.stations[1].worker?.model_name).toBe('DeepSeek Coder');
  });

  it('maps task dependencies to renderer-neutral edges', () => {
    const result = buildWorkspaceViewModel(state, getTeamPreset('code-delivery'));

    expect(result.edges).toMatchObject([
      { fromTaskId: 't-1', toTaskId: 't-2', fromAgentId: 'planner', toAgentId: 'coder', status: 'active' },
      { fromTaskId: 't-2', toTaskId: 't-3', fromAgentId: 'coder', toAgentId: 'reviewer', status: 'planned' },
    ]);
  });

  it('marks both source and target stations when a real handoff is active', () => {
    const handoffState: WorkspaceState = {
      ...state,
      handoffs: [{
        id: 'h-1', task_id: 't-2', status: 'requested', reason: 'context_limit',
        from_agent_id: 'coder', from_model_id: 'code-model', to_agent_id: 'reviewer', to_model_id: 'review-model',
      }],
    };

    const result = buildWorkspaceViewModel(handoffState, getTeamPreset('code-delivery'));
    expect(result.stations.find((station) => station.agent.id === 'coder')?.status).toBe('handoff');
    expect(result.stations.find((station) => station.agent.id === 'reviewer')?.status).toBe('handoff');
  });

  it('renders only agents activated by the current plan after a replan', () => {
    const replannedState: WorkspaceState = {
      ...state,
      active_plan: {
        id: 'plan-v2', plan_id: 'plan', goal_id: 'g-1', version: 2, status: 'active',
        task_mode: 'single_agent', goal_summary: 'Repair', assumptions: [], required_context: [],
        activation_reason: 'Only the coder repair remains.', final_acceptance_criteria: [],
        human_approval_points: [], estimated_cost: {}, planner_type: 'runtime_replan',
        tasks: [{
          id: 'pt-2', client_task_id: 'repair', objective: 'Repair', task_type: 'coding',
          required_capabilities: ['code_edit'], required_tools: [], dependencies: [], acceptance_criteria: [],
          risk_level: 'medium', parallel_safe: false, context_query: '', approval_required: false,
          runtime_task_id: 't-2', source: 'replaced',
        }],
      },
    };
    const result = buildWorkspaceViewModel(replannedState, getTeamPreset('code-delivery'));
    expect(result.stations.map((station) => station.agent.id)).toEqual(['coder']);
    expect(result.edges).toEqual([]);
  });
});
