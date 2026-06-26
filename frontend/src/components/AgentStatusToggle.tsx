import { useState } from 'react';
import { useUpdateAgentStatus } from '../hooks/useAgents';

interface AgentStatusToggleProps {
  agentId: string;
  isEnabled: boolean;
  hasRunningTask?: boolean;
}

export default function AgentStatusToggle({ agentId, isEnabled, hasRunningTask }: AgentStatusToggleProps) {
  const [showConfirm, setShowConfirm] = useState(false);
  const [pendingValue, setPendingValue] = useState(isEnabled);
  const updateStatus = useUpdateAgentStatus();

  const handleToggle = () => {
    const newValue = !isEnabled;
    if (!newValue && hasRunningTask) {
      setPendingValue(newValue);
      setShowConfirm(true);
      return;
    }
    updateStatus.mutate(
      { agentId, isEnabled: newValue },
      {
        onError: () => {
          // Mutation error handled by parent refetch; no local state to revert
        },
      }
    );
  };

  const handleConfirm = () => {
    updateStatus.mutate(
      { agentId, isEnabled: pendingValue },
      {
        onSuccess: () => setShowConfirm(false),
        onError: () => setShowConfirm(false),
      }
    );
  };

  const handleCancel = () => {
    setShowConfirm(false);
  };

  return (
    <>
      <button
        onClick={handleToggle}
        disabled={updateStatus.isPending}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 focus:outline-none ${
          isEnabled ? 'bg-green-700' : 'bg-stone-300'
        }`}
        aria-label={isEnabled ? '禁用 Agent' : '启用 Agent'}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200 ${
            isEnabled ? 'translate-x-6' : 'translate-x-1'
          }`}
        />
      </button>

      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div className="bg-white rounded-xl shadow-lg p-6 max-w-sm w-full mx-4">
            <h3 className="text-base font-semibold text-stone-800 mb-2">该 Agent 有进行中任务</h3>
            <p className="text-sm text-stone-500 mb-6">
              禁用后该 Agent 不再接收新任务，但当前任务会继续执行。
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={handleCancel}
                className="px-4 py-2 text-sm text-stone-600 hover:text-stone-800"
              >
                取消
              </button>
              <button
                onClick={handleConfirm}
                className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                强制禁用
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
