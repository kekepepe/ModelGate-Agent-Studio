import { ArrowUpRight, GitBranch, Pause, X } from 'lucide-react';
import type { StationViewModel } from '../utils/workspaceViewModel';

export default function StationPopover({ station, onClose, onOpenDetail, onHandoff, onPause }: {
  station: StationViewModel;
  onClose: () => void;
  onOpenDetail: (taskId: string) => void;
  onHandoff: (taskId: string) => void;
  onPause?: () => void;
}) {
  const task = station.activeTask;
  const canHandoff = Boolean(task && ['assigned', 'running', 'failed', 'handoff'].includes(task.status));
  return (
    <div role="dialog" aria-label={`${station.agent.name}工位详情`} className="absolute left-1/2 top-0 z-30 w-64 -translate-x-1/2 -translate-y-[108%] rounded-xl border border-stone-200 bg-white p-3 text-left shadow-xl">
      <button type="button" onClick={onClose} aria-label="关闭工位详情" className="absolute right-2 top-2 rounded p-1 text-stone-400 hover:bg-stone-100"><X size={13} /></button>
      <div className="pr-6">
        <p className="text-sm font-semibold text-stone-900">{station.agent.name}</p>
        <p className="mt-0.5 text-[11px] text-stone-500">{station.worker?.model_name || station.agent.default_model_id || '未绑定模型'} · {station.status}</p>
      </div>
      <div className="mt-3 rounded-lg bg-stone-50 px-3 py-2">
        <p className="text-[10px] font-semibold uppercase tracking-wide text-stone-400">Current task</p>
        <p className="mt-1 truncate text-xs font-medium text-stone-700">{task?.title || '暂无任务'}</p>
        <p className="mt-1 line-clamp-2 text-[11px] leading-4 text-stone-500">{task?.output || station.worker?.next_action || (task?.status === 'pending' ? '已规划，等待上游完成或运行开始。' : '等待任务分配。')}</p>
      </div>
      <div className="mt-3 grid gap-1">
        <button type="button" disabled={!task} onClick={() => task && onOpenDetail(task.id)} className="flex items-center justify-between rounded-md px-2 py-1.5 text-xs font-medium text-stone-700 hover:bg-stone-50 disabled:opacity-40">View Full Detail <ArrowUpRight size={13} /></button>
        <button type="button" disabled={!onPause} onClick={onPause} className="flex items-center justify-between rounded-md px-2 py-1.5 text-xs font-medium text-stone-600 hover:bg-stone-50 disabled:cursor-not-allowed disabled:opacity-40"><span className="flex items-center gap-2"><Pause size={13} /> Pause run</span></button>
        <button type="button" disabled={!canHandoff} onClick={() => canHandoff && task && onHandoff(task.id)} className="flex items-center justify-between rounded-md px-2 py-1.5 text-xs font-medium text-purple-700 hover:bg-purple-50 disabled:cursor-not-allowed disabled:opacity-40"><span className="flex items-center gap-2"><GitBranch size={13} /> Handoff</span></button>
      </div>
      <span aria-hidden="true" className="absolute -bottom-2 left-1/2 h-4 w-4 -translate-x-1/2 rotate-45 border-b border-r border-stone-200 bg-white" />
    </div>
  );
}
