import { useState, useMemo } from 'react';
import { Search, RefreshCw, BarChart3 } from 'lucide-react';
import { useOverview, useModelStatus, useUpdateQuotaConfig, useResetQuotaStatus } from '../hooks/useQuota';
import type { QuotaOverviewItem, QuotaStatus } from '../types/quota';
import { STATUS_COLORS, STATUS_BG_COLORS, STATUS_LABELS, PROVIDER_LABELS } from '../types/quota';
import ModelUsageCard from '../components/ModelUsageCard';
import QuotaAlertBanner from '../components/QuotaAlertBanner';

interface SummaryCard {
  key: string;
  label: string;
  count: number;
  colorClass: string;
  dotClass: string;
  borderClass: string;
  statuses: string[];
}

const SORT_OPTIONS = [
  { value: 'usage_percent', label: '使用率' },
  { value: 'last_used_at', label: '最近使用' },
  { value: 'total_tokens', label: '总 tokens' },
  { value: 'model_name', label: '模型名' },
];

export default function QuotaOverviewPage() {
  const [search, setSearch] = useState('');
  const [providerFilter, setProviderFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sortBy, setSortBy] = useState('usage_percent');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [expandedModelId, setExpandedModelId] = useState<string | null>(null);
  const [dismissedAlerts, setDismissedAlerts] = useState<Set<string>>(new Set());

  const { data: overviewData, isLoading, error, refetch } = useOverview({
    provider: providerFilter || undefined,
    status: statusFilter || undefined,
    sort_by: sortBy,
    order: sortOrder,
  });

  const { data: detailData } = useModelStatus(expandedModelId || '');
  const updateQuota = useUpdateQuotaConfig();
  const resetStatus = useResetQuotaStatus();

  const summary = overviewData?.summary;

  const summaryCards = useMemo<SummaryCard[]>(() => {
    if (!summary) return [];
    return [
      {
        key: 'normal',
        label: '正常',
        count: summary.normal_count,
        colorClass: 'text-green-700',
        dotClass: 'bg-green-500',
        borderClass: 'border-green-300',
        statuses: ['normal'],
      },
      {
        key: 'warning',
        label: '警告',
        count: summary.warning_count + summary.near_limit_count,
        colorClass: 'text-yellow-700',
        dotClass: 'bg-yellow-500',
        borderClass: 'border-yellow-300',
        statuses: ['warning', 'near_limit'],
      },
      {
        key: 'limited',
        label: '受限',
        count: summary.limited_count + summary.cooldown_count,
        colorClass: 'text-red-700',
        dotClass: 'bg-red-500',
        borderClass: 'border-red-300',
        statuses: ['limited', 'cooldown'],
      },
      {
        key: 'unknown',
        label: '未知',
        count: summary.unknown_count,
        colorClass: 'text-stone-600',
        dotClass: 'bg-stone-400',
        borderClass: 'border-stone-300',
        statuses: ['unknown'],
      },
    ];
  }, [summary]);

  const filteredModels = useMemo(() => {
    const models = overviewData?.models || [];
    if (!search.trim()) return models;
    const q = search.trim().toLowerCase();
    return models.filter(
      (m) =>
        m.model_name.toLowerCase().includes(q) ||
        m.model_id.toLowerCase().includes(q) ||
        m.provider.toLowerCase().includes(q)
    );
  }, [overviewData, search]);

  const alerts = useMemo(() => {
    const models = overviewData?.models || [];
    return models
      .filter(
        (m) =>
          ['warning', 'near_limit', 'limited', 'cooldown'].includes(m.quota_status) &&
          !dismissedAlerts.has(m.model_id)
      )
      .map((m) => ({
        modelId: m.model_id,
        modelName: m.model_name,
        status: m.quota_status as QuotaStatus,
        usagePercent: m.usage_percent,
      }));
  }, [overviewData, dismissedAlerts]);

  const handleToggleExpand = (modelId: string) => {
    setExpandedModelId((prev) => (prev === modelId ? null : modelId));
  };

  const handleDismissAlert = (modelId: string) => {
    setDismissedAlerts((prev) => new Set([...prev, modelId]));
  };

  const handleUpdateQuota = (modelId: string, data: { token_limit?: number; reset_period?: string }) => {
    updateQuota.mutate({ modelId, request: data });
  };

  const handleResetStatus = (modelId: string) => {
    resetStatus.mutate({ modelId });
  };

  const toggleSortOrder = () => {
    setSortOrder((prev) => (prev === 'desc' ? 'asc' : 'desc'));
  };

  const providers = useMemo(() => {
    const set = new Set<string>();
    overviewData?.models?.forEach((m) => set.add(m.provider));
    return Array.from(set);
  }, [overviewData]);

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-stone-900">Quota Manager</h1>
          <p className="text-sm text-stone-500 mt-0.5">监控所有模型的额度使用状态和风险级别</p>
        </div>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-stone-600 bg-white border border-stone-200 rounded-lg hover:bg-stone-50 transition-colors"
        >
          <RefreshCw size={14} />
          刷新
        </button>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <QuotaAlertBanner alerts={alerts} onDismiss={handleDismissAlert} />
      )}

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {summaryCards.map((card) => (
            <button
              key={card.key}
              onClick={() =>
                setStatusFilter((prev) => {
                  const isActive = card.statuses.includes(prev);
                  return isActive ? '' : card.statuses[0];
                })
              }
              className={`text-left bg-white border rounded-xl p-5 transition-all hover:shadow-sm ${
                card.statuses.includes(statusFilter) ? `border-2 ${card.borderClass}` : 'border-stone-200'
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                <span className={`w-2 h-2 rounded-full ${card.dotClass}`} />
                <span className="text-xs font-medium text-stone-600">{card.label}</span>
              </div>
              <div className={`text-3xl font-bold ${card.colorClass}`}>{card.count}</div>
            </button>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-stone-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索模型..."
            className="w-full pl-9 pr-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300 bg-white"
          />
        </div>
        <select
          value={providerFilter}
          onChange={(e) => setProviderFilter(e.target.value)}
          className="px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300 bg-white"
        >
          <option value="">所有 Provider</option>
          {providers.map((p) => (
            <option key={p} value={p}>
              {PROVIDER_LABELS[p] || p}
            </option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300 bg-white"
        >
          <option value="">所有状态</option>
          <option value="normal">正常</option>
          <option value="warning">警告</option>
          <option value="near_limit">接近上限</option>
          <option value="limited">已受限</option>
          <option value="cooldown">冷却中</option>
          <option value="unknown">未知</option>
        </select>
        <div className="flex items-center gap-1">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300 bg-white"
          >
            {SORT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <button
            onClick={toggleSortOrder}
            className="px-2 py-2 text-sm border border-stone-200 rounded-lg hover:bg-stone-50 bg-white text-stone-600"
          >
            {sortOrder === 'desc' ? '↓' : '↑'}
          </button>
        </div>
      </div>

      {/* Model List */}
      <div className="bg-white border border-stone-200 rounded-xl overflow-hidden">
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-stone-300 border-t-stone-800 rounded-full animate-spin" />
          </div>
        )}

        {error && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="text-stone-400 mb-2">加载失败</div>
            <p className="text-sm text-stone-500">{(error as Error).message}</p>
            <button
              onClick={() => refetch()}
              className="mt-4 px-4 py-2 text-sm text-stone-600 hover:text-stone-800"
            >
              重试
            </button>
          </div>
        )}

        {!isLoading && !error && filteredModels.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <BarChart3 size={48} className="text-stone-300 mb-4" />
            <div className="text-base font-medium text-stone-600 mb-1">暂无额度记录</div>
            <p className="text-sm text-stone-400">
              开始调用模型后，系统会自动记录使用量和额度状态。
            </p>
          </div>
        )}

        {!isLoading && !error && filteredModels.length > 0 && (
          <div className="divide-y divide-stone-100">
            {filteredModels.map((item) => (
              <ModelUsageRow
                key={item.model_id}
                item={item}
                isExpanded={expandedModelId === item.model_id}
                onToggle={() => handleToggleExpand(item.model_id)}
                detail={expandedModelId === item.model_id ? detailData : undefined}
                onUpdateQuota={handleUpdateQuota}
                onResetStatus={handleResetStatus}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

interface ModelUsageRowProps {
  item: QuotaOverviewItem;
  isExpanded: boolean;
  onToggle: () => void;
  detail?: import('../types/quota').QuotaRecord;
  onUpdateQuota?: (modelId: string, data: { token_limit?: number; reset_period?: string }) => void;
  onResetStatus?: (modelId: string) => void;
}

function ModelUsageRow({ item, isExpanded, onToggle, detail, onUpdateQuota, onResetStatus }: ModelUsageRowProps) {
  const usagePct = item.usage_percent !== null && item.usage_percent !== undefined
    ? item.usage_percent * 100
    : null;

  const barColor = usagePct !== null
    ? usagePct >= 100
      ? 'bg-red-500'
      : usagePct >= 90
      ? 'bg-orange-500'
      : usagePct >= 70
      ? 'bg-yellow-500'
      : 'bg-green-500'
    : null;

  const statusClass = STATUS_BG_COLORS[item.quota_status];

  return (
    <div className={`${isExpanded ? 'bg-stone-50' : 'bg-white hover:bg-stone-50'} transition-colors`}>
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-4 px-4 py-3.5 text-left"
      >
        <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${STATUS_COLORS[item.quota_status]}`} />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-stone-800">{item.model_name}</span>
            <span className="text-xs text-stone-400">
              {PROVIDER_LABELS[item.provider] || item.provider}
            </span>
          </div>
        </div>

        <div className="w-40 hidden sm:flex items-center gap-3">
          {usagePct !== null && barColor ? (
            <>
              <div className="flex-1 h-2 bg-stone-200 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${barColor}`}
                  style={{ width: `${Math.min(usagePct, 100)}%` }}
                />
              </div>
              <span className="text-xs font-mono text-stone-600 w-10 text-right">
                {usagePct.toFixed(0)}%
              </span>
            </>
          ) : (
            <div className="flex items-center gap-3">
              <div className="flex-1 h-2 border border-dashed border-stone-300 rounded-full" />
              <span className="text-xs font-mono text-stone-400 w-10 text-right">--</span>
            </div>
          )}
        </div>

        <span className={`hidden md:inline-flex text-[11px] font-semibold uppercase tracking-wide px-2.5 py-0.5 rounded-full border ${statusClass}`}>
          {STATUS_LABELS[item.quota_status]}
        </span>

        <span className="hidden lg:block text-xs text-stone-500 w-24 text-right font-mono">
          {item.total_tokens.toLocaleString()}
        </span>

        <span className="hidden xl:block text-xs text-stone-400 w-20 text-right">
          {item.last_used_at ? formatRelativeTime(item.last_used_at) : '--'}
        </span>
      </button>

      {isExpanded && detail && (
        <div className="border-t border-stone-200">
          <div className="px-4 py-4">
            <ModelUsageCard
              item={item}
              detail={detail}
              onUpdateQuota={onUpdateQuota}
              onResetStatus={onResetStatus}
            />
          </div>
        </div>
      )}
    </div>
  );
}

function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffMin < 1) return '刚刚';
  if (diffMin < 60) return `${diffMin} 分钟前`;
  if (diffHour < 24) return `${diffHour} 小时前`;
  if (diffDay < 7) return `${diffDay} 天前`;
  return date.toLocaleDateString('zh-CN');
}
