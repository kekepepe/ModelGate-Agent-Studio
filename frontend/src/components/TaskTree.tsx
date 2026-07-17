import { CheckCircle2, ChevronDown, Circle, CircleDot, ListTree } from 'lucide-react';
import type { WorkspaceTask } from '../types/workspace';

interface TaskTreeProps {
  tasks: WorkspaceTask[];
  goalTitle?: string | null;
  onTaskClick?: (taskId: string) => void;
  selectedTaskId?: string | null;
}

const COMPLETE = new Set(['completed', 'completed_verified', 'completed_unverified']);

export default function TaskTree({ tasks, goalTitle, onTaskClick, selectedTaskId }: TaskTreeProps) {
  const groups = groupTasks(tasks);
  return (
    <section className="task-tree-panel">
      <header className="task-tree-heading"><ListTree size={17} /><h3>Task tree</h3></header>
      {tasks.length === 0 ? <p className="task-tree-empty">暂无任务</p> : <>
        <div className="task-tree-root"><ChevronDown size={12} /><span>{goalTitle || 'Current goal'}</span></div>
        <div className="task-tree-groups">
          {groups.map((group, groupIndex) => <div key={group.key} className="task-tree-group">
            <div className="task-tree-stage"><ChevronDown size={11} /><strong>{groupIndex + 1}. {group.label}</strong><StageStatus tasks={group.tasks} /></div>
            <div className="task-tree-items">
              {group.tasks.map((task, taskIndex) => {
                const selected = task.id === selectedTaskId;
                return <button key={task.id} type="button" onClick={() => onTaskClick?.(task.id)} className={selected ? 'is-selected bg-stone-100' : ''}>
                  <span>{groupIndex + 1}.{taskIndex + 1}</span><span className="task-tree-title">{task.title}</span><TaskStatus status={task.status} />
                </button>;
              })}
            </div>
          </div>)}
        </div>
        <button type="button" className="sidebar-text-link task-tree-link">View full task tree</button>
        <span className="sr-only">{tasks.length} 个 Task · {tasks.filter((task) => task.status === 'running').length} 个进行中 · {tasks.filter((task) => COMPLETE.has(task.status)).length} 个已完成</span>
      </>}
    </section>
  );
}

function groupTasks(tasks: WorkspaceTask[]) {
  const groups: Array<{ key: string; label: string; tasks: WorkspaceTask[] }> = [];
  const byKey = new Map<string, typeof groups[number]>();
  tasks.toSorted((a, b) => (a.flow_position || 0) - (b.flow_position || 0)).forEach((task) => {
    const key = task.assigned_agent_id || task.agent_role || 'unassigned';
    let group = byKey.get(key);
    if (!group) {
      group = { key, label: task.agent_name || roleLabel(task.agent_role) || titleStage(task.title), tasks: [] };
      groups.push(group); byKey.set(key, group);
    }
    group.tasks.push(task);
  });
  return groups;
}

function titleStage(title: string) {
  const value = title.toLowerCase();
  if (value.startsWith('plan')) return 'Planning & Breakdown';
  if (value.startsWith('build') || value.startsWith('implement')) return 'Implementation';
  if (value.startsWith('review')) return 'Code Review';
  if (value.startsWith('research')) return 'Research';
  if (value.startsWith('write') || value.startsWith('document')) return 'Documentation';
  return 'Execution';
}

function roleLabel(role?: string | null) {
  const labels: Record<string, string> = { planner: 'Planning & Breakdown', coder: 'Implementation', reviewer: 'Code Review', research: 'Research', summarizer: 'Documentation', supervisor: 'Final Review' };
  return role ? labels[role] || role : '';
}

function StageStatus({ tasks }: { tasks: WorkspaceTask[] }) {
  if (tasks.every((task) => COMPLETE.has(task.status))) return <CheckCircle2 size={11} className="task-status-done" />;
  if (tasks.some((task) => task.status === 'running')) return <CircleDot size={11} className="task-status-running" />;
  return <Circle size={10} className="task-status-idle" />;
}

function TaskStatus({ status }: { status: string }) {
  if (COMPLETE.has(status)) return <CheckCircle2 size={11} className="task-status-done" />;
  if (status === 'running') return <CircleDot size={11} className="task-status-running" />;
  if (status === 'failed' || status === 'blocked') return <CircleDot size={11} className="task-status-error" />;
  return <Circle size={10} className="task-status-idle" />;
}
