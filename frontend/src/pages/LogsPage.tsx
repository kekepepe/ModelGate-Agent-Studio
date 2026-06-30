import { useRef, useState } from 'react';
import { useLogsQuery, useLogDetailQuery, useTaskTimelineQuery } from '../hooks/useLogs';
import type { ExecutionLog, LogFilters as LogFiltersType } from '../types/log';
import LogListItem from '../components/LogListItem';
import LogFilters from '../components/LogFilters';
import LogDetailDrawer from '../components/LogDetailDrawer';
import TaskTimeline from '../components/TaskTimeline';

export default function LogsPage() {
  const [filters, setFilters] = useState<LogFiltersType>({ page: 1, page_size: 20 });
  const [selectedLogId, setSelectedLogId] = useState<string | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'list' | 'timeline'>('list');
  const seenIds = useRef<Set<string>>(new Set());

  const { data: logsData, isLoading: logsLoading, error: logsError } = useLogsQuery(filters);
  const { data: logDetail } = useLogDetailQuery(selectedLogId);
  const { data: timelineData, isLoading: timelineLoading } = useTaskTimelineQuery(selectedTaskId);

  const getNewIds = (items: ExecutionLog[]) => {
    const newIds = new Set<string>();
    items.forEach((item) => {
      if (!seenIds.current.has(item.id)) {
        newIds.add(item.id);
        seenIds.current.add(item.id);
      }
    });
    return newIds;
  };

  const newIds = logsData?.items ? getNewIds(logsData.items) : new Set<string>();

  const handlePageChange = (page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  };

  const totalPages = logsData?.total_pages || 0;
  const currentPage = logsData?.page || 1;

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-stone-900">执行日志</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={() => { setViewMode('list'); setSelectedTaskId(null); }}
            className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
              viewMode === 'list'
                ? 'bg-stone-800 text-white border-stone-800'
                : 'bg-white text-stone-600 border-stone-200 hover:border-stone-300'
            }`}
          >
            日志列表
          </button>
          <button
            onClick={() => setViewMode('timeline')}
            className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
              viewMode === 'timeline'
                ? 'bg-stone-800 text-white border-stone-800'
                : 'bg-white text-stone-600 border-stone-200 hover:border-stone-300'
            }`}
          >
            Task 时间线
          </button>
        </div>
      </div>

      {viewMode === 'list' && (
        <>
          <div className="mb-4">
            <LogFilters filters={filters} onChange={setFilters} />
          </div>

          {logsError && (
            <div className="border border-red-200 bg-red-50 text-red-700 rounded-lg px-3 py-2 text-sm mb-4">
              日志加载失败: {logsError.message}
            </div>
          )}

          <div className="bg-white rounded-xl border border-stone-200 shadow-sm overflow-hidden">
            {logsLoading && (
              <div className="p-4 space-y-3">
                <div className="h-12 bg-stone-200 rounded animate-pulse" />
                <div className="h-12 bg-stone-200 rounded animate-pulse" />
                <div className="h-12 bg-stone-200 rounded animate-pulse" />
              </div>
            )}

            {!logsLoading && logsData?.items.length === 0 && (
              <div className="flex items-center justify-center h-40 text-stone-400 text-sm">
                暂无日志记录
              </div>
            )}

            {!logsLoading && logsData?.items.map((log: ExecutionLog) => (
              <LogListItem
                key={log.id}
                log={log}
                isSelected={selectedLogId === log.id}
                isNew={newIds.has(log.id)}
                onClick={() => setSelectedLogId(log.id)}
              />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-4">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage <= 1}
                className="px-3 py-1.5 text-sm border border-stone-200 rounded-lg disabled:opacity-40 hover:bg-stone-50"
              >
                上一页
              </button>
              <span className="text-sm text-stone-500">
                {currentPage} / {totalPages}
              </span>
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage >= totalPages}
                className="px-3 py-1.5 text-sm border border-stone-200 rounded-lg disabled:opacity-40 hover:bg-stone-50"
              >
                下一页
              </button>
            </div>
          )}
        </>
      )}

      {viewMode === 'timeline' && (
        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-4">
          <div className="bg-white rounded-xl border border-stone-200 shadow-sm p-4">
            <h3 className="text-sm font-semibold text-stone-700 mb-3">选择 Task</h3>
            <TaskSelector onSelect={setSelectedTaskId} selectedTaskId={selectedTaskId} />
          </div>
          <div className="bg-white rounded-xl border border-stone-200 shadow-sm min-h-[400px]">
            <TaskTimeline timeline={timelineData || null} isLoading={timelineLoading} />
          </div>
        </div>
      )}

      {selectedLogId && logDetail && (
        <LogDetailDrawer log={logDetail} onClose={() => setSelectedLogId(null)} />
      )}
    </div>
  );
}

function TaskSelector({ onSelect, selectedTaskId }: { onSelect: (id: string) => void; selectedTaskId: string | null }) {
  const { data: logsData } = useLogsQuery({ page_size: 100 });

  const taskMap = new Map<string, { taskId: string; taskTitle?: string | null; goalId?: string | null }>();
  logsData?.items.forEach((log) => {
    if (log.task_id && !taskMap.has(log.task_id)) {
      taskMap.set(log.task_id, {
        taskId: log.task_id,
        taskTitle: log.task_title,
        goalId: log.goal_id,
      });
    }
  });

  const tasks = Array.from(taskMap.values());

  if (tasks.length === 0) {
    return <p className="text-xs text-stone-400">暂无 Task 数据，请先在日志列表中生成一些日志。</p>;
  }

  return (
    <div className="space-y-1 max-h-[400px] overflow-y-auto">
      {tasks.map((task) => (
        <button
          key={task.taskId}
          onClick={() => onSelect(task.taskId)}
          className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
            selectedTaskId === task.taskId
              ? 'bg-stone-100 text-stone-900'
              : 'text-stone-600 hover:bg-stone-50'
          }`}
        >
          <div className="font-medium truncate">{task.taskTitle || `Task ${task.taskId.slice(0, 8)}`}</div>
          <div className="text-xs text-stone-400 font-mono truncate">{task.taskId}</div>
        </button>
      ))}
    </div>
  );
}
