import { useState } from 'react';
import type { TaskTimelineResponse, TimelineEvent } from '../types/log';
import { LOG_EVENT_TYPE_ICONS, LOG_EVENT_TYPE_LABELS, TIMELINE_NODE_COLORS } from '../types/log';
import LogDetailDrawer from './LogDetailDrawer';

interface TaskTimelineProps {
  timeline?: TaskTimelineResponse | null;
  isLoading?: boolean;
}

export default function TaskTimeline({ timeline, isLoading = false }: TaskTimelineProps) {
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null);

  if (isLoading) {
    return (
      <div className="space-y-4 p-4">
        <div className="h-4 bg-stone-200 rounded animate-pulse w-1/3" />
        <div className="h-20 bg-stone-200 rounded animate-pulse" />
        <div className="h-20 bg-stone-200 rounded animate-pulse" />
      </div>
    );
  }

  if (!timeline || timeline.events.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-stone-400 text-sm">
        该 Task 暂无执行日志
      </div>
    );
  }

  const { events, summary } = timeline;

  return (
    <div className="p-4">
      <div className="grid grid-cols-5 gap-2 mb-6">
        <StatCard label="总耗时" value={formatDuration(summary.total_duration_ms)} />
        <StatCard label="总 Token" value={summary.total_tokens.toLocaleString()} />
        <StatCard label="模型调用" value={summary.model_call_count.toString()} />
        <StatCard label="交接次数" value={summary.handoff_count.toString()} />
        <StatCard label="错误次数" value={summary.error_count.toString()} />
      </div>

      <div className="relative">
        <div className="absolute left-4 top-0 bottom-0 w-px bg-stone-200" />
        <div className="space-y-4">
          {events.map((event, idx) => {
            const nodeColor = TIMELINE_NODE_COLORS[event.event_type] || 'bg-stone-400';
            const isError = event.event_status === 'error' || event.event_status === 'failed';
            return (
              <div
                key={idx}
                className={`relative pl-10 cursor-pointer group ${isError ? 'bg-red-50 rounded-lg -mx-2 px-2 py-2' : 'py-1'}`}
                onClick={() => setSelectedEvent(event)}
              >
                <div className={`absolute left-2.5 top-2 w-3 h-3 rounded-full ${nodeColor} ring-2 ring-white`} />
                <div className="flex items-center gap-2 text-xs text-stone-400 mb-0.5">
                  <span>{event.time ? new Date(event.time).toLocaleString('zh-CN') : ''}</span>
                  <span className="text-lg leading-none">{LOG_EVENT_TYPE_ICONS[event.event_type] || '•'}</span>
                  <span className="font-medium text-stone-600">{LOG_EVENT_TYPE_LABELS[event.event_type] || event.event_type}</span>
                </div>
                <p className="text-sm text-stone-700 leading-snug truncate group-hover:text-stone-900">
                  {event.summary}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {selectedEvent && (
        <LogDetailDrawer
          log={{
            id: `timeline-${selectedEvent.time}`,
            event_type: selectedEvent.event_type as any,
            event_status: selectedEvent.event_status as any,
            agent_id: selectedEvent.agent_id,
            model_id: selectedEvent.model_id,
            output_summary: selectedEvent.summary,
            created_at: selectedEvent.time,
          }}
          onClose={() => setSelectedEvent(null)}
        />
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-stone-200 p-2 text-center">
      <div className="text-[10px] text-stone-400 uppercase tracking-wide">{label}</div>
      <div className="text-sm font-semibold text-stone-800 mt-0.5">{value}</div>
    </div>
  );
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${Math.floor(ms / 1000)}s`;
  const min = Math.floor(ms / 60000);
  const sec = Math.floor((ms % 60000) / 1000);
  return `${min}m ${sec}s`;
}
