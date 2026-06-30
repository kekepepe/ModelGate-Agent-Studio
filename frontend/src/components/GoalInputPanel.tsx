import { useState } from 'react';
import { useCreateGoal, useStartGoal } from '../hooks/useWorkspace';

interface GoalInputPanelProps {
  onGoalCreated: (goalId: string) => void;
  activeGoalId?: string | null;
  goalTitle?: string | null;
}

export default function GoalInputPanel({ onGoalCreated, activeGoalId, goalTitle }: GoalInputPanelProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);
  const createGoal = useCreateGoal();
  const startGoal = useStartGoal();

  const isSubmitting = createGoal.isPending || startGoal.isPending;
  const isValid = title.trim().length > 0;

  const handleStart = async () => {
    if (!isValid) return;
    setError(null);
    try {
      const result = await createGoal.mutateAsync({ title: title.trim(), description: description.trim() || undefined });
      const startResult = await startGoal.mutateAsync(result.goal_id);
      onGoalCreated(startResult.goal_id);
    } catch {
      setError('创建失败，请重试');
    }
  };

  if (activeGoalId) {
    return (
      <div className="p-4 border-b border-stone-200">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-stone-400 mb-2">当前 Goal</h3>
        <p className="text-sm font-medium text-stone-800 mb-1 truncate">{goalTitle || 'Untitled'}</p>
        <p className="text-xs text-stone-400 font-mono truncate">{activeGoalId}</p>
      </div>
    );
  }

  return (
    <div className="p-4 border-b border-stone-200">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-stone-400 mb-3">新任务</h3>
      <textarea
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        placeholder="描述你的目标..."
        rows={4}
        className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg resize-none focus:outline-none focus:ring-1 focus:ring-stone-400 mb-2"
        disabled={isSubmitting}
      />
      <input
        type="text"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        placeholder="补充说明（可选）"
        className="w-full px-3 py-1.5 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-stone-400 mb-3"
        disabled={isSubmitting}
      />
      <button
        onClick={handleStart}
        disabled={!isValid || isSubmitting}
        className="w-full py-2 text-sm font-medium bg-stone-800 text-white rounded-lg hover:bg-stone-900 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        {isSubmitting ? '创建中...' : '开始'}
      </button>
      {error && <p className="text-xs text-red-600 mt-2">{error}</p>}
    </div>
  );
}
