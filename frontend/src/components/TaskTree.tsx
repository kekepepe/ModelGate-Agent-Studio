import type { WorkspaceTask } from '../types/workspace';
import { TASK_STATUS_ICONS } from '../types/workspace';

interface TaskTreeProps {
  tasks: WorkspaceTask[];
  onTaskClick?: (taskId: string) => void;
  selectedTaskId?: string | null;
}

export default function TaskTree({ tasks, onTaskClick, selectedTaskId }: TaskTreeProps) {
  const runningCount = tasks.filter((t) => t.status === 'running').length;
  const completedCount = tasks.filter((t) => t.status === 'completed').length;

  return (
    <div className="p-3">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-stone-400 mb-2">任务列表</h3>
      {tasks.length === 0 ? (
        <p className="text-xs text-stone-400">暂无任务</p>
      ) : (
        <div className="space-y-0.5">
          {tasks.map((task) => {
            const isSelected = selectedTaskId === task.id;
            const isRunning = task.status === 'running';
            return (
              <button
                key={task.id}
                onClick={() => onTaskClick?.(task.id)}
                className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-lg text-left text-xs transition-colors ${
                  isSelected ? 'bg-stone-100' : 'hover:bg-stone-50'
                } ${isRunning ? 'border-l-2 border-l-blue-500' : 'border-l-2 border-l-transparent'}`}
              >
                <span className="text-sm flex-shrink-0">{TASK_STATUS_ICONS[task.status] || '•'}</span>
                <span className="text-stone-700 truncate flex-1">{task.title}</span>
              </button>
            );
          })}
        </div>
      )}
      <div className="mt-3 pt-2 border-t border-stone-100 text-[10px] text-stone-400">
        {tasks.length} 个 Task · {runningCount} 个进行中 · {completedCount} 个已完成
      </div>
    </div>
  );
}
