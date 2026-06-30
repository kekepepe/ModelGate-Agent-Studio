import { useState } from 'react';
import type { LogFilters as LogFiltersType } from '../types/log';

interface LogFiltersProps {
  filters: LogFiltersType;
  onChange: (filters: LogFiltersType) => void;
}

const EVENT_TYPE_OPTIONS = [
  { value: '', label: '全部类型' },
  { value: 'model_call', label: '模型调用' },
  { value: 'agent_step', label: 'Agent 步骤' },
  { value: 'tool_call', label: '工具调用' },
  { value: 'handoff_created,handoff_completed', label: '交接' },
  { value: 'error', label: '错误' },
  { value: 'task_status_change', label: '任务状态' },
];

export default function LogFilters({ filters, onChange }: LogFiltersProps) {
  const [search, setSearch] = useState(filters.search || '');

  const handleSearch = () => {
    onChange({ ...filters, search, page: 1 });
  };

  const handleQuickFilter = (eventType: string) => {
    onChange({ ...filters, event_type: eventType, event_status: '', page: 1 });
  };

  const handleErrorsOnly = () => {
    onChange({ ...filters, event_status: 'error,failed', event_type: '', page: 1 });
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <button
          onClick={() => handleQuickFilter('')}
          className={`px-2.5 py-1 text-xs rounded-lg border transition-colors ${
            !filters.event_type && !filters.event_status
              ? 'bg-stone-800 text-white border-stone-800'
              : 'bg-white text-stone-600 border-stone-200 hover:border-stone-300'
          }`}
        >
          全部
        </button>
        <button
          onClick={handleErrorsOnly}
          className={`px-2.5 py-1 text-xs rounded-lg border transition-colors ${
            filters.event_status === 'error,failed'
              ? 'bg-red-700 text-white border-red-700'
              : 'bg-white text-stone-600 border-stone-200 hover:border-stone-300'
          }`}
        >
          仅错误
        </button>
        {EVENT_TYPE_OPTIONS.slice(1).map((opt) => (
          <button
            key={opt.value}
            onClick={() => handleQuickFilter(opt.value)}
            className={`px-2.5 py-1 text-xs rounded-lg border transition-colors ${
              filters.event_type === opt.value
                ? 'bg-stone-800 text-white border-stone-800'
                : 'bg-white text-stone-600 border-stone-200 hover:border-stone-300'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <div className="flex items-center gap-2">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="搜索日志内容..."
          className="flex-1 min-w-0 px-3 py-1.5 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-stone-400"
        />
        <button
          onClick={handleSearch}
          className="px-3 py-1.5 text-sm bg-stone-800 text-white rounded-lg hover:bg-stone-900"
        >
          搜索
        </button>
        <select
          value={filters.page_size || 20}
          onChange={(e) => onChange({ ...filters, page_size: Number(e.target.value), page: 1 })}
          className="px-2 py-1.5 text-sm border border-stone-200 rounded-lg"
        >
          <option value={10}>10 条/页</option>
          <option value={20}>20 条/页</option>
          <option value={50}>50 条/页</option>
        </select>
      </div>
    </div>
  );
}
