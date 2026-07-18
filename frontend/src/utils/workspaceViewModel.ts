import type {
  WorkspaceAgent,
  WorkspaceHandoff,
  WorkspaceState,
  WorkspaceTask,
  WorkspaceWorker,
} from '../types/workspace';
import type { TeamPreset } from '../types/team';

export type WorkspaceViewMode = 'card' | 'pixel';

export type StationViewModel = {
  agent: WorkspaceAgent;
  worker?: WorkspaceWorker | null;
  tasks: WorkspaceTask[];
  status: string;
  activeTask?: WorkspaceTask | null;
  handoffs: WorkspaceHandoff[];
  order: number;
};

export type TaskEdgeViewModel = {
  id: string;
  fromTaskId: string;
  toTaskId: string;
  fromAgentId?: string | null;
  toAgentId?: string | null;
  status: 'planned' | 'active' | 'done' | 'waiting' | 'handoff' | 'error';
};

export type WorkspaceViewModel = {
  stations: StationViewModel[];
  edges: TaskEdgeViewModel[];
  handoffs: WorkspaceHandoff[];
};

const COMPLETE_STATUSES = new Set(['completed', 'completed_verified', 'completed_unverified']);
const ROLE_ORDER = ['planner', 'research', 'coder', 'summarizer', 'reviewer', 'supervisor'];

export function buildWorkspaceViewModel(state: WorkspaceState, preset: TeamPreset): WorkspaceViewModel {
  const activeTaskIds = new Set(
    state.active_plan?.tasks.map((task) => task.runtime_task_id).filter(Boolean) || [],
  );
  const graphTasks = activeTaskIds.size > 0
    ? state.tasks.filter((task) => activeTaskIds.has(task.id))
    : state.tasks;
  const taskAgentIds = new Set(graphTasks.map((task) => task.assigned_agent_id).filter(Boolean));
  const handoffAgentIds = new Set(state.handoffs.flatMap((handoff) => [handoff.from_agent_id, handoff.to_agent_id]));

  const visibleAgents = state.agents
    .filter((agent) => taskAgentIds.has(agent.id) || handoffAgentIds.has(agent.id))
    .toSorted((left, right) => {
      const leftTaskOrder = minimumTaskOrder(graphTasks, left.id);
      const rightTaskOrder = minimumTaskOrder(graphTasks, right.id);
      if (leftTaskOrder !== rightTaskOrder) return leftTaskOrder - rightTaskOrder;
      return roleOrder(left.role, preset) - roleOrder(right.role, preset);
    });

  const stations = visibleAgents.map((agent, index): StationViewModel => {
    const tasks = graphTasks
      .filter((task) => task.assigned_agent_id === agent.id)
      .toSorted((left, right) => (left.flow_position || 0) - (right.flow_position || 0));
    const worker = pickWorker(state.workers, agent.id);
    const activeTask = tasks.find((task) => task.status === 'running' || task.status === 'handoff') || tasks.at(-1) || null;
    const handoffs = state.handoffs.filter((handoff) => handoff.from_agent_id === agent.id || handoff.to_agent_id === agent.id);
    return {
      agent,
      worker,
      tasks,
      activeTask,
      handoffs,
      status: deriveStationStatus(agent, worker, tasks, handoffs),
      order: index,
    };
  });

  const tasksById = new Map(graphTasks.map((task) => [task.id, task]));
  const orderedTasks = graphTasks.toSorted((left, right) => (left.flow_position || 0) - (right.flow_position || 0));
  const edges: TaskEdgeViewModel[] = [];

  orderedTasks.forEach((task, index) => {
    const dependencyIds = task.dependencies?.length ? task.dependencies : index > 0 ? [orderedTasks[index - 1].id] : [];
    dependencyIds.forEach((dependencyId) => {
      const dependency = tasksById.get(dependencyId);
      if (!dependency) return;
      edges.push({
        id: `${dependency.id}-${task.id}`,
        fromTaskId: dependency.id,
        toTaskId: task.id,
        fromAgentId: dependency.assigned_agent_id,
        toAgentId: task.assigned_agent_id,
        status: deriveEdgeStatus(dependency, task),
      });
    });
  });

  return { stations, edges, handoffs: state.handoffs };
}

function minimumTaskOrder(tasks: WorkspaceTask[], agentId: string): number {
  let minimum = Number.MAX_SAFE_INTEGER;
  for (const task of tasks) {
    if (task.assigned_agent_id === agentId) minimum = Math.min(minimum, task.flow_position || minimum);
  }
  return minimum;
}

function roleOrder(role: string, preset: TeamPreset): number {
  const presetIndex = preset.roles.findIndex((item) => item.role === role);
  if (presetIndex >= 0) return presetIndex;
  const fallbackIndex = ROLE_ORDER.indexOf(role);
  return fallbackIndex >= 0 ? preset.roles.length + fallbackIndex : 999;
}

function pickWorker(workers: WorkspaceWorker[], agentId: string): WorkspaceWorker | null {
  const matching = workers.filter((worker) => worker.agent_id === agentId);
  return matching.find((worker) => worker.status === 'running' || worker.status === 'handoff_required') || matching.at(-1) || null;
}

function deriveStationStatus(
  agent: WorkspaceAgent,
  worker: WorkspaceWorker | null,
  tasks: WorkspaceTask[],
  handoffs: WorkspaceHandoff[],
): string {
  if (handoffs.some((handoff) => ['requested', 'summary_ready', 'accepted', 'in_progress'].includes(handoff.status))) return 'handoff';
  if (worker?.status === 'running' || tasks.some((task) => task.status === 'running')) return 'running';
  if (worker?.status === 'failed' || tasks.some((task) => task.status === 'failed' || task.status === 'blocked')) return 'error';
  if (tasks.length > 0 && tasks.every((task) => COMPLETE_STATUSES.has(task.status))) return 'done';
  if (tasks.length > 0) return 'waiting';
  return agent.status === 'disabled' ? 'disabled' : 'idle';
}

function deriveEdgeStatus(fromTask: WorkspaceTask, toTask: WorkspaceTask): TaskEdgeViewModel['status'] {
  if (fromTask.status === 'failed' || fromTask.status === 'blocked' || toTask.status === 'failed') return 'error';
  if (fromTask.status === 'handoff' || toTask.status === 'handoff') return 'handoff';
  if (COMPLETE_STATUSES.has(fromTask.status) && COMPLETE_STATUSES.has(toTask.status)) return 'done';
  if (toTask.status === 'running') return 'active';
  if (COMPLETE_STATUSES.has(fromTask.status)) return 'waiting';
  return 'planned';
}
