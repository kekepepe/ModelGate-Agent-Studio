import { useEffect } from 'react';
import type { WorkspaceHandoff, WorkspaceTask } from '../types/workspace';
import TaskDetailPanel from './TaskDetailPanel';

export default function AgentDetailModal({ task, isLoading, handoffs, onClose, onOpenHandoff, onPause, onRetry, onHandoff }: {
  task?: WorkspaceTask | null;
  isLoading?: boolean;
  handoffs?: WorkspaceHandoff[];
  onClose: () => void;
  onOpenHandoff?: (handoffId: string) => void;
  onPause?: () => void;
  onRetry?: () => void;
  onHandoff?: () => void;
}) {
  useEffect(() => {
    if (!task) return;
    const handleKeyDown = (event: KeyboardEvent) => { if (event.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [task, onClose]);

  if (!task) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-stone-950/35 p-4" role="presentation" onMouseDown={(event) => { if (event.currentTarget === event.target) onClose(); }}>
      <div role="dialog" aria-modal="true" aria-label={`${task.title}详情`} className="h-[min(680px,88vh)] w-full max-w-4xl overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-2xl">
        <TaskDetailPanel
          task={task}
          isLoading={isLoading}
          onClose={onClose}
          handoffs={handoffs}
          onOpenHandoff={onOpenHandoff}
          onPause={onPause}
          onRetry={onRetry}
          onHandoff={onHandoff}
          variant="modal"
        />
      </div>
    </div>
  );
}
