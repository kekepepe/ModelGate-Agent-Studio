import { ArrowUpRight, GitBranch, Pause, X } from 'lucide-react';
import type { StationViewModel } from '../utils/workspaceViewModel';

export default function StationPopover({ station, onClose, onOpenDetail, onHandoff, onPause }: { station: StationViewModel; onClose: () => void; onOpenDetail: (taskId: string) => void; onHandoff: (taskId: string) => void; onPause?: () => void }) {
  const task = station.activeTask;
  const canHandoff = Boolean(task && ['assigned', 'running', 'failed', 'handoff'].includes(task.status));
  return (
    <div role="dialog" aria-label={`${station.agent.name}工位详情`} className="station-popover">
      <button type="button" onClick={onClose} aria-label="关闭工位详情" className="station-popover-close"><X size={13} /></button>
      <header><span className="agent-status-dot agent-status-dot--blue" /><div><strong>{station.agent.name} ({station.status})</strong><small>Model: {station.worker?.model_name || station.agent.default_model_id || 'Unassigned'}</small></div></header>
      <div className="station-popover-actions">
        <button type="button" disabled={!task} onClick={() => task && onOpenDetail(task.id)}>View Full Detail <ArrowUpRight size={13} /></button>
        <button type="button" disabled={!onPause} onClick={onPause}>Pause <Pause size={13} fill="currentColor" /></button>
        <button type="button" disabled={!canHandoff} onClick={() => canHandoff && task && onHandoff(task.id)}>Handoff <GitBranch size={14} /></button>
      </div>
      <i aria-hidden="true" />
    </div>
  );
}
