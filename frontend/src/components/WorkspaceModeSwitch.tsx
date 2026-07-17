import { Building2, PanelsTopLeft } from 'lucide-react';
import type { WorkspaceViewMode } from '../utils/workspaceViewModel';

export default function WorkspaceModeSwitch({ mode, onChange }: { mode: WorkspaceViewMode; onChange: (mode: WorkspaceViewMode) => void }) {
  return (
    <div className="inline-flex rounded-lg border border-stone-200 bg-stone-50 p-0.5" aria-label="工作区视图">
      <button
        type="button"
        aria-pressed={mode === 'card'}
        onClick={() => onChange('card')}
        className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${mode === 'card' ? 'bg-white text-blue-700 shadow-sm' : 'text-stone-500 hover:text-stone-800'}`}
      >
        <PanelsTopLeft size={14} /> Card Flow
      </button>
      <button
        type="button"
        aria-pressed={mode === 'pixel'}
        onClick={() => onChange('pixel')}
        className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${mode === 'pixel' ? 'bg-white text-blue-700 shadow-sm' : 'text-stone-500 hover:text-stone-800'}`}
      >
        <Building2 size={14} /> Pixel Office
      </button>
    </div>
  );
}
