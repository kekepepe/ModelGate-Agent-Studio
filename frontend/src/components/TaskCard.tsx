import type { TaskStatus, WorkspaceHandoff } from '../types/workspace';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { AgentStatusBadge } from './ui/agent-status-badge';
import { cn } from '@/lib/utils';

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

const PRIORITY_LABEL: Record<number, string> = { 0: 'P3', 1: 'P2', 2: 'P1', 3: 'P0' };

const QUOTA_TONE = {
  limited: 'bg-red-50 text-red-700 border-red-200',
  cooldown: 'bg-red-50 text-red-700 border-red-200',
  warning: 'bg-amber-50 text-amber-700 border-amber-200',
  near_limit: 'bg-amber-50 text-amber-700 border-amber-200',
  healthy: 'bg-emerald-50 text-emerald-700 border-emerald-200',
} as const;

function quotaToneClass(q?: string | null): string {
  if (!q) return QUOTA_TONE.healthy;
  return (QUOTA_TONE as Record<string, string>)[q] ?? QUOTA_TONE.healthy;
}

export default function TaskCard(props: TaskCardProps) {
  const {
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
    onOpenHandoff,
    quotaStatus,
    quotaUsagePercent,
    latestToolCall,
    changedFileCount,
    testStatus,
    blockedReason,
    currentStep,
    nextAction,
  } = props;

  return (
    <Card
      data-task-card-id={id}
      data-task-status={status}
      className={cn(
        'cursor-pointer gap-0 p-0 transition-shadow',
        isSelected && 'ring-2 ring-blue-400',
        status === 'running' && 'shadow-sm',
      )}
      onClick={onSelect ? () => onSelect(id) : undefined}
      role="button"
      tabIndex={0}
      onKeyDown={
        onSelect
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onSelect(id);
              }
            }
          : undefined
      }
    >
      <CardContent className="space-y-2 p-3">
        {/* Title row */}
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-stone-900" title={title}>
              {title}
            </p>
            {agentName && (
              <p className="mt-0.5 text-[10px] text-stone-500" title={agentName}>
                {agentName}
              </p>
            )}
          </div>
          <div className="flex shrink-0 items-center gap-1">
            {priority > 0 && (
              <Badge variant="outline" className="text-[10px] font-mono">
                {PRIORITY_LABEL[priority] ?? `P${priority}`}
              </Badge>
            )}
            <AgentStatusBadge state={status} dot className="text-[10px]" />
          </div>
        </div>

        {/* Handoff indicator / output snippet */}
        {handoffIndicator}
        {outputSnippet && (
          <p
            className="line-clamp-2 rounded border border-stone-200 bg-stone-50 p-1.5 text-[11px] text-stone-600"
            title={outputSnippet}
          >
            {outputSnippet}
          </p>
        )}

        {/* Handoff block */}
        {handoff && (
          <button
            type="button"
            aria-label={`View handoff: ${handoff.reason}`}
            onClick={(e) => {
              e.stopPropagation();
              onOpenHandoff?.(handoff.id);
            }}
            className="w-full rounded border border-violet-200 bg-violet-50 p-1.5 text-left text-[10px] text-violet-800 hover:bg-violet-100"
          >
            <div className="flex items-center justify-between">
              <span className="font-medium">Handoff</span>
              <span>{handoff.reason}</span>
            </div>
            {onOpenHandoff && (
              <div className="mt-0.5 text-violet-600">点击查看 →</div>
            )}
          </button>
        )}

        {/* Meta row: tokens + step + next action */}
        <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[10px] text-stone-500">
          {tokensUsed > 0 && (
            <span className="font-mono">{tokensUsed.toLocaleString()} tok</span>
          )}
          {modelName && (
            <>
              <span aria-hidden>·</span>
              <span className="font-mono text-stone-600">{modelName}</span>
            </>
          )}
          {currentStep !== undefined && (
            <>
              <span aria-hidden>·</span>
              <span>步骤 {currentStep}</span>
            </>
          )}
          {nextAction && (
            <>
              <span aria-hidden>·</span>
              <span className="italic">{nextAction}</span>
            </>
          )}
        </div>

        {/* Quota + tools row */}
        {(quotaStatus || latestToolCall || (changedFileCount ?? 0) > 0 || testStatus) && (
          <div className="flex flex-wrap gap-1.5 text-[10px]">
            {quotaStatus && (
              <span
                className={cn(
                  'rounded border px-1.5 py-0.5',
                  quotaToneClass(quotaStatus),
                )}
                title={typeof quotaUsagePercent === 'number' ? `${quotaUsagePercent}%` : quotaStatus}
              >
                quota {typeof quotaUsagePercent === 'number' ? `${quotaUsagePercent}%` : quotaStatus}
              </span>
            )}
            {latestToolCall && (
              <span className="rounded border border-stone-200 bg-stone-50 px-1.5 py-0.5 text-stone-700">
                {latestToolCall.tool_name} · {latestToolCall.status}
              </span>
            )}
            {(changedFileCount ?? 0) > 0 && (
              <span className="rounded border border-blue-200 bg-blue-50 px-1.5 py-0.5 text-blue-700">
                文件 {changedFileCount}
              </span>
            )}
            {testStatus && (
              <span className="rounded border border-stone-200 bg-stone-50 px-1.5 py-0.5 text-stone-700">
                test: {testStatus}
              </span>
            )}
          </div>
        )}

        {/* Blocked reason */}
        {blockedReason && (
          <p className="rounded border border-red-200 bg-red-50 px-1.5 py-1 text-[10px] text-red-700">
            {blockedReason}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
