import { ArrowRight, BrainCircuit, CheckCircle2, Code2, FileSearch, FileText, LoaderCircle, Terminal, Wrench } from 'lucide-react';
import type { WorkspaceAgent, WorkspaceHandoff, WorkspaceWorker } from '../types/workspace';

interface AgentStationCardProps {
  agent: WorkspaceAgent;
  worker?: WorkspaceWorker | null;
  tasks: Array<{ id: string; title: string; status: string; agent_id?: string | null; assigned_agent_id?: string | null; output?: string | null; tokens_used?: number; model_name?: string | null; quota?: { quota_status: string; usage_percent?: number | null; token_limit?: number | null } | null; latest_tool_call?: { tool_name: string; status: string } | null; next_action?: string | null; dependencies?: string[] }>;
  status?: string;
  handoffs?: WorkspaceHandoff[];
  isSelected?: boolean;
  onStationClick?: (agentId: string, taskId?: string) => void;
  onTaskClick?: (taskId: string) => void;
}

const STATUS: Record<string, { label: string; color: string }> = {
  idle: { label: 'Idle', color: 'gray' }, waiting: { label: 'Waiting', color: 'amber' }, running: { label: 'Running', color: 'blue' }, handoff: { label: 'Handoff', color: 'purple' }, done: { label: 'Done', color: 'green' }, completed: { label: 'Done', color: 'green' }, error: { label: 'Error', color: 'red' }, failed: { label: 'Error', color: 'red' }, disabled: { label: 'Disabled', color: 'gray' },
};

export default function AgentStationCard({ agent, worker, tasks, status, handoffs = [], isSelected = false, onStationClick, onTaskClick }: AgentStationCardProps) {
  const agentTasks = tasks.filter((task) => !task.assigned_agent_id || task.assigned_agent_id === agent.id);
  const currentTask = agentTasks.find((task) => ['running', 'handoff'].includes(task.status)) || agentTasks.at(-1);
  const stationStatus = status || agent.status;
  const statusStyle = STATUS[stationStatus] || STATUS.idle;
  const modelName = worker?.model_name || currentTask?.model_name || worker?.model_id || agent.default_model_id || 'Unassigned';
  const usage = currentTask?.tokens_used || worker?.total_tokens_used || 0;
  const tokenLimit = currentTask?.quota?.token_limit || Math.max(20_000, usage);
  const usagePercent = currentTask?.quota?.usage_percent ?? Math.min(100, Math.round((usage / tokenLimit) * 100));
  const latestHandoff = handoffs.at(-1);
  const outgoing = latestHandoff?.from_agent_id === agent.id;

  return (
    <article className={`agent-station agent-station--${statusStyle.color} ${isSelected ? 'is-selected' : ''}`}>
      <button type="button" className="agent-station-main" onClick={() => { if (currentTask) onTaskClick?.(currentTask.id); onStationClick?.(agent.id, currentTask?.id); }}>
        <header className="agent-station-header">
          <span className={`agent-status-dot agent-status-dot--${statusStyle.color}`} />
          <strong>{agent.name}</strong><span className={`agent-status-pill agent-status-pill--${statusStyle.color}`}>{statusStyle.label}</span>
          <span className="sr-only">{agent.role}</span>
        </header>
        <section className="agent-card-section agent-model-section">
          <span className="agent-section-label">Model</span>
          <div className="agent-model-row"><ModelIcon role={agent.role} /><strong>{shortModelName(modelName)}</strong></div>
        </section>
        <section className="agent-card-section">
          <span className="agent-section-label">Current task</span>
          <div className="agent-current-task"><TaskStateIcon status={currentTask?.status || stationStatus} /><span>{currentTask?.title || 'Awaiting task'}</span>{!currentTask ? <span className="sr-only">暂无任务</span> : null}</div>
        </section>
        <section className="agent-card-section agent-output-section">
          <span className="agent-section-label">Latest output</span>
          <p>{currentTask?.output || currentTask?.next_action || waitingMessage(currentTask?.status, stationStatus)}</p>
        </section>
        <section className="agent-card-section">
          <span className="agent-section-label">Usage (this run)</span>
          <div className="agent-usage-copy"><span>{usage.toLocaleString()} / {tokenLimit.toLocaleString()} tokens</span><strong>{Math.round(usagePercent)}%</strong></div>
          <div className="agent-usage-track"><span style={{ width: `${Math.min(100, usagePercent)}%` }} /></div>
        </section>
        <section className="agent-card-section">
          <span className="agent-section-label">{currentTask?.latest_tool_call ? 'Tools in use' : 'Tools'}</span>
          <div className="agent-tools"><span><Wrench size={12} />{currentTask?.latest_tool_call?.tool_name || defaultTools(agent.role)[0]}</span><span>{agent.role === 'coder' ? <Terminal size={12} /> : <FileText size={12} />}{defaultTools(agent.role)[1]}</span></div>
        </section>
        <section className={`agent-card-section agent-handoff-section ${latestHandoff ? 'has-handoff' : ''}`}>
          <span className="agent-section-label">Handoff {latestHandoff ? (outgoing ? '(outgoing)' : '(incoming)') : ''}</span>
          {latestHandoff ? <><p className="agent-handoff-party">{outgoing ? 'To' : 'From'}: <strong>{outgoing ? latestHandoff.to_agent_name || 'Target' : latestHandoff.from_agent_name || 'Source'}</strong></p><p>Reason: {latestHandoff.reason_description || latestHandoff.reason}</p></> : <p>{currentTask ? `Will ${stationStatus === 'done' ? 'handoff' : 'receive'} when ready` : 'No handoff planned'} <ArrowRight size={12} /></p>}
        </section>
      </button>
      {currentTask ? <button type="button" className="agent-card-detail-hit" onClick={() => onTaskClick?.(currentTask.id)} aria-label={`Open ${currentTask.title}`} /> : null}
    </article>
  );
}

function ModelIcon({ role }: { role: string }) {
  if (role === 'coder') return <span className="model-mark model-mark--blue"><Code2 size={20} /></span>;
  if (role === 'reviewer') return <span className="model-mark model-mark--green"><FileSearch size={20} /></span>;
  return <span className="model-mark model-mark--orange"><BrainCircuit size={20} /></span>;
}

function TaskStateIcon({ status }: { status: string }) {
  if (['done', 'completed', 'completed_verified', 'completed_unverified'].includes(status)) return <CheckCircle2 size={14} className="task-status-done" />;
  if (status === 'running') return <LoaderCircle size={14} className="agent-task-spinner" />;
  return <span className="agent-task-hourglass">⌛</span>;
}

function shortModelName(value: string) {
  if (/^[0-9a-f]{8}-[0-9a-f-]{27,}$/i.test(value)) return 'Configured Model';
  const parts = value.split(/[/:]/); return parts.at(-1) || value;
}

function defaultTools(role: string) {
  if (role === 'coder') return ['VS Code', 'Terminal'];
  if (role === 'reviewer') return ['Code Review', 'Files'];
  return ['Web Search', 'File Reader'];
}

function waitingMessage(taskStatus?: string, stationStatus?: string) {
  if (taskStatus === 'running') return 'Execution in progress. Waiting for the next verified output.';
  if (stationStatus === 'waiting') return 'Waiting for upstream task completion.';
  if (stationStatus === 'done') return 'Task completed and ready for the next station.';
  return 'No output yet.';
}
