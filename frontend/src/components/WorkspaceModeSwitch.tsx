import type { WorkspaceViewMode } from '../utils/workspaceViewModel';

export default function WorkspaceModeSwitch({ mode, onChange }: { mode: WorkspaceViewMode; onChange: (mode: WorkspaceViewMode) => void }) {
  return (
    <div className="workspace-mode-switch" aria-label="工作区视图">
      <button
        type="button"
        aria-pressed={mode === 'card'}
        onClick={() => onChange('card')}
        className={mode === 'card' ? 'is-active' : ''}
      >
        Card Flow
      </button>
      <button
        type="button"
        aria-pressed={mode === 'pixel'}
        onClick={() => onChange('pixel')}
        className={mode === 'pixel' ? 'is-active' : ''}
      >
        Pixel Office
      </button>
    </div>
  );
}
