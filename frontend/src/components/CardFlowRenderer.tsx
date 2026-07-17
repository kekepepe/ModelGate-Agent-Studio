import { ArrowRight, GitBranch } from 'lucide-react';
import AgentStationCard from './AgentStationCard';
import type { StationViewModel, TaskEdgeViewModel, WorkspaceViewModel } from '../utils/workspaceViewModel';

const EDGE_STYLES: Record<TaskEdgeViewModel['status'], { line: string; label: string }> = {
  planned: { line: 'border-stone-300 border-dashed text-stone-300', label: 'Planned' },
  active: { line: 'border-blue-500 text-blue-500', label: 'Active' },
  done: { line: 'border-emerald-500 text-emerald-500', label: 'Done' },
  waiting: { line: 'border-amber-400 border-dashed text-amber-500', label: 'Waiting' },
  handoff: { line: 'border-purple-500 border-dashed text-purple-600', label: 'Handoff' },
  error: { line: 'border-red-500 text-red-600', label: 'Blocked' },
};

interface CardFlowRendererProps {
  viewModel: WorkspaceViewModel;
  selectedTaskId?: string | null;
  onSelectTask: (taskId: string) => void;
  onOpenHandoff: (handoffId: string) => void;
}

export default function CardFlowRenderer({ viewModel, selectedTaskId, onSelectTask, onOpenHandoff }: CardFlowRendererProps) {
  return (
    <section aria-label="Agent 工位协作流" className="min-h-full rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
      <header className="mb-5 flex items-start justify-between gap-4">
        <div>
          <h2 className="text-sm font-semibold text-stone-900">Agent Station Flow</h2>
          <p className="mt-1 text-xs leading-5 text-stone-500">工位并排展示团队结构；状态、连线和 Worker 只表达真实运行数据。</p>
        </div>
        <div className="flex items-center gap-3 text-[10px] text-stone-500">
          <Legend color="bg-emerald-500" label="Done" />
          <Legend color="bg-blue-500" label="Running" />
          <Legend color="bg-amber-500" label="Waiting" />
          <Legend color="bg-purple-500" label="Handoff" />
        </div>
      </header>

      {viewModel.stations.length === 0 ? (
        <div className="flex min-h-[420px] items-center justify-center rounded-xl border border-dashed border-stone-300 bg-stone-50 text-sm text-stone-400">
          启动 Goal 后，Agent 工位将在这里依次激活。
        </div>
      ) : (
        <div className="overflow-x-auto pb-4">
          <div className="flex min-w-max items-center gap-0 px-1 py-3">
            {viewModel.stations.map((station, index) => (
              <div key={station.agent.id} className="flex items-center">
                <AgentStationCard
                  agent={station.agent}
                  worker={station.worker}
                  tasks={station.tasks}
                  status={station.status}
                  handoffs={station.handoffs}
                  isSelected={station.tasks.some((task) => task.id === selectedTaskId)}
                  onStationClick={(_, taskId) => { if (taskId) onSelectTask(taskId); }}
                  onTaskClick={onSelectTask}
                />
                {index < viewModel.stations.length - 1 ? (
                  <StationEdge from={station} to={viewModel.stations[index + 1]} edges={viewModel.edges} />
                ) : null}
              </div>
            ))}
          </div>
        </div>
      )}

      {viewModel.handoffs.length > 0 ? (
        <div className="mt-4 border-t border-stone-100 pt-4">
          <h3 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-purple-700"><GitBranch size={14} /> Handoff summaries</h3>
          <div className="mt-3 grid gap-2 lg:grid-cols-2">
            {viewModel.handoffs.map((handoff) => (
              <button key={handoff.id} type="button" onClick={() => onOpenHandoff(handoff.id)} className="flex items-center justify-between gap-3 rounded-lg border border-purple-200 bg-purple-50 px-3 py-2 text-left hover:border-purple-300">
                <div className="min-w-0">
                  <p className="truncate text-xs font-semibold text-purple-900">{handoff.from_agent_name || 'Source'} → {handoff.to_agent_name || 'Target'}</p>
                  <p className="mt-0.5 truncate text-[11px] text-purple-700">{handoff.reason_description || handoff.reason}</p>
                </div>
                <span className="shrink-0 text-[10px] font-medium uppercase tracking-wide text-purple-600">{handoff.status}</span>
              </button>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}

function StationEdge({ from, to, edges }: { from: StationViewModel; to: StationViewModel; edges: TaskEdgeViewModel[] }) {
  const edge = edges.find((item) => item.fromAgentId === from.agent.id && item.toAgentId === to.agent.id);
  const style = EDGE_STYLES[edge?.status || 'planned'];
  return (
    <div className="flex w-20 shrink-0 flex-col items-center px-2" aria-label={`${from.agent.name} 到 ${to.agent.name}：${style.label}`}>
      <span className="mb-1 text-[9px] font-medium uppercase tracking-wide text-stone-400">{style.label}</span>
      <div className={`relative w-full border-t-2 ${style.line}`}>
        <ArrowRight size={15} className="absolute -right-1.5 -top-[8px] bg-white" />
      </div>
    </div>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return <span className="flex items-center gap-1"><span className={`h-2 w-2 rounded-full ${color}`} /> {label}</span>;
}
