import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Copy, ExternalLink, X } from 'lucide-react';
import type { ExecutionLog } from '../types/log';
import { LOG_EVENT_TYPE_LABELS, LOG_EVENT_STATUS_LABELS, LOG_EVENT_STATUS_COLORS } from '../types/log';

interface LogDetailDrawerProps {
  log?: ExecutionLog | null;
  onClose: () => void;
}

export default function LogDetailDrawer({ log, onClose }: LogDetailDrawerProps) {
  const [copiedField, setCopiedField] = useState<string | null>(null);

  if (!log) return null;

  const handleCopy = async (text: string, field: string) => {
    if (!text) return;
    await navigator.clipboard?.writeText(text);
    setCopiedField(field);
    window.setTimeout(() => setCopiedField(null), 2000);
  };

  const statusClass = LOG_EVENT_STATUS_COLORS[log.event_status] || 'bg-stone-100 text-stone-600 border-stone-200';

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/30" onClick={onClose}>
      <aside
        className="h-full w-full sm:w-[480px] xl:w-[560px] bg-white shadow-xl border-l border-stone-200 flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 z-10 bg-white px-5 py-4 border-b border-stone-200 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg">{log.event_type}</span>
              <span className={`inline-flex items-center px-1.5 py-0.5 text-[10px] font-medium rounded border ${statusClass}`}>
                {LOG_EVENT_STATUS_LABELS[log.event_status] || log.event_status}
              </span>
            </div>
            <h2 className="text-lg font-semibold text-stone-900 truncate">
              {LOG_EVENT_TYPE_LABELS[log.event_type] || log.event_type}
            </h2>
            <p className="text-xs text-stone-400 font-mono mt-1">{log.id}</p>
          </div>
          <button onClick={onClose} aria-label="close drawer" className="text-stone-400 hover:text-stone-700">
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          <section className="grid grid-cols-2 gap-3 text-sm">
            <Field label="Goal" value={log.goal_id} />
            <Field label="Task" value={log.task_title || log.task_id} link={log.task_id ? `/handoffs?task_id=${log.task_id}` : undefined} />
            <Field label="Agent" value={log.agent_name || log.agent_id} link={log.agent_id ? `/agents` : undefined} />
            <Field label="Model" value={log.model_name || log.model_id} />
            <Field label="Worker" value={log.worker_id} />
            <Field label="Handoff" value={log.handoff_id} link={log.handoff_id ? `/handoffs` : undefined} />
            <div className="col-span-2">
              <span className="text-xs text-stone-400">时间: </span>
              <span className="text-stone-700">{log.created_at ? new Date(log.created_at).toLocaleString('zh-CN') : '—'}</span>
            </div>
          </section>

          {log.token_usage && log.token_usage.total_tokens > 0 && (
            <section>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-stone-400 mb-2">Token 消耗</h3>
              <div className="grid grid-cols-3 gap-2 text-sm">
                <div className="rounded-lg border border-stone-200 p-2 text-center">
                  <div className="text-xs text-stone-400">Input</div>
                  <div className="font-medium text-stone-800">{log.token_usage.input_tokens.toLocaleString()}</div>
                </div>
                <div className="rounded-lg border border-stone-200 p-2 text-center">
                  <div className="text-xs text-stone-400">Output</div>
                  <div className="font-medium text-stone-800">{log.token_usage.output_tokens.toLocaleString()}</div>
                </div>
                <div className="rounded-lg border border-stone-200 p-2 text-center">
                  <div className="text-xs text-stone-400">Total</div>
                  <div className="font-medium text-stone-800">{log.token_usage.total_tokens.toLocaleString()}</div>
                </div>
              </div>
              {log.latency_ms != null && (
                <div className="mt-2 text-sm text-stone-600">延迟: {log.latency_ms} ms</div>
              )}
            </section>
          )}

          {log.input_summary && (
            <section>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xs font-semibold uppercase tracking-wide text-stone-400">输入摘要</h3>
                <button
                  onClick={() => handleCopy(log.input_summary || '', 'input')}
                  className="inline-flex items-center gap-1 px-2 py-0.5 text-xs text-stone-500 hover:text-stone-800 border border-stone-200 rounded"
                >
                  <Copy size={12} /> {copiedField === 'input' ? '已复制' : '复制'}
                </button>
              </div>
              <pre className="text-sm text-stone-700 bg-stone-50 rounded-lg p-3 whitespace-pre-wrap break-words border border-stone-200">{log.input_summary}</pre>
            </section>
          )}

          {log.output_summary && (
            <section>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xs font-semibold uppercase tracking-wide text-stone-400">输出摘要</h3>
                <button
                  onClick={() => handleCopy(log.output_summary || '', 'output')}
                  className="inline-flex items-center gap-1 px-2 py-0.5 text-xs text-stone-500 hover:text-stone-800 border border-stone-200 rounded"
                >
                  <Copy size={12} /> {copiedField === 'output' ? '已复制' : '复制'}
                </button>
              </div>
              <pre className="text-sm text-stone-700 bg-stone-50 rounded-lg p-3 whitespace-pre-wrap break-words border border-stone-200">{log.output_summary}</pre>
            </section>
          )}

          {log.error_message && (
            <section>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-red-400 mb-2">错误信息</h3>
              <div className="text-sm text-red-700 bg-red-50 rounded-lg p-3 border border-red-200">
                <p><strong>{log.error_type || 'Error'}</strong> {log.error_code ? `(${log.error_code})` : ''}</p>
                <p className="mt-1">{log.error_message}</p>
              </div>
            </section>
          )}

          {log.routing_info && Object.keys(log.routing_info).length > 0 && (
            <section>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-stone-400 mb-2">路由信息</h3>
              <div className="text-sm text-stone-700 bg-stone-50 rounded-lg p-3 border border-stone-200 space-y-1">
                {!!log.routing_info.routing_reason && (
                  <p><span className="text-stone-400">原因: </span>{String(log.routing_info.routing_reason)}</p>
                )}
                {log.routing_info.confidence != null && (
                  <p><span className="text-stone-400">置信度: </span>{Number(log.routing_info.confidence).toFixed(2)}</p>
                )}
                {Array.isArray(log.routing_info.risk_flags) && (log.routing_info.risk_flags as unknown[]).length > 0 && (
                  <p><span className="text-stone-400">风险标志: </span>{(log.routing_info.risk_flags as string[]).join(', ')}</p>
                )}
              </div>
            </section>
          )}

          {log.metadata && Object.keys(log.metadata).length > 0 && (
            <section>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-stone-400 mb-2">元数据</h3>
              <pre className="text-xs text-stone-600 bg-stone-50 rounded-lg p-3 whitespace-pre-wrap break-words border border-stone-200 font-mono">{JSON.stringify(log.metadata, null, 2)}</pre>
            </section>
          )}
        </div>
      </aside>
    </div>
  );
}

function Field({ label, value, link }: { label: string; value?: string | null; link?: string }) {
  if (!value) return null;
  return (
    <div>
      <span className="text-xs text-stone-400">{label}: </span>
      {link ? (
        <Link to={link} className="text-stone-700 font-mono text-xs hover:text-stone-900 underline decoration-dotted inline-flex items-center gap-0.5">
          {value} <ExternalLink size={10} />
        </Link>
      ) : (
        <span className="text-stone-700 font-mono text-xs">{value}</span>
      )}
    </div>
  );
}
