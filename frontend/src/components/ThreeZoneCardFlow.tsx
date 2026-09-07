import { useMemo } from 'react';
import { Info, Route } from 'lucide-react';
import TaskCard from './TaskCard';
import { AgentStatusBadge } from './ui/agent-status-badge';
import { cn } from '@/lib/utils';
import type { WorkspaceViewModel } from '../utils/workspaceViewModel';
import type { WorkspaceTask } from '../types/workspace';

/**
 * V1.0-6c — ThreeZoneCardFlow.
 *
 * Inspired by Star-Office-UI's 3-zone pixel office layout
 * (ringhyacinth/Star-Office-UI, 7K+ stars, Feb 2026): the canvas is
 * divided into three regions (Breakroom / Writing Desk / Bug Area)
 * and agent characters walk between them based on their state.
 *
 * Adapted to ModelGate:
 *   - Pixel canvas -> CSS Grid 3 columns
 *   - Character walking between zones -> TaskCard grouped by status
 *   - Region state -> aggregate zone header badge + count
 *
 * TaskCard itself is unchanged for V1.0-6c; it gets the shadcn
 * refactor in V1.0-7.
 */

const ZONE_DEFS: Array<{
  key: 'rest' | 'working' | 'problem';
  title: string;
  subtitle: string;
  stateForBadge: string; // the "canonical" state used for the header badge
  statuses: string[];
  // Light tints used as the column header background (OKLCH ≈ V1.0-5
  // state tokens, lightened for header readability).
  tint: string;
}> = [
  {
    key: 'rest',
    title: 'Rest / 等待',
    subtitle: '空闲或待命的任务（idle / pending / queued / cancelled）',
    stateForBadge: 'idle',
    statuses: ['idle', 'pending', 'queued', 'cancelled', 'disabled', 'skipped', 'completed', 'done', 'stopped'],
    tint: 'oklch(0.97 0.01 240)',
  },
  {
    key: 'working',
    title: 'Working / 工作中',
    subtitle: '正在执行的任务（running / writing / researching / executing / syncing）',
    stateForBadge: 'running',
    statuses: ['running', 'writing', 'researching', 'executing', 'syncing', 'reviewing', 'started', 'finishing', 'in_progress'],
    tint: 'oklch(0.97 0.02 244)',
  },
  {
    key: 'problem',
    title: 'Problem / 异常',
    subtitle: '需要人介入（failed / error / handoff / blocked / paused）',
    stateForBadge: 'error',
    statuses: ['failed', 'error', 'handoff', 'handoff_required', 'blocked', 'paused', 'revision_required', 'waiting_approval'],
    tint: 'oklch(0.97 0.02 27)',
  },
];

function zoneForStatus(status: string): 'rest' | 'working' | 'problem' {
  for (const zone of ZONE_DEFS) {
    if (zone.statuses.includes(status)) return zone.key;
  }
  // Unknown status falls into 'rest' (safer default — visible but not alarming)
  return 'rest';
}

interface ThreeZoneCardFlowProps {
  viewModel: WorkspaceViewModel;
  selectedTaskId?: string | null;
  onSelectTask: (taskId: string) => void;
}

export default function ThreeZoneCardFlow({
  viewModel,
  selectedTaskId,
  onSelectTask,
}: ThreeZoneCardFlowProps) {
  // Flat-collect all tasks across stations, group by zone
  const allTasks: WorkspaceTask[] = useMemo(
    () => viewModel.stations.flatMap((s) => s.tasks),
    [viewModel],
  );

  const grouped = useMemo(() => {
    const buckets: Record<'rest' | 'working' | 'problem', WorkspaceTask[]> = {
      rest: [],
      working: [],
      problem: [],
    };
    for (const t of allTasks) {
      buckets[zoneForStatus(t.status)].push(t);
    }
    return buckets;
  }, [allTasks]);

  const total = allTasks.length;

  return (
    <section
      aria-label="Three-zone card flow (仿 Star-Office-UI 3 区布局)"
      className="flex h-full min-h-0 flex-col"
    >
      <header className="workspace-canvas-heading flex shrink-0 items-center justify-between border-b border-stone-200 bg-white px-4 py-2">
        <h2 className="flex items-center gap-2 text-sm font-semibold text-stone-800">
          <Info size={13} /> 3 区 Card Flow
        </h2>
        <div className="flex items-center gap-3 text-[11px] text-stone-500">
          <span>{total} 任务</span>
          <span aria-hidden>·</span>
          <span className="italic">仿 Star-Office-UI Breakroom / Writing Desk / Bug Area</span>
        </div>
      </header>

      {total === 0 ? (
        <div className="workspace-empty-state">
          <Route size={30} />
          <strong>暂无 Task</strong>
          <span>创建并规划 Goal 后，Task 会按状态自动落入 3 个区。</span>
        </div>
      ) : (
        <div
          className="grid min-h-0 flex-1 gap-2 p-2"
          style={{ gridTemplateColumns: '1fr 1.4fr 1fr' }}
        >
          {ZONE_DEFS.map((zone) => {
            const tasks = grouped[zone.key];
            return (
              <div
                key={zone.key}
                className="flex min-h-0 flex-col rounded-lg border border-stone-200 bg-white"
              >
                <header
                  className={cn(
                    'flex shrink-0 items-center justify-between border-b border-stone-200 px-3 py-2',
                  )}
                  style={{ backgroundColor: zone.tint }}
                >
                  <div className="min-w-0">
                    <h3 className="truncate text-xs font-semibold uppercase tracking-wider text-stone-700">
                      {zone.title}
                    </h3>
                    <p className="truncate text-[10px] text-stone-500" title={zone.subtitle}>
                      {zone.subtitle}
                    </p>
                  </div>
                  <AgentStatusBadge
                    state={zone.stateForBadge}
                    label={tasks.length.toString()}
                    dot
                    className="px-1.5 py-0 font-mono text-[10px]"
                  />
                </header>
                <div className="flex-1 overflow-y-auto p-2">
                  {tasks.length === 0 ? (
                    <p className="px-2 py-4 text-center text-[11px] italic text-stone-400">
                      暂无可显示的 Task
                    </p>
                  ) : (
                    <ul className="space-y-2">
                      {tasks.map((task) => (
                        <li key={task.id}>
                          <TaskCard
                            id={task.id}
                            title={task.title}
                            status={task.status as never}
                            tokensUsed={task.tokens_used ?? 0}
                            agentName={task.agent_name ?? null}
                            modelName={task.model_name ?? null}
                            onSelect={onSelectTask}
                            isSelected={task.id === selectedTaskId}
                            handoffIndicator={undefined}
                            outputSnippet={null}
                            handoff={null}
                            onRequestHandoff={undefined}
                            onOpenHandoff={undefined}
                            quotaStatus={null}
                            quotaUsagePercent={null}
                            latestToolCall={null}
                            changedFileCount={undefined}
                            testStatus={null}
                            blockedReason={null}
                            currentStep={undefined}
                            nextAction={null}
                            priority={task.priority ?? 0}
                          />
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
