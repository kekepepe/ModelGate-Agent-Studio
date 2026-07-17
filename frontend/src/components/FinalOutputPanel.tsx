import { useState } from 'react';
import { Copy, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import type { FinalSummary } from '../types/runtime';

interface TaskOutput {
  id: string;
  title: string;
  output: string;
}

interface FinalOutputPanelProps {
  output?: string | null;
  status: string;
  tasksCompleted: number;
  tasksFailed: number;
  tasksHandoff: number;
  tasksTotal?: number;
  totalTokens: number;
  logCount: number;
  finalSummary?: FinalSummary | null;
  taskOutputs?: TaskOutput[];
  onOpenTask?: (taskId: string) => void;
}

export default function FinalOutputPanel({
  output,
  status,
  tasksCompleted,
  tasksFailed,
  tasksHandoff,
  tasksTotal,
  totalTokens,
  logCount,
  finalSummary,
  taskOutputs = [],
  onOpenTask,
}: FinalOutputPanelProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!output) return;
    await navigator.clipboard?.writeText(output);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  const StatusIcon = status === 'completed' ? CheckCircle
    : status === 'failed' || status === 'cancelled' ? XCircle
    : AlertTriangle;

  const statusColor = status === 'completed' ? 'text-green-600'
    : status === 'failed' ? 'text-red-600'
    : status === 'cancelled' ? 'text-stone-500'
    : 'text-amber-600';

  const bgColor = status === 'completed' ? 'bg-green-50 border-green-200'
    : status === 'failed' ? 'bg-red-50 border-red-200'
    : status === 'cancelled' ? 'bg-stone-100 border-stone-300'
    : 'bg-amber-50 border-amber-200';

  return (
    <div className={`rounded-xl border ${bgColor} p-4`}>
      <div className="flex items-center gap-2 mb-3">
        <StatusIcon size={18} className={statusColor} />
        <h3 className="text-sm font-semibold text-stone-800">
          {status === 'completed' ? '执行完成，交付内容如下' : status === 'failed' ? '执行失败，可查看已产出内容' : status === 'cancelled' ? '运行已停止，保留当前状态与未完成项' : '任务执行中'}
        </h3>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-3 text-xs">
        <div className="bg-white/60 rounded-lg p-2 text-center">
          <div className="text-stone-400">Tasks</div>
          <div className="font-semibold text-stone-800">
            {tasksCompleted}/{tasksTotal ?? tasksCompleted + tasksFailed + tasksHandoff}
          </div>
        </div>
        <div className="bg-white/60 rounded-lg p-2 text-center">
          <div className="text-stone-400">Token</div>
          <div className="font-semibold text-stone-800">{totalTokens.toLocaleString()}</div>
        </div>
        <div className="bg-white/60 rounded-lg p-2 text-center">
          <div className="text-stone-400">日志</div>
          <div className="font-semibold text-stone-800">{logCount} 条</div>
        </div>
      </div>

      {output && (
        <div className="mt-2">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-semibold text-stone-500 uppercase">Final Output</span>
            <button
              onClick={handleCopy}
              className="inline-flex items-center gap-1 px-2 py-0.5 text-xs text-stone-500 hover:text-stone-800 border border-stone-200 rounded bg-white"
            >
              <Copy size={12} /> {copied ? '已复制' : '复制'}
            </button>
          </div>
          <pre className="text-sm text-stone-700 bg-white rounded-lg p-3 whitespace-pre-wrap break-words border border-stone-200 max-h-60 overflow-y-auto">
            {output}
          </pre>
        </div>
      )}

      {taskOutputs.length > 0 && (
        <section className="mt-4 border-t border-stone-200 pt-3" aria-label="任务产出">
          <h4 className="mb-2 text-xs font-semibold text-stone-700">任务产出</h4>
          <div className="space-y-2">
            {taskOutputs.map((task) => (
              <button
                key={task.id}
                type="button"
                onClick={() => onOpenTask?.(task.id)}
                className="w-full rounded-lg border border-stone-200 bg-white/70 px-3 py-2 text-left hover:border-stone-400"
              >
                <div className="text-xs font-medium text-stone-700">{task.title}</div>
                <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-stone-500">{task.output}</p>
              </button>
            ))}
          </div>
          <p className="mt-2 text-[11px] text-stone-400">点击任一项可在 Agent Detail Modal 中查看和复制完整内容。</p>
        </section>
      )}

      {tasksFailed > 0 && (
        <div className="mt-2 text-xs text-red-600">
          ⚠ {tasksFailed} 个任务执行失败
        </div>
      )}

      {tasksHandoff > 0 && (
        <div className="mt-1 text-xs text-purple-600">
          🔄 {tasksHandoff} 个任务已交接
        </div>
      )}

      {finalSummary && (
        <section className="mt-4 border-t border-stone-200 pt-3" aria-label="运行总结">
          <div className="mb-2 flex items-center justify-between gap-2">
            <h4 className="text-xs font-semibold text-stone-700">运行总结</h4>
            <span className={`rounded-full px-2 py-0.5 text-[10px] ${finalSummary.quality.passed === true ? 'bg-green-100 text-green-700' : finalSummary.quality.passed === false ? 'bg-amber-100 text-amber-800' : 'bg-stone-100 text-stone-600'}`}>
              {finalSummary.quality.passed === true ? '质量检查通过' : finalSummary.quality.passed === false ? '需要复核' : '尚无质量检查'}
            </span>
          </div>
          <dl className="grid grid-cols-2 gap-2 text-xs">
            <SummaryItem label="已完成" value={`${finalSummary.completed.length} 项`} />
            <SummaryItem label="未完成" value={`${finalSummary.incomplete.length} 项`} />
            <SummaryItem label="使用模型" value={finalSummary.models.map((model) => model.name).join('、') || '暂无'} />
            <SummaryItem label="交接次数" value={`${finalSummary.handoff_count} 次`} />
          </dl>
          {finalSummary.quality.summary && (
            <p className="mt-3 rounded-md bg-white/70 p-2 text-xs leading-5 text-stone-600">
              {finalSummary.quality.summary}
            </p>
          )}
          {finalSummary.risks.length > 0 && (
            <p className="mt-2 text-xs leading-5 text-amber-800">
              风险：{finalSummary.risks.join('；')}
            </p>
          )}
          <p className="mt-2 text-[11px] leading-4 text-stone-500">成本：{finalSummary.cost.note}</p>
        </section>
      )}
    </div>
  );
}

function SummaryItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md bg-white/60 p-2">
      <dt className="text-stone-400">{label}</dt>
      <dd className="mt-0.5 break-words font-medium text-stone-700">{value}</dd>
    </div>
  );
}
