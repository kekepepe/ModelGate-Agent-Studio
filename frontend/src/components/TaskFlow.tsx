import { Children, type ReactNode } from 'react';

interface TaskFlowProps {
  taskCount: number;
  handoffCount: number;
  children: ReactNode;
}

/**
 * The Workspace's primary visual model: a readable serial flow of Tasks.
 *
 * The Runtime currently executes the generated plan serially. Keeping that
 * fact visible prevents the old Agent-board layout from implying parallel
 * work that the backend does not perform yet.
 */
export default function TaskFlow({ taskCount, handoffCount, children }: TaskFlowProps) {
  const taskCards = Children.toArray(children);

  return (
    <section aria-label="任务协作流" className="rounded-xl border border-stone-200 bg-white p-4 shadow-sm">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h3 className="text-sm font-semibold text-stone-800">任务协作流</h3>
          <p className="mt-1 text-xs leading-5 text-stone-500">
            当前计划按步骤串行推进；每一步都保留执行者、模型、风险与交接记录。
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2 text-[11px] text-stone-500">
          <span className="rounded-full bg-stone-100 px-2 py-1">{taskCount} 步</span>
          <span className="rounded-full bg-purple-50 px-2 py-1 text-purple-700">{handoffCount} 次交接</span>
        </div>
      </div>

      <ol className="space-y-0" aria-label="任务执行顺序">
        {taskCards.map((card, index) => {
          const isLast = index === taskCards.length - 1;
          return (
            <li key={`task-flow-step-${index}`} className="relative pl-9">
              {!isLast && <span aria-hidden="true" className="absolute left-[11px] top-8 h-[calc(100%+0.25rem)] w-px bg-stone-200" />}
              <span className="absolute left-0 top-3 flex h-6 w-6 items-center justify-center rounded-full border border-stone-300 bg-stone-50 text-[10px] font-semibold text-stone-600">
                {index + 1}
              </span>
              <div className={isLast ? '' : 'pb-3'}>{card}</div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
