import { useState } from 'react';
import { Copy, X, Wrench } from 'lucide-react';
import type { WorkspaceHandoff, WorkspaceTask } from '../types/workspace';
import { TASK_STATUS_LABELS } from '../types/workspace';
import { useToolCalls } from '../hooks/useTools';

interface TaskDetailPanelProps {
  task?: WorkspaceTask | null;
  isLoading?: boolean;
  onClose: () => void;
  handoffs?: WorkspaceHandoff[];
  onOpenHandoff?: (handoffId: string) => void;
}

type TabKey = 'overview' | 'task' | 'router' | 'context' | 'handoff' | 'logs';

export default function TaskDetailPanel({ task, isLoading, onClose, handoffs = [], onOpenHandoff }: TaskDetailPanelProps) {
  const [activeTab, setActiveTab] = useState<TabKey>('overview');
  const [copied, setCopied] = useState(false);
  const { data: toolCallsData } = useToolCalls(
    task ? { task_id: task.id } : {}
  );

  if (!task) return null;

  const toolCalls = toolCallsData?.items || [];

  const handleCopy = async () => {
    if (!task.output) return;
    await navigator.clipboard?.writeText(task.output);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  const tabs: { key: TabKey; label: string }[] = [
    { key: 'overview', label: 'Overview' },
    { key: 'task', label: 'Task' },
    { key: 'router', label: 'Router' },
    { key: 'context', label: 'Context' },
    { key: 'handoff', label: 'Handoff' },
    { key: 'logs', label: 'Logs' },
  ];

  return (
    <aside className="h-full bg-white border-l border-stone-200 flex flex-col">
      <div className="px-4 py-3 border-b border-stone-200 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-stone-800 truncate">{task.title}</h2>
        <button onClick={onClose} className="text-stone-400 hover:text-stone-700">
          <X size={18} />
        </button>
      </div>

      <div className="flex border-b border-stone-200">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 py-2 text-xs font-medium transition-colors ${
              activeTab === tab.key
                ? 'text-stone-800 border-b-2 border-stone-800'
                : 'text-stone-400 hover:text-stone-600'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {isLoading && (
          <div className="space-y-2">
            <div className="h-4 bg-stone-200 rounded animate-pulse" />
            <div className="h-4 bg-stone-200 rounded animate-pulse w-3/4" />
          </div>
        )}

        {activeTab === 'overview' && (
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-stone-400">状态</span>
              <span className="text-stone-700 font-medium">{TASK_STATUS_LABELS[task.status] || task.status}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-stone-400">优先级</span>
              <span className="text-stone-700">{task.priority}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-stone-400">分配 Agent</span>
              <span className="text-stone-700">{task.agent_name || task.assigned_agent_id || '—'}</span>
            </div>
            {task.agent_role && (
              <div className="flex justify-between">
                <span className="text-stone-400">Agent 角色</span>
                <span className="text-stone-700">{task.agent_role}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-stone-400">Worker 模型</span>
              <span className="text-stone-700 font-mono text-xs">{task.model_name || '—'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-stone-400">Token 消耗</span>
              <span className="text-stone-700">{task.tokens_used.toLocaleString()}</span>
            </div>
            {task.quota && (
              <div className="flex justify-between">
                <span className="text-stone-400">额度状态</span>
                <span className={task.quota.quota_status === 'limited' || task.quota.quota_status === 'cooldown' ? 'text-red-700 font-medium' : 'text-stone-700'}>
                  {quotaLabel(task.quota.quota_status)}{task.quota.usage_percent != null ? ` · ${Math.round(task.quota.usage_percent * 100)}%` : ''}
                </span>
              </div>
            )}
            {task.duration_ms != null && (
              <div className="flex justify-between">
                <span className="text-stone-400">耗时</span>
                <span className="text-stone-700">{formatDuration(task.duration_ms)}</span>
              </div>
            )}
          </div>
        )}

        {activeTab === 'task' && (
          <div className="space-y-3">
            {task.description && (
              <div>
                <h4 className="text-xs font-semibold text-stone-400 mb-1 uppercase">描述</h4>
                <p className="text-sm text-stone-700">{task.description}</p>
              </div>
            )}
            {task.output ? (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <h4 className="text-xs font-semibold text-stone-400 uppercase">输出</h4>
                  <button
                    onClick={handleCopy}
                    className="inline-flex items-center gap-1 px-2 py-0.5 text-xs text-stone-500 hover:text-stone-800 border border-stone-200 rounded"
                  >
                    <Copy size={12} /> {copied ? '已复制' : '复制'}
                  </button>
                </div>
                <pre className="text-sm text-stone-700 bg-stone-50 rounded-lg p-3 whitespace-pre-wrap break-words border border-stone-200 max-h-96 overflow-y-auto">{task.output}</pre>
              </div>
            ) : (
              <p className="text-sm text-stone-400">尚未产出输出</p>
            )}

            {/* Tool Call Records */}
            {toolCalls.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-stone-400 mb-2 uppercase flex items-center gap-1">
                  <Wrench size={12} /> 工具调用记录 ({toolCalls.length})
                </h4>
                <div className="space-y-2">
                  {toolCalls.map((tc) => (
                    <div key={tc.id} className="bg-stone-50 border border-stone-200 rounded-lg p-2 text-sm">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-mono text-xs text-stone-700">{tc.tool_name}</span>
                        <span className={`text-xs ${tc.status === 'completed' ? 'text-green-600' : 'text-red-600'}`}>
                          {tc.status === 'completed' ? '✅' : '❌'} {tc.latency_ms}ms
                        </span>
                      </div>
                      <p className="text-xs text-stone-500 truncate">
                        输入: {JSON.stringify(tc.tool_input).substring(0, 80)}
                      </p>
                      {tc.tool_output && (
                        <p className="text-xs text-stone-600 mt-1 line-clamp-2">
                          {tc.tool_output.substring(0, 200)}
                        </p>
                      )}
                      {tc.error_message && (
                        <p className="text-xs text-red-600 mt-1">{tc.error_message}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'context' && (
          task.context ? (
            <div>
              <p className="mb-2 text-xs text-stone-400">当前 Worker 接收到的上下文（包含交接摘要时会在此呈现）。</p>
              <pre className="max-h-96 overflow-y-auto whitespace-pre-wrap break-words rounded-lg border border-stone-200 bg-stone-50 p-3 text-xs leading-relaxed text-stone-700">{formatContext(task.context)}</pre>
            </div>
          ) : (
            <p className="text-sm text-stone-400">当前 Task 尚未建立可继承上下文。</p>
          )
        )}

        {activeTab === 'router' && (
          task.routing_decision ? (
            <div className="space-y-4">
              <section>
                <h4 className="text-xs font-semibold uppercase text-stone-400">选择理由</h4>
                <p className="mt-1 text-sm leading-relaxed text-stone-700">{task.routing_decision.routing_reason?.summary || '已记录模型路由决策。'}</p>
                <p className="mt-1 text-xs text-stone-400">置信度 {Math.round((task.routing_decision.confidence || 0) * 100)}%</p>
              </section>
              <ListSection title="主要因素" items={task.routing_decision.routing_reason?.primary_factors || []} />
              <ListSection title="取舍" items={task.routing_decision.routing_reason?.tradeoffs || []} emptyText="未记录明显取舍。" />
              <ListSection title="备用模型" items={task.routing_decision.backup_model_ids || []} emptyText="暂无备用模型。" mono />
              {(task.routing_decision.risk_flags || []).length > 0 && (
                <section>
                  <h4 className="text-xs font-semibold uppercase text-stone-400">风险提示</h4>
                  <div className="mt-2 space-y-2">
                    {task.routing_decision.risk_flags?.map((risk, index) => (
                      <div key={`${risk.type}-${index}`} className="rounded-lg border border-amber-200 bg-amber-50 p-2 text-xs text-amber-800">
                        {risk.message}{risk.suggestion ? ` · ${risk.suggestion}` : ''}
                      </div>
                    ))}
                  </div>
                </section>
              )}
            </div>
          ) : (
            <p className="text-sm text-stone-400">尚未执行模型路由；运行 Task 后会在此显示选择依据。</p>
          )
        )}

        {activeTab === 'handoff' && (
          handoffs.length > 0 ? (
            <div className="space-y-3">
              <p className="text-xs text-stone-400">交接按发生顺序保留在当前任务中。</p>
              {handoffs.map((handoff) => (
                <button
                  key={handoff.id}
                  type="button"
                  onClick={() => onOpenHandoff?.(handoff.id)}
                  className="w-full text-left rounded-lg border border-stone-200 bg-stone-50 p-3 hover:border-stone-400"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-medium text-stone-700 truncate">
                      {handoff.from_agent_name || '原 Agent'} → {handoff.to_agent_name || '接手 Agent'}
                    </span>
                    <span className="text-[11px] text-purple-700">{handoff.status}</span>
                  </div>
                  <p className="mt-1 text-xs text-stone-500">{handoff.reason_description || handoff.reason}</p>
                </button>
              ))}
            </div>
          ) : (
            <p className="text-sm text-stone-400">当前 Task 尚无交接记录。</p>
          )
        )}

        {activeTab === 'logs' && (
          task.recent_logs && task.recent_logs.length > 0 ? (
            <div className="space-y-2">
              <p className="text-xs text-stone-400">展示当前 Task 最近 10 条运行事件。</p>
              {task.recent_logs.map((log) => (
                <div key={log.id} className="rounded-lg border border-stone-200 bg-stone-50 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-medium text-stone-700">{log.event_type} · {log.event_status}</span>
                    <span className="text-[10px] text-stone-400">{formatTimestamp(log.created_at)}</span>
                  </div>
                  <p className="mt-1 text-xs leading-relaxed text-stone-500">{log.error_message || log.output_summary || log.input_summary || '无附加摘要'}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-stone-400">当前 Task 尚无运行日志。</p>
          )
        )}
      </div>
    </aside>
  );
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${Math.floor(ms / 1000)}s`;
  const min = Math.floor(ms / 60000);
  const sec = Math.floor((ms % 60000) / 1000);
  return `${min}m ${sec}s`;
}

function quotaLabel(status: string): string {
  return ({ normal: '正常', warning: '注意', near_limit: '接近上限', limited: '已受限', cooldown: '冷却中', unknown: '未知' } as Record<string, string>)[status] || status;
}

function formatContext(context: string): string {
  try {
    return JSON.stringify(JSON.parse(context), null, 2);
  } catch {
    return context;
  }
}

function formatTimestamp(value?: string | null): string {
  if (!value) return '—';
  return new Date(value).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function ListSection({ title, items, emptyText = '—', mono = false }: { title: string; items: string[]; emptyText?: string; mono?: boolean }) {
  return (
    <section>
      <h4 className="text-xs font-semibold uppercase text-stone-400">{title}</h4>
      {items.length > 0 ? (
        <ul className={`mt-2 space-y-1 text-sm text-stone-700 ${mono ? 'font-mono text-xs' : ''}`}>
          {items.map((item, index) => <li key={`${item}-${index}`}>• {item}</li>)}
        </ul>
      ) : <p className="mt-1 text-sm text-stone-400">{emptyText}</p>}
    </section>
  );
}
