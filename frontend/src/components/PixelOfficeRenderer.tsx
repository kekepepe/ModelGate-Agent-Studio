import { BriefcaseBusiness, CheckCircle2, Clock3, PlayCircle } from 'lucide-react';
import { useState } from 'react';
import type { WorkspaceViewModel } from '../utils/workspaceViewModel';
import StationPopover from './StationPopover';

interface PixelOfficeRendererProps {
  viewModel: WorkspaceViewModel;
  onSelectTask: (taskId: string) => void;
  onRequestHandoff: (taskId: string) => void;
  onOpenHandoff: (handoffId: string) => void;
  onPause?: () => void;
}

const STATUS_LIGHTS: Record<string, string> = {
  running: 'bg-blue-500 shadow-[0_0_0_4px_rgba(59,130,246,0.13)]',
  done: 'bg-emerald-500',
  completed: 'bg-emerald-500',
  waiting: 'bg-amber-500',
  handoff: 'bg-purple-500 shadow-[0_0_0_4px_rgba(168,85,247,0.13)]',
  error: 'bg-red-500',
  idle: 'bg-stone-300',
};

export default function PixelOfficeRenderer({ viewModel, onSelectTask, onRequestHandoff, onOpenHandoff, onPause }: PixelOfficeRendererProps) {
  const [selectedStationId, setSelectedStationId] = useState<string | null>(null);
  const selectedStation = viewModel.stations.find((station) => station.agent.id === selectedStationId);
  const latestHandoff = viewModel.handoffs.at(-1);

  return (
    <section aria-label="Pixel Office" className="relative min-h-[620px] overflow-hidden rounded-xl border border-slate-300 bg-slate-100 shadow-sm">
      <div className="flex h-12 items-center justify-between border-b border-slate-300 bg-white/90 px-4">
        <div>
          <h2 className="text-sm font-semibold text-slate-900">Pixel Office</h2>
          <p className="text-[10px] text-slate-500">同一份 Workspace State 的空间化观察模式</p>
        </div>
        <div className="flex items-center gap-3 text-[10px] text-slate-500">
          <span className="flex items-center gap-1"><PlayCircle size={12} className="text-blue-600" /> Working</span>
          <span className="flex items-center gap-1"><Clock3 size={12} className="text-amber-600" /> Waiting</span>
          <span className="flex items-center gap-1"><CheckCircle2 size={12} className="text-emerald-600" /> Done</span>
        </div>
      </div>

      <div className="pixel-office-room relative min-h-[568px] px-6 pb-28 pt-20">
        <div aria-hidden="true" className="absolute left-8 top-7 h-20 w-28 border-4 border-slate-400 bg-blue-50 shadow-inner">
          <div className="grid h-full grid-cols-4 gap-1 p-2">{Array.from({ length: 12 }).map((_, index) => <span key={index} className="bg-white/70" />)}</div>
        </div>
        <div aria-hidden="true" className="absolute right-8 top-7 flex h-20 w-32 items-end gap-1 border-4 border-amber-900/50 bg-amber-50 p-2">
          {['h-8 bg-blue-400', 'h-12 bg-red-400', 'h-10 bg-emerald-500', 'h-14 bg-amber-500', 'h-9 bg-purple-400', 'h-11 bg-stone-500'].map((style, index) => <span key={index} className={`w-3 ${style}`} />)}
        </div>

        {viewModel.stations.length === 0 ? (
          <div className="flex min-h-[370px] items-center justify-center text-sm text-slate-500">启动 Goal 后，Worker 会进入对应工位。</div>
        ) : (
          <div className="relative z-10 flex min-h-[390px] min-w-max items-end justify-center gap-10 overflow-visible px-5">
            {viewModel.stations.map((station) => (
              <div key={station.agent.id} className="relative flex w-52 shrink-0 flex-col items-center">
                {selectedStation?.agent.id === station.agent.id ? (
                  <StationPopover
                    station={station}
                    onClose={() => setSelectedStationId(null)}
                    onOpenDetail={onSelectTask}
                    onHandoff={onRequestHandoff}
                    onPause={onPause}
                  />
                ) : null}
                <button type="button" onClick={() => setSelectedStationId(station.agent.id)} className="group flex w-full flex-col items-center" aria-label={`打开${station.agent.name}工位`}>
                  <span className={`mb-2 h-3 w-3 rounded-sm border-2 border-white ${STATUS_LIGHTS[station.status] || STATUS_LIGHTS.idle}`} />
                  <div className="rounded border-2 border-amber-900/50 bg-amber-50 px-4 py-1 text-center shadow-sm">
                    <p className="text-xs font-bold text-stone-800">{station.agent.name}</p>
                    <p className="font-mono text-[9px] text-stone-500">{station.worker?.model_name || station.agent.default_model_id || 'No model'}</p>
                  </div>
                  <PixelWorker status={station.status} role={station.agent.role} />
                  <div className="relative -mt-2 h-24 w-full border-4 border-amber-900/50 bg-amber-100 shadow-[inset_0_-8px_0_rgba(120,53,15,0.12)] group-hover:border-amber-800/70">
                    <div className="absolute inset-x-3 top-3 rounded border border-stone-300 bg-white px-2 py-1.5 text-left shadow-sm">
                      <p className="text-[8px] font-semibold uppercase tracking-wide text-stone-400">Current task</p>
                      <p className="mt-0.5 truncate text-[10px] font-medium text-stone-700">{station.activeTask?.title || 'Awaiting task'}</p>
                    </div>
                    <div className="absolute bottom-2 left-3 flex h-7 w-9 items-center justify-center border border-stone-300 bg-white text-stone-500"><BriefcaseBusiness size={14} /></div>
                    <div className="absolute bottom-2 right-3 h-7 w-12 border border-slate-600 bg-slate-800 shadow-inner"><span className="block h-1 w-8 translate-x-2 translate-y-2 bg-blue-300" /></div>
                  </div>
                </button>
              </div>
            ))}
          </div>
        )}

        {latestHandoff ? (
          <button type="button" onClick={() => onOpenHandoff(latestHandoff.id)} className="absolute bottom-8 left-1/2 z-20 flex w-72 -translate-x-1/2 items-center gap-3 rounded-lg border-2 border-purple-400 bg-purple-50 px-4 py-3 text-left shadow-lg hover:border-purple-500">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded border border-purple-300 bg-purple-100 text-purple-700"><BriefcaseBusiness size={18} /></span>
            <span className="min-w-0">
              <span className="block text-[10px] font-semibold uppercase tracking-wide text-purple-600">Handoff Folder</span>
              <span className="block truncate text-xs font-medium text-purple-900">{latestHandoff.from_agent_name || 'Source'} → {latestHandoff.to_agent_name || 'Target'}</span>
              <span className="block truncate text-[10px] text-purple-700">{latestHandoff.reason_description || latestHandoff.reason}</span>
            </span>
          </button>
        ) : null}
      </div>
    </section>
  );
}

function PixelWorker({ status, role }: { status: string; role: string }) {
  const shirt = role === 'planner' ? 'bg-purple-500' : role === 'reviewer' ? 'bg-amber-500' : role === 'research' ? 'bg-emerald-600' : 'bg-blue-600';
  return (
    <div aria-hidden="true" className={`relative mt-4 h-24 w-20 ${status === 'running' ? 'animate-pixel-work' : ''}`} style={{ imageRendering: 'pixelated' }}>
      <div className="absolute left-5 top-0 h-5 w-10 bg-stone-800" />
      <div className="absolute left-3 top-4 h-10 w-14 border-4 border-stone-800 bg-orange-200">
        <span className="absolute left-2 top-2 h-1.5 w-1.5 bg-stone-900" />
        <span className="absolute right-2 top-2 h-1.5 w-1.5 bg-stone-900" />
        <span className="absolute bottom-2 left-1/2 h-1 w-3 -translate-x-1/2 bg-stone-700" />
      </div>
      <div className={`absolute left-2 top-14 h-8 w-16 border-4 border-stone-800 ${shirt}`} />
      <div className="absolute bottom-0 left-3 h-5 w-5 bg-stone-800" />
      <div className="absolute bottom-0 right-3 h-5 w-5 bg-stone-800" />
    </div>
  );
}
