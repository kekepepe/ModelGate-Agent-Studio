import { ArrowRight, Folder, Info, Route } from 'lucide-react';
import AgentStationCard from './AgentStationCard';
import type { StationViewModel, TaskEdgeViewModel, WorkspaceViewModel } from '../utils/workspaceViewModel';

const EDGE_LABELS: Record<TaskEdgeViewModel['status'], string> = { planned: 'Planned', active: 'Active', done: 'Done', waiting: 'Waiting', handoff: 'Handoff', error: 'Blocked' };

interface CardFlowRendererProps {
  viewModel: WorkspaceViewModel;
  selectedTaskId?: string | null;
  onSelectTask: (taskId: string) => void;
  onOpenHandoff: (handoffId: string) => void;
}

export default function CardFlowRenderer({ viewModel, selectedTaskId, onSelectTask, onOpenHandoff }: CardFlowRendererProps) {
  const latestHandoff = viewModel.handoffs.at(-1);
  return (
    <section aria-label="Agent Flow" className="agent-flow-canvas">
      <header className="workspace-canvas-heading"><h2>Agent flow <Info size={13} /></h2><div className="agent-flow-legend"><Legend color="green" label="Done" /><Legend color="blue" label="Running" /><Legend color="amber" label="Waiting" /><Legend color="purple" label="Handoff" /></div></header>
      {viewModel.stations.length === 0 ? <div className="workspace-empty-state"><Route size={30} /><strong>Agent stations are ready</strong><span>创建并规划 Goal 后，工位将按真实任务流依次激活。</span></div> : <div className="agent-flow-scroll">
        <div className="agent-flow-stations">
          {viewModel.stations.map((station, index) => <div key={station.agent.id} className="agent-flow-station-wrap">
            <AgentStationCard agent={station.agent} worker={station.worker} tasks={station.tasks} status={station.status} handoffs={station.handoffs} isSelected={station.tasks.some((task) => task.id === selectedTaskId)} onStationClick={(_, taskId) => taskId && onSelectTask(taskId)} onTaskClick={onSelectTask} />
            {index < viewModel.stations.length - 1 ? <StationEdge from={station} to={viewModel.stations[index + 1]} edges={viewModel.edges} /> : null}
          </div>)}
        </div>
        <div className={`handoff-route ${latestHandoff ? 'is-active' : ''}`} aria-hidden="true"><span className="handoff-route-left" /><span className="handoff-route-line" /><span className="handoff-route-right" /></div>
        <button type="button" disabled={!latestHandoff} onClick={() => latestHandoff && onOpenHandoff(latestHandoff.id)} className="handoff-summary-card">
          <span className="handoff-summary-icon"><Folder size={22} fill="currentColor" /></span>
          <span className="handoff-summary-copy"><small>Handoff summary</small><strong>{latestHandoff?.reason_description || latestHandoff?.reason || 'No active handoff'}</strong><span>From: {latestHandoff?.from_agent_name || '—'} <ArrowRight size={11} /> To: {latestHandoff?.to_agent_name || '—'}</span></span>
          <time>{latestHandoff?.created_at ? formatRelative(latestHandoff.created_at) : '—'}</time>
        </button>
      </div>}
    </section>
  );
}

function StationEdge({ from, to, edges }: { from: StationViewModel; to: StationViewModel; edges: TaskEdgeViewModel[] }) {
  const edge = edges.find((item) => item.fromAgentId === from.agent.id && item.toAgentId === to.agent.id);
  const status = edge?.status || 'planned';
  return <div className={`station-edge station-edge--${status}`} aria-label={`${from.agent.name} 到 ${to.agent.name}：${EDGE_LABELS[status]}`}><span /><ArrowRight size={23} /></div>;
}

function Legend({ color, label }: { color: string; label: string }) { return <span><i className={`legend-dot legend-dot--${color}`} />{label}</span>; }

function formatRelative(value: string) {
  const seconds = Math.max(0, Math.round((Date.now() - new Date(value).getTime()) / 1000));
  if (seconds < 60) return `${seconds}s ago`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m ago`;
  return `${Math.round(seconds / 3600)}h ago`;
}
