import { useMemo, useState } from 'react';
import type { AgentListItem } from '../types/agent';
import type { HandoffReason } from '../types/handoff';
import { HANDOFF_REASON_LABELS } from '../types/handoff';

interface HandoffConfirmModalProps {
  taskId: string;
  agents: AgentListItem[];
  fromAgentId?: string;
  onConfirm: (data: { to_agent_id: string; reason: HandoffReason; reason_description?: string }) => void;
  onCancel: () => void;
  isSubmitting?: boolean;
  error?: string | null;
}

const REASONS = ['quota_exceeded', 'error', 'quality_issue', 'role_mismatch', 'manual', 'context_limit', 'other'] as HandoffReason[];

export default function HandoffConfirmModal({
  taskId,
  agents,
  fromAgentId,
  onConfirm,
  onCancel,
  isSubmitting = false,
  error,
}: HandoffConfirmModalProps) {
  const candidates = useMemo(
    () => agents.filter((agent) => agent.id !== fromAgentId && agent.is_enabled !== false),
    [agents, fromAgentId]
  );
  const [toAgentId, setToAgentId] = useState(candidates[0]?.id || '');
  const [reason, setReason] = useState<HandoffReason>('manual');
  const [description, setDescription] = useState('');

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!toAgentId) return;
    onConfirm({
      to_agent_id: toAgentId,
      reason,
      reason_description: description.trim() || undefined,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
      <form onSubmit={submit} className="w-full max-w-lg rounded-xl bg-white shadow-lg border border-stone-200">
        <div className="px-5 py-4 border-b border-stone-200">
          <h2 className="text-base font-semibold text-stone-900">Generate Handoff</h2>
          <p className="text-xs text-stone-400 mt-1 font-mono">Task {taskId}</p>
        </div>

        <div className="p-5 space-y-4">
          {error && (
            <div className="border border-red-200 bg-red-50 text-red-700 text-sm rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <label className="block">
            <span className="text-xs font-medium text-stone-500">接手 Agent</span>
            <select
              value={toAgentId}
              onChange={(e) => setToAgentId(e.target.value)}
              required
              className="mt-1 w-full px-3 py-2 text-sm border border-stone-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-stone-300"
            >
              {candidates.length === 0 && <option value="">无可用 Agent</option>}
              {candidates.map((agent) => (
                <option key={agent.id} value={agent.id}>
                  {agent.name} · {agent.role}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="text-xs font-medium text-stone-500">交接原因</span>
            <select
              value={reason}
              onChange={(e) => setReason(e.target.value as HandoffReason)}
              className="mt-1 w-full px-3 py-2 text-sm border border-stone-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-stone-300"
            >
              {REASONS.map((r) => (
                <option key={r} value={r}>{HANDOFF_REASON_LABELS[r]}</option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="text-xs font-medium text-stone-500">原因描述</span>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              placeholder="补充当前上下文、失败原因或接手要求..."
              className="mt-1 w-full px-3 py-2 text-sm border border-stone-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-stone-300"
            />
          </label>
        </div>

        <div className="px-5 py-4 border-t border-stone-200 flex justify-end gap-2">
          <button type="button" onClick={onCancel} className="px-3 py-2 text-sm text-stone-600 hover:text-stone-800">
            取消
          </button>
          <button
            type="submit"
            disabled={isSubmitting || !toAgentId}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-stone-800 text-white hover:bg-stone-900 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? '生成中...' : '确认交接'}
          </button>
        </div>
      </form>
    </div>
  );
}
