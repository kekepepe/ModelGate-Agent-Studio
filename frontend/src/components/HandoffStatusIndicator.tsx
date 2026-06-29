import type { HandoffStatus } from '../types/handoff';
import { HANDOFF_STATUS_LABELS } from '../types/handoff';

const STEPS: HandoffStatus[] = ['requested', 'generating_summary', 'ready', 'accepted', 'completed'];

interface HandoffStatusIndicatorProps {
  status: HandoffStatus;
}

export default function HandoffStatusIndicator({ status }: HandoffStatusIndicatorProps) {
  const failed = status === 'failed';
  const currentIndex = failed ? -1 : STEPS.indexOf(status);

  return (
    <div className="flex items-center gap-2 text-xs" aria-label={`handoff status ${status}`}>
      {STEPS.map((step, index) => {
        const done = !failed && index < currentIndex;
        const current = !failed && index === currentIndex;
        const upcoming = !done && !current;
        return (
          <div key={step} className="flex items-center gap-2">
            <div className="flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full transition-colors ${
                  done
                    ? 'bg-green-500'
                    : current
                    ? step === 'generating_summary'
                      ? 'bg-lavender-500 animate-pulse'
                      : 'bg-lavender-500'
                    : failed
                    ? 'bg-red-300'
                    : 'bg-stone-200'
                }`}
              />
              <span className={`${current ? 'text-lavender-800 font-medium' : done ? 'text-stone-600' : upcoming ? 'text-stone-300' : 'text-red-600'}`}>
                {HANDOFF_STATUS_LABELS[step]}
              </span>
            </div>
            {index < STEPS.length - 1 && <span className="w-4 h-px bg-stone-200" />}
          </div>
        );
      })}
      {failed && <span className="ml-1 text-red-700 font-medium">失败</span>}
    </div>
  );
}
