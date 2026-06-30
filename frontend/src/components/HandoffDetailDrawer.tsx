import { useMemo, useState } from 'react';
import { Copy, X } from 'lucide-react';
import type { HandoffRecord, HandoffResult } from '../types/handoff';
import { HANDOFF_REASON_LABELS } from '../types/handoff';
import HandoffStatusIndicator from './HandoffStatusIndicator';
import HandoffStatusTag from './HandoffStatusTag';

interface HandoffDetailDrawerProps {
  handoff?: HandoffRecord | null;
  isLoading?: boolean;
  error?: Error | null;
  onClose: () => void;
  onAccept?: () => void;
  onSaveResult?: (data: { result_after_handoff: HandoffResult; result_note?: string }) => void;
  isAccepting?: boolean;
  isSavingResult?: boolean;
}

const SUMMARY_FIELDS: Array<{ key: keyof HandoffRecord['handoff_summary']; label: string }> = [
  { key: 'original_goal', label: 'Original Goal' },
  { key: 'current_task', label: 'Current Task' },
  { key: 'completed_work', label: 'Completed Work' },
  { key: 'unfinished_work', label: 'Unfinished Work' },
  { key: 'important_constraints', label: 'Important Constraints' },
  { key: 'key_decisions', label: 'Key Decisions' },
  { key: 'errors_and_risks', label: 'Errors and Risks' },
  { key: 'next_suggested_steps', label: 'Next Suggested Steps' },
  { key: 'context_needed', label: 'Context Needed' },
];

export default function HandoffDetailDrawer({
  handoff,
  isLoading = false,
  error,
  onClose,
  onAccept,
  onSaveResult,
  isAccepting = false,
  isSavingResult = false,
}: HandoffDetailDrawerProps) {
  const [copied, setCopied] = useState(false);
  const [result, setResult] = useState<HandoffResult>('success');
  const [resultNote, setResultNote] = useState('');

  const summaryText = useMemo(() => {
    if (!handoff) return '';
    return SUMMARY_FIELDS.map((field) => {
      const value = handoff.handoff_summary[field.key];
      return `${field.label}\n${Array.isArray(value) ? value.join('\n') : value}`;
    }).join('\n\n');
  }, [handoff]);

  const handleCopy = async () => {
    if (!handoff) return;
    await navigator.clipboard?.writeText(summaryText || handoff.id);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/30" onClick={onClose}>
      <aside
        className="h-full w-full sm:w-[480px] xl:w-[560px] bg-white shadow-xl border-l border-stone-200 flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 z-10 bg-white px-5 py-4 border-b border-stone-200 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h2 className="text-lg font-semibold text-stone-900 truncate">
              Handoff {handoff ? `#${handoff.id.slice(0, 8)}` : ''}
            </h2>
            {handoff && <p className="text-xs text-stone-400 font-mono mt-1">{handoff.id}</p>}
          </div>
          <div className="flex items-center gap-2">
            {handoff && (
              <button onClick={handleCopy} aria-label="复制摘要" className="inline-flex items-center gap-1 px-2 py-1 text-xs text-stone-500 hover:text-stone-800 border border-stone-200 rounded-lg">
                <Copy size={13} /> {copied ? 'Copied' : '复制'}
              </button>
            )}
            <button onClick={onClose} aria-label="close drawer" className="text-stone-400 hover:text-stone-700">
              <X size={20} />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          {isLoading && (
            <div className="space-y-3">
              <div className="h-4 bg-stone-200 rounded animate-pulse" />
              <div className="h-4 bg-stone-200 rounded animate-pulse w-5/6" />
              <div className="h-4 bg-stone-200 rounded animate-pulse w-2/3" />
            </div>
          )}

          {error && (
            <div className="border border-red-200 bg-red-50 text-red-700 rounded-lg px-3 py-2 text-sm">
              {(error as Error).message || '加载交接详情失败'}
            </div>
          )}

          {handoff && (
            <>
              <section className="flex flex-wrap items-center gap-3">
                <HandoffStatusTag status={handoff.status} />
                <HandoffStatusTag status={handoff.result_after_handoff} type="result" />
                <span className="text-xs text-stone-400">{HANDOFF_REASON_LABELS[handoff.reason]}</span>
                <span className="text-xs text-stone-400">{handoff.created_at ? formatRelativeTime(handoff.created_at) : '—'}</span>
              </section>

              {handoff.status === 'generating_summary' && (
                <div className="bg-lavender-50 text-lavender-800 border border-lavender-100 rounded-lg px-3 py-2 text-sm">
                  Generating summary... This may take a few seconds.
                </div>
              )}

              {handoff.status === 'failed' && (
                <div className="bg-red-50 text-red-700 border border-red-100 rounded-lg px-3 py-2 text-sm">
                  Summary generation failed. A fallback summary has been provided.
                </div>
              )}

              <section>
                <h3 className="text-xs font-semibold uppercase tracking-wide text-stone-400 mb-3">Participants</h3>
                <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3">
                  <ParticipantCard label="From" agent={handoff.from_agent_name || handoff.from_agent_id} model={handoff.from_model_id} />
                  <span className="text-stone-300">→</span>
                  <ParticipantCard label="To" agent={handoff.to_agent_name || handoff.to_agent_id} model={handoff.to_model_id} highlight />
                </div>
              </section>

              <section>
                <h3 className="text-xs font-semibold uppercase tracking-wide text-stone-400 mb-3">Timeline</h3>
                <HandoffStatusIndicator status={handoff.status} />
                <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-stone-500">
                  <TimeLineItem label="Created" value={handoff.created_at} />
                  <TimeLineItem label="Summary" value={handoff.summary_generated_at} />
                  <TimeLineItem label="Accepted" value={handoff.accepted_at} />
                  <TimeLineItem label="Completed" value={handoff.completed_at} />
                </div>
              </section>

              <section>
                <h3 className="text-xs font-semibold uppercase tracking-wide text-stone-400 mb-3">Handoff Summary</h3>
                <div className="space-y-3">
                  {SUMMARY_FIELDS.map((field) => (
                    <SummarySection key={field.key} title={field.label} value={handoff.handoff_summary[field.key]} />
                  ))}
                </div>
              </section>

              <section>
                <h3 className="text-xs font-semibold uppercase tracking-wide text-stone-400 mb-3">Result</h3>
                {handoff.result_after_handoff ? (
                  <div className="rounded-lg border border-stone-200 p-3">
                    <HandoffStatusTag status={handoff.result_after_handoff} type="result" />
                    {handoff.result_note && <p className="text-sm text-stone-600 mt-2">{handoff.result_note}</p>}
                  </div>
                ) : handoff.status === 'accepted' ? (
                  <div className="rounded-lg border border-stone-200 p-3 space-y-3">
                    <select value={result} onChange={(e) => setResult(e.target.value as HandoffResult)} className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg">
                      <option value="success">成功</option>
                      <option value="partial">部分完成</option>
                      <option value="failed">失败</option>
                    </select>
                    <textarea value={resultNote} onChange={(e) => setResultNote(e.target.value)} rows={3} className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg resize-none" placeholder="结果备注" />
                    <button
                      onClick={() => onSaveResult?.({ result_after_handoff: result, result_note: resultNote || undefined })}
                      disabled={isSavingResult}
                      className="px-3 py-2 text-sm bg-stone-800 text-white rounded-lg disabled:opacity-50"
                    >
                      {isSavingResult ? '保存中...' : '保存结果'}
                    </button>
                  </div>
                ) : (
                  <div className="text-sm text-stone-400 rounded-lg border border-dashed border-stone-200 p-3">尚未记录结果</div>
                )}
              </section>
            </>
          )}
        </div>

        {handoff?.status === 'ready' && (
          <div className="sticky bottom-0 bg-white border-t border-stone-200 p-4 flex justify-end">
            <button
              onClick={onAccept}
              disabled={isAccepting}
              className="px-4 py-2 text-sm font-medium bg-stone-800 text-white rounded-lg hover:bg-stone-900 disabled:opacity-50"
            >
              {isAccepting ? '接受中...' : 'Accept Handoff'}
            </button>
          </div>
        )}
      </aside>
    </div>
  );
}

function ParticipantCard({ label, agent, model, highlight = false }: { label: string; agent: string; model: string; highlight?: boolean }) {
  return (
    <div className={`rounded-lg border p-3 ${highlight ? 'border-lavender-300 bg-lavender-50' : 'border-stone-200 bg-white'}`}>
      <div className="text-[10px] uppercase tracking-wide text-stone-400 mb-1">{label}</div>
      <div className="text-sm font-medium text-stone-800 truncate">{agent}</div>
      <div className="text-xs text-stone-400 truncate font-mono mt-1">{model}</div>
    </div>
  );
}

function SummarySection({ title, value }: { title: string; value: string | string[] }) {
  const isArray = Array.isArray(value);
  const empty = isArray ? value.length === 0 : !value || value === '—';
  return (
    <div className="rounded-lg border border-stone-200 bg-white p-4">
      <div className="text-xs font-semibold text-stone-500 mb-2">{title}</div>
      {empty ? (
        <div className="text-sm text-stone-300">—</div>
      ) : isArray ? (
        <ul className="space-y-1 text-sm text-stone-700 leading-relaxed">
          {value.map((item, idx) => <li key={idx}>• {item}</li>)}
        </ul>
      ) : (
        <p className="text-sm text-stone-700 leading-relaxed whitespace-pre-wrap">{value}</p>
      )}
    </div>
  );
}

function TimeLineItem({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="flex justify-between gap-2 rounded-lg bg-stone-50 px-2 py-1.5">
      <span>{label}</span>
      <span className="font-mono text-stone-400">{value ? formatRelativeTime(value) : '—'}</span>
    </div>
  );
}

function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const diffMs = new Date().getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60000);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);
  if (diffMin < 1) return '刚刚';
  if (diffMin < 60) return `${diffMin} 分钟前`;
  if (diffHour < 24) return `${diffHour} 小时前`;
  if (diffDay < 7) return `${diffDay} 天前`;
  return date.toLocaleDateString('zh-CN');
}
