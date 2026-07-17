import { ArrowRight, Check, Code2, FileCheck2, Folder, Info, LoaderCircle } from 'lucide-react';
import { useState } from 'react';
import officeTeamImage from '../assets/pixel-office/office-team.png';
import type { WorkspaceViewModel } from '../utils/workspaceViewModel';
import StationPopover from './StationPopover';

interface PixelOfficeRendererProps {
  viewModel: WorkspaceViewModel;
  onSelectTask: (taskId: string) => void;
  onRequestHandoff: (taskId: string) => void;
  onOpenHandoff: (handoffId: string) => void;
  onPause?: () => void;
}

const STATUS_COLOR: Record<string, string> = { running: 'blue', done: 'green', completed: 'green', waiting: 'amber', handoff: 'purple', error: 'red', idle: 'gray' };
const STATION_POSITIONS: Record<number, number[]> = { 1: [50], 2: [30, 70], 3: [17, 50, 83], 4: [12, 37, 63, 88] };

export default function PixelOfficeRenderer({ viewModel, onSelectTask, onRequestHandoff, onOpenHandoff, onPause }: PixelOfficeRendererProps) {
  const [selectedStationId, setSelectedStationId] = useState<string | null>(null);
  const stations = viewModel.stations.slice(0, 4);
  const isEmpty = stations.length === 0;
  const positions = STATION_POSITIONS[stations.length] || STATION_POSITIONS[3];
  const latestHandoff = viewModel.handoffs.at(-1);

  return (
    <section aria-label="Pixel Office" className="pixel-office-canvas">
      <header className="workspace-canvas-heading"><h2>Pixel office <Info size={13} /></h2></header>
      {isEmpty ? (
        <div className="pixel-office-empty-state" role="status" aria-live="polite">
          <span className="pixel-office-empty-icon" aria-hidden="true"><Info size={16} /></span>
          <span className="pixel-office-empty-copy">
            <strong>办公室等待任务</strong>
            <span>创建 Goal 后，Agent 会进入对应工位。</span>
          </span>
        </div>
      ) : null}
      <div className="pixel-office-room" style={{ backgroundImage: `url(${officeTeamImage})` }}>
        {isEmpty ? null : <>
          {stations.map((station, index) => {
            const active = station.agent.id === selectedStationId;
            const color = STATUS_COLOR[station.status] || 'gray';
            return <div key={station.agent.id} className={`pixel-station pixel-station--${color}`} style={{ left: `${positions[index]}%` }}>
              {active ? <StationPopover station={station} onClose={() => setSelectedStationId(null)} onOpenDetail={onSelectTask} onHandoff={onRequestHandoff} onPause={onPause} /> : null}
              <button type="button" className="pixel-station-target" onClick={() => setSelectedStationId(active ? null : station.agent.id)} aria-label={`打开 ${station.agent.name} 工位`}>
                <span className={`pixel-status-lamp pixel-status-lamp--${color}`} />
                <span className="pixel-agent-plaque"><strong>{station.agent.name}</strong><small>{shortModel(station.worker?.model_name || station.activeTask?.model_name || station.agent.default_model_id || 'No model')}</small></span>
                <span className="pixel-task-card"><small>Current task</small><span>{station.activeTask?.title || 'Awaiting task'}</span><TaskIndicator status={station.activeTask?.status || station.status} /></span>
                <span className="pixel-output-card"><small>Output</small><span className="pixel-output-icon">{station.agent.role === 'coder' ? <Code2 size={23} /> : station.agent.role === 'reviewer' ? <FileCheck2 size={23} /> : <Folder size={23} fill="currentColor" />}</span></span>
              </button>
            </div>;
          })}
          {stations.slice(0, -1).map((station, index) => <div key={`${station.agent.id}-arrow`} className={`pixel-flow-arrow pixel-flow-arrow--${STATUS_COLOR[stations[index + 1]?.status] || 'gray'}`} style={{ left: `${(positions[index] + positions[index + 1]) / 2}%` }}><ArrowRight size={34} strokeWidth={3.5} /></div>)}
        </>}

        <div className={`pixel-handoff-route ${latestHandoff ? 'is-active' : ''}`} aria-hidden="true"><span className="pixel-handoff-left" /><span className="pixel-handoff-line" /><span className="pixel-handoff-right" /></div>
        <button type="button" disabled={!latestHandoff} onClick={() => latestHandoff && onOpenHandoff(latestHandoff.id)} className="pixel-handoff-card">
          <Folder size={27} fill="currentColor" /><span><small>Handoff folder</small><strong>{latestHandoff?.reason_description || latestHandoff?.reason || 'No active handoff'}</strong><em>From: {latestHandoff?.from_agent_name || '—'} <ArrowRight size={10} /> To: {latestHandoff?.to_agent_name || '—'}</em></span>
        </button>
      </div>
    </section>
  );
}

function TaskIndicator({ status }: { status: string }) {
  if (['done', 'completed', 'completed_verified', 'completed_unverified'].includes(status)) return <Check size={15} className="pixel-task-state pixel-task-state--done" />;
  if (status === 'running') return <LoaderCircle size={15} className="pixel-task-state pixel-task-state--running" />;
  return <span className="pixel-task-state pixel-task-state--waiting">⌛</span>;
}

function shortModel(value: string) { if (/^[0-9a-f]{8}-[0-9a-f-]{27,}$/i.test(value)) return 'Configured Model'; return value.split(/[/:]/).at(-1) || value; }
