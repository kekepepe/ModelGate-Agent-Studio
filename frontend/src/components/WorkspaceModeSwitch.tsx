import type { WorkspaceViewMode } from '../utils/workspaceViewModel';

export default function WorkspaceModeSwitch({ mode, onChange }: { mode: WorkspaceViewMode; onChange: (mode: WorkspaceViewMode) => void }) {
  return (
    <div className="workspace-mode-switch" aria-label="工作区视图">
      <button
        type="button"
        aria-pressed={mode === 'card'}
        onClick={() => onChange('card')}
        className={mode === 'card' ? 'is-active' : ''}
        title="Card Flow — 横向 agent flow，1 个工位 1 列"
      >
        Card Flow
      </button>
      <button
        type="button"
        aria-pressed={mode === 'zones'}
        onClick={() => onChange('zones')}
        className={mode === 'zones' ? 'is-active' : ''}
        title="3 Zones — 仿 Star-Office-UI 三区布局：Rest / Working / Problem"
      >
        3 Zones
      </button>
      <button
        type="button"
        aria-pressed={mode === 'pixel'}
        onClick={() => onChange('pixel')}
        className={mode === 'pixel' ? 'is-active' : ''}
        title="Pixel Office — 经典像素风"
      >
        Pixel Office
      </button>
    </div>
  );
}
