import { STATUS_CONFIG } from '../types/agent';
import type { AgentStatus } from '../types/agent';

interface StatusIndicatorProps {
  status: AgentStatus;
}

export default function StatusIndicator({ status }: StatusIndicatorProps) {
  const config = STATUS_CONFIG[status] || { label: status, dot: 'bg-stone-400', text: 'text-stone-500' };

  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${config.text}`}>
      <span
        className={`inline-block w-2 h-2 rounded-full ${config.dot} ${config.animate ? 'animate-pulse' : ''}`}
        style={config.animate ? { boxShadow: '0 0 0 0 rgba(59, 130, 246, 0.4)' } : undefined}
      />
      {config.label}
    </span>
  );
}
