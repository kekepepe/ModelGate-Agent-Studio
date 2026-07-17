import type { TaskStatus } from '../types/workspace';
import type { WorkspaceHandoff } from '../types/workspace';
import { TASK_STATUS_ICONS, TASK_STATUS_LABELS, TASK_STATUS_BORDERS, TASK_STATUS_BG } from '../types/workspace';

interface TaskCardProps {
  id: string;
  title: string;
  status: TaskStatus;
  priority?: number;
  tokensUsed?: number;
  onSelect?: (taskId: string) => void;
  isSelected?: boolean;
  handoffIndicator?: React.ReactNode;
  agentName?: string | null;
  modelName?: string | null;
  outputSnippet?: string | null;
  handoff?: WorkspaceHandoff | null;
  onRequestHandoff?: (taskId: string) => void;
  onOpenHandoff?: (handoffId: string) => void;
  quotaStatus?: string | null;
  quotaUsagePercent?: number | null;
  latestToolCall?: { tool_name: string; status: string } | null;
  changedFileCount?: number;
  testStatus?: string | null;
  blockedReason?: string | null;
  currentStep?: number;
  nextAction?: string | null;
}

export default function TaskCard({
  id,
  title,
  status,
  priority = 0,
  tokensUsed = 0,
  onSelect,
  isSelected = false,
  handoffIndicator,
  agentName,
  modelName,
  outputSnippet,
  handoff,
  onRequestHandoff,
  onOpenHandoff,
  quotaStatus,
  quotaUsagePercent,
  latestToolCall,
  changedFileCount = 0,
  testStatus,
  blockedReason,
  currentStep = 0,
  nextAction,
}: TaskCardProps) {
  const icon = TASK_STATUS_ICONS[status] || '•';
  const border = TASK_STATUS_BORDERS[status] || 'border-stone-200';
  const bg = TASK_STATUS_BG[status] || 'bg-white';

  const animationClass =
    status === 'running' ? 'animate-breathe' :
    status === 'failed' ? 'animate-shake' :
    status === 'handoff' ? 'animate-rotate-border' : '';

  return (
    <div
      onClick={() => onSelect?.(id)}
      className={`cursor-pointer rounded-lg border ${border} ${bg} p-3 transition-all duration-300 ${animationClass} ${isSelected ? 'ring-2 ring-blue-400' : 'hover:shadow-sm'}`}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter') onSelect?.(id); }}
    >
      <div className="flex items-start gap-2">
        <span className="text-lg leading-none mt-0.5 flex-shrink-0">{icon}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <p className="text-sm font-medium text-stone-800 truncate">{title}</p>
            {priority > 0 && (
              <span className="text-[10px] text-amber-600 border border-amber-200 bg-amber-50 px-1 rounded">
                P{priority}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 text-xs text-stone-400">
            <span>{TASK_STATUS_LABELS[status]}</span>
            {tokensUsed > 0 && <span>{tokensUsed.toLocaleString()} tokens</span>}
          </div>
          {(agentName || modelName) && (
            <div className="mt-2 flex flex-wrap gap-x-2 gap-y-1 text-[11px] text-stone-500">
              {agentName && <span>{agentName}</span>}
              {modelName && <span className="font-mono text-stone-400">{modelName}</span>}
            </div>
          )}
          {(currentStep > 0 || nextAction) && (
            <div className="mt-1 text-[10px] text-stone-500">步骤 {currentStep}{nextAction ? ` · ${nextAction}` : ''}</div>
          )}
          {quotaStatus && quotaStatus !== 'unknown' && (
            <div className={`mt-2 inline-flex rounded px-1.5 py-0.5 text-[10px] ${quotaStatus === 'limited' || quotaStatus === 'cooldown' ? 'bg-red-50 text-red-700' : quotaStatus === 'warning' || quotaStatus === 'near_limit' ? 'bg-amber-50 text-amber-700' : 'bg-green-50 text-green-700'}`}>
              额度 {quotaStatus}{quotaUsagePercent != null ? ` · ${Math.round(quotaUsagePercent * 100)}%` : ''}
            </div>
          )}
          {(latestToolCall || changedFileCount > 0 || testStatus) && (
            <div className="mt-2 flex flex-wrap gap-1.5 text-[10px] text-stone-600">
              {latestToolCall && <span className="rounded bg-stone-100 px-1.5 py-0.5">工具 {latestToolCall.tool_name} · {latestToolCall.status}</span>}
              {changedFileCount > 0 && <span className="rounded bg-blue-50 px-1.5 py-0.5 text-blue-700">文件 {changedFileCount}</span>}
              {testStatus && <span className={`rounded px-1.5 py-0.5 ${testStatus === 'completed' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>测试 {testStatus}</span>}
            </div>
          )}
        </div>
      </div>
      {outputSnippet && (
        <p className="mt-3 line-clamp-2 text-xs leading-relaxed text-stone-500 border-l-2 border-stone-200 pl-2">
          {outputSnippet}
        </p>
      )}
      {blockedReason && (
        <p className="mt-2 rounded bg-red-50 px-2 py-1 text-xs text-red-700 line-clamp-2">阻塞：{blockedReason}</p>
      )}
      {handoff && (
        <button
          type="button"
          onClick={(event) => { event.stopPropagation(); onOpenHandoff?.(handoff.id); }}
          className="mt-3 w-full text-left rounded-md border border-purple-200 bg-purple-50 px-2.5 py-2 text-xs text-purple-800 hover:bg-purple-100"
        >
          交接 {handoff.from_agent_name || '原 Agent'} → {handoff.to_agent_name || '接手 Agent'} · {handoff.status}
        </button>
      )}
      {!handoff && (status === 'running' || status === 'failed') && onRequestHandoff && (
        <button
          type="button"
          onClick={(event) => { event.stopPropagation(); onRequestHandoff(id); }}
          className="mt-3 rounded-md border border-stone-300 bg-white px-2.5 py-1.5 text-xs font-medium text-stone-600 hover:border-stone-500 hover:text-stone-900"
        >
          交接任务
        </button>
      )}
      {handoffIndicator}
    </div>
  );
}
