import { useNavigate, useSearchParams } from 'react-router-dom';
import GoalInputPanel from '../components/GoalInputPanel';
import { getTeamPreset } from '../types/team';

export default function CreateRunPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const preset = getTeamPreset(params.get('team'));
  return <div className="mx-auto max-w-2xl px-4 py-10 sm:px-6"><p className="text-xs font-medium uppercase tracking-[0.16em] text-blue-700">New workspace run</p><h1 className="mt-2 text-2xl font-semibold">为 {preset.name} 创建 Goal</h1><p className="mt-1 text-sm text-stone-500">创建后会生成稳定 Run URL，并进入规划工作区。</p><div className="mt-6 overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm"><GoalInputPanel preset={preset} onGoalCreated={(_goalId, runId) => navigate(`/workspace/runs/${runId}`)} /></div></div>;
}
