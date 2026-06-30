import type { Goal, WorkspaceTask } from '../types/workspace';
import { GOAL_STATUS_LABELS, GOAL_STATUS_COLORS } from '../types/workspace';

interface TopStatusBarProps {
  goal?: Goal | null;
  tasks?: WorkspaceTask[];
}

export default function TopStatusBar({ goal, tasks = [] }: TopStatusBarProps) {
  if (!goal) return null;

  const completedCount = tasks.filter((t) => t.status === 'completed').length;
  const totalCount = tasks.length;
  const runningCount = tasks.filter((t) => t.status === 'running').length;
  const handoffCount = tasks.filter((t) => t.status === 'handoff').length;
  const totalTokens = tasks.reduce((sum, t) => sum + (t.tokens_used || 0), 0);

  const statusColor = GOAL_STATUS_COLORS[goal.status] || GOAL_STATUS_COLORS.idle;
  const statusLabel = GOAL_STATUS_LABELS[goal.status] || goal.status;

  return (
    <div className="bg-white border-b border-stone-200 px-4 sm:px-6 lg:px-8 py-3">
      <div className="flex items-center justify-between max-w-full">
        <div className="flex items-center gap-3 min-w-0">
          <h1 className="text-base font-semibold text-stone-900 truncate max-w-md">
            Goal: {goal.title}
          </h1>
          <span className={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full border transition-colors duration-300 ${statusColor}`}>
            {statusLabel}
          </span>
        </div>
        <div className="flex items-center gap-4 text-xs text-stone-500 flex-shrink-0">
          <span>进度: {completedCount}/{totalCount} Tasks</span>
          {runningCount > 0 && <span className="text-blue-600">{runningCount} 运行中</span>}
          {handoffCount > 0 && <span className="text-purple-600">{handoffCount} 交接中</span>}
          <span>Token: {totalTokens.toLocaleString()}</span>
        </div>
      </div>
    </div>
  );
}
