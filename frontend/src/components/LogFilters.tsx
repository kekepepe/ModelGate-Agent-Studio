import { useState } from 'react';
import { Input } from './ui/input';
import { Button } from './ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
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
      <div className="flex flex-wrap items-center gap-1.5">
        <Button
          size="sm"
          variant={!filters.event_type && !filters.event_status ? 'default' : 'outline'}
          onClick={() => handleQuickFilter('')}
        >
          全部
        </Button>
        <Button
          size="sm"
          variant={filters.event_status === 'error,failed' ? 'destructive' : 'outline'}
          onClick={handleErrorsOnly}
        >
          仅错误
        </Button>
        {EVENT_TYPE_OPTIONS.slice(1).map((opt) => (
          <Button
            key={opt.value}
            size="sm"
            variant={filters.event_type === opt.value ? 'default' : 'outline'}
            onClick={() => handleQuickFilter(opt.value)}
          >
            {opt.label}
          </Button>
        ))}
      </div>

      <div className="flex items-center gap-2">
        <Input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="搜索日志内容…"
          className="h-8 flex-1 min-w-0 text-sm"
        />
        <Button size="sm" onClick={handleSearch} className="h-8">
          搜索
        </Button>
        <Select
          value={String(filters.page_size || 20)}
          onValueChange={(v) =>
            onChange({ ...filters, page_size: Number(v), page: 1 })
          }
        >
          <SelectTrigger className="h-8 w-[110px] text-sm">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="10">10 条/页</SelectItem>
            <SelectItem value="20">20 条/页</SelectItem>
            <SelectItem value="50">50 条/页</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
