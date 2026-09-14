import { CheckCircle2, ChevronDown, Circle, CircleDot, ListTree } from 'lucide-react';
import { Button } from './ui/button';
import { AgentStatusBadge } from './ui/agent-status-badge';
import { cn } from '@/lib/utils';
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
    <section className="space-y-2 p-3">
      <header className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-stone-700">
        <ListTree size={15} aria-hidden />
        <h3>Task tree</h3>
      </header>
      {tasks.length === 0 ? (
        <p className="text-[11px] italic text-stone-400">暂无任务</p>
      ) : (
        <>
          <div className="flex items-center gap-1 text-[11px] text-stone-500">
            <ChevronDown size={11} aria-hidden />
            <span>{goalTitle || 'Current goal'}</span>
          </div>
          <div className="space-y-2">
            {groups.map((group, groupIndex) => (
              <div key={group.key} className="space-y-1 rounded-md border border-stone-200 bg-white p-2">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="flex items-center gap-1 font-semibold text-stone-700">
                    <ChevronDown size={10} aria-hidden />
                    {groupIndex + 1}. {group.label}
                  </span>
                  <StageStatus tasks={group.tasks} />
                </div>
                <div className="space-y-0.5">
                  {group.tasks.map((task, taskIndex) => {
                    const selected = task.id === selectedTaskId;
                    return (
                      <Button
                        key={task.id}
                        type="button"
                        variant={selected ? 'secondary' : 'ghost'}
                        size="sm"
                        onClick={() => onTaskClick?.(task.id)}
                        className={cn(
                          'h-7 w-full justify-start gap-1.5 px-2 text-[11px] font-normal',
                        )}
                        aria-pressed={selected}
                      >
                        <span className="text-stone-400 tabular-nums">
                          {groupIndex + 1}.{taskIndex + 1}
                        </span>
                        <span className="flex-1 truncate text-left">{task.title}</span>
                        <TaskStatus status={task.status} />
                      </Button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
          <span className="sr-only">
            {tasks.length} 个 Task · {tasks.filter((task) => task.status === 'running').length} 个进行中 ·{' '}
            {tasks.filter((task) => COMPLETE.has(task.status)).length} 个已完成
          </span>
        </>
      )}
    </section>
  );
}

function groupTasks(tasks: WorkspaceTask[]) {
  const groups: Array<{ key: string; label: string; tasks: WorkspaceTask[] }> = [];
  const byKey = new Map<string, typeof groups[number]>();
  tasks
    .toSorted((a, b) => (a.flow_position || 0) - (b.flow_position || 0))
    .forEach((task) => {
      const key = task.assigned_agent_id || task.agent_role || 'unassigned';
      let group = byKey.get(key);
      if (!group) {
        group = {
          key,
          label: task.agent_name || roleLabel(task.agent_role) || titleStage(task.title),
          tasks: [],
        };
        groups.push(group);
        byKey.set(key, group);
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
  if (value.startsWith('sum')) return 'Summary';
  return 'Stage';
}

function roleLabel(role?: string | null) {
  if (!role) return '';
  return role.charAt(0).toUpperCase() + role.slice(1);
}

function TaskStatus({ status }: { status: string }) {
  if (status === 'running') return <CircleDot size={11} className="text-blue-500 animate-pulse" aria-hidden />;
  if (COMPLETE.has(status)) return <CheckCircle2 size={11} className="text-emerald-600" aria-hidden />;
  if (status === 'failed' || status === 'blocked') return <Circle size={11} className="text-red-600" aria-hidden />;
  return <Circle size={11} className="text-stone-400" aria-hidden />;
}

function StageStatus({ tasks }: { tasks: WorkspaceTask[] }) {
  if (tasks.length === 0) return null;
  const running = tasks.filter((t) => t.status === 'running').length;
  const done = tasks.filter((t) => COMPLETE.has(t.status)).length;
  if (running > 0) return <AgentStatusBadge state="running" label={`${done}/${tasks.length}`} dot={false} className="px-1.5 py-0 text-[10px]" />;
  if (done === tasks.length) return <AgentStatusBadge state="completed" label="done" dot={false} className="px-1.5 py-0 text-[10px]" />;
  return <span className="text-[10px] tabular-nums text-stone-500">{done}/{tasks.length}</span>;
}
