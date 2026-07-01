import { useState } from 'react';
import { Copy, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

interface FinalOutputPanelProps {
  output?: string | null;
  status: string;
  tasksCompleted: number;
  tasksFailed: number;
  tasksHandoff: number;
  totalTokens: number;
  logCount: number;
}

export default function FinalOutputPanel({
  output,
  status,
  tasksCompleted,
  tasksFailed,
  tasksHandoff,
  totalTokens,
  logCount,
}: FinalOutputPanelProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!output) return;
    await navigator.clipboard?.writeText(output);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  const StatusIcon = status === 'completed' ? CheckCircle
    : status === 'failed' ? XCircle
    : AlertTriangle;

  const statusColor = status === 'completed' ? 'text-green-600'
    : status === 'failed' ? 'text-red-600'
    : 'text-amber-600';

  const bgColor = status === 'completed' ? 'bg-green-50 border-green-200'
    : status === 'failed' ? 'bg-red-50 border-red-200'
    : 'bg-amber-50 border-amber-200';

  return (
    <div className={`rounded-xl border ${bgColor} p-4`}>
      <div className="flex items-center gap-2 mb-3">
        <StatusIcon size={18} className={statusColor} />
        <h3 className="text-sm font-semibold text-stone-800">
          {status === 'completed' ? '执行完成' : status === 'failed' ? '执行失败' : '执行中'}
        </h3>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-3 text-xs">
        <div className="bg-white/60 rounded-lg p-2 text-center">
          <div className="text-stone-400">Tasks</div>
          <div className="font-semibold text-stone-800">
            {tasksCompleted}/{tasksCompleted + tasksFailed + tasksHandoff}
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
    </div>
  );
}
