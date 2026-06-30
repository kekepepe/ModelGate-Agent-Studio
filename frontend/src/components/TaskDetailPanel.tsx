import { useState } from 'react';
import { Copy, X } from 'lucide-react';
import type { WorkspaceTask } from '../types/workspace';
import { TASK_STATUS_LABELS } from '../types/workspace';

interface TaskDetailPanelProps {
  task?: WorkspaceTask | null;
  isLoading?: boolean;
  onClose: () => void;
}

type TabKey = 'overview' | 'task' | 'context' | 'logs';

export default function TaskDetailPanel({ task, isLoading, onClose }: TaskDetailPanelProps) {
  const [activeTab, setActiveTab] = useState<TabKey>('overview');
  const [copied, setCopied] = useState(false);

  if (!task) return null;

  const handleCopy = async () => {
    if (!task.output) return;
    await navigator.clipboard?.writeText(task.output);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  const tabs: { key: TabKey; label: string }[] = [
    { key: 'overview', label: 'Overview' },
    { key: 'task', label: 'Task' },
    { key: 'context', label: 'Context' },
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
          </div>
        )}

        {activeTab === 'context' && (
          <p className="text-sm text-stone-400">上下文信息待实现</p>
        )}

        {activeTab === 'logs' && (
          <p className="text-sm text-stone-400">该 Task 相关日志的缩略列表（点击跳转完整日志）</p>
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
