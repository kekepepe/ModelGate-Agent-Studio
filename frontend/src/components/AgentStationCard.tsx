import type { WorkspaceAgent, WorkspaceWorker } from '../types/workspace';
import WorkerBadge from './WorkerBadge';

const ROLE_COLORS: Record<string, string> = {
  planner: 'bg-purple-100 text-purple-700',
  coder: 'bg-blue-100 text-blue-700',
  reviewer: 'bg-amber-100 text-amber-700',
  research: 'bg-green-100 text-green-700',
  summarizer: 'bg-sky-100 text-sky-700',
  supervisor: 'bg-red-100 text-red-700',
};

interface AgentStationCardProps {
  agent: WorkspaceAgent;
  worker?: WorkspaceWorker | null;
  tasks: { id: string; title: string; status: string; agent_id?: string | null }[];
  onTaskClick?: (taskId: string) => void;
}

export default function AgentStationCard({ agent, worker, tasks, onTaskClick }: AgentStationCardProps) {
  const agentTasks = tasks.filter((t) => t.agent_id === agent.id);
  const roleColor = ROLE_COLORS[agent.role] || 'bg-stone-100 text-stone-600';

  const borderColor = agent.status === 'running'
    ? 'border-blue-400'
    : agent.status === 'handoff'
    ? 'border-purple-400'
    : 'border-stone-200';

  return (
    <div className={`rounded-xl border ${borderColor} bg-white shadow-sm transition-colors duration-300`}>
      <div className="px-4 py-3 border-b border-stone-100 flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-sm font-semibold text-stone-800 truncate">{agent.name}</span>
          <span className={`inline-block px-1.5 py-0.5 text-[10px] font-medium rounded ${roleColor}`}>
            {agent.role}
          </span>
        </div>
        <div className="flex-shrink-0">
          <WorkerBadge
            modelName={worker?.model_name || agent.default_model_id}
            status={worker?.status || agent.status}
            totalTokensUsed={worker?.total_tokens_used}
          />
        </div>
      </div>

      <div className="px-4 py-2 space-y-1">
        {agentTasks.length === 0 && (
          <p className="text-xs text-stone-400 py-2">暂无任务</p>
        )}
        {agentTasks.map((task) => (
          <button
            key={task.id}
            onClick={() => onTaskClick?.(task.id)}
            className="w-full text-left px-2 py-1.5 rounded-lg text-sm text-stone-700 hover:bg-stone-50 transition-colors"
          >
            <span className="truncate block">{task.title}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
