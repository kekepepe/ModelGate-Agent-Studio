import { useState } from 'react';
import { ChevronDown, ChevronUp, Settings } from 'lucide-react';
import type { QuotaRecord, QuotaOverviewItem } from '../types/quota';
import { STATUS_BG_COLORS, STATUS_LABELS } from '../types/quota';
import QuotaConfigForm from './QuotaConfigForm';

interface ModelUsageCardProps {
  item: QuotaOverviewItem;
  detail?: QuotaRecord | null;
  onUpdateQuota?: (modelId: string, data: { token_limit?: number; reset_period?: string }) => void;
  onResetStatus?: (modelId: string) => void;
}

export default function ModelUsageCard({ item, detail, onUpdateQuota, onResetStatus }: ModelUsageCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [showConfig, setShowConfig] = useState(false);

  const usagePct = item.usage_percent !== null && item.usage_percent !== undefined
    ? item.usage_percent * 100
    : null;

  const statusClass = STATUS_BG_COLORS[item.quota_status];

  const handleSaveConfig = (data: { token_limit?: number; reset_period?: string }) => {
    onUpdateQuota?.(item.model_id, data);
    setShowConfig(false);
  };

  return (
    <div className="bg-white border border-stone-200 rounded-xl overflow-hidden">
      {/* Header row */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-4 px-4 py-3 text-left hover:bg-stone-50 transition-colors"
      >
        <div className="w-2 h-2 rounded-full shrink-0 bg-stone-300" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-stone-800">{item.model_name}</span>
            <span className="text-xs text-stone-400">{item.provider}</span>
          </div>
        </div>

        {/* Usage bar */}
        <div className="w-32 hidden sm:block">
          {usagePct !== null ? (
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 bg-stone-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    usagePct >= 90
                      ? 'bg-red-500'
                      : usagePct >= 70
                      ? 'bg-yellow-500'
                      : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(usagePct, 100)}%` }}
                />
              </div>
              <span className="text-xs text-stone-500 w-10 text-right">
                {usagePct.toFixed(0)}%
              </span>
            </div>
          ) : (
            <span className="text-xs text-stone-400">--</span>
          )}
        </div>

        {/* Status tag */}
        <span className={`text-xs px-2 py-0.5 rounded-full border ${statusClass}`}>
          {STATUS_LABELS[item.quota_status]}
        </span>

        {expanded ? <ChevronUp size={16} className="text-stone-400" /> : <ChevronDown size={16} className="text-stone-400" />}
      </button>

      {/* Expanded detail */}
      {expanded && detail && (
        <div className="border-t border-stone-100 px-4 py-4 space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <div className="text-xs text-stone-400 mb-0.5">调用次数</div>
              <div className="text-sm font-medium text-stone-700">{detail.request_count.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-xs text-stone-400 mb-0.5">Input tokens</div>
              <div className="text-sm font-medium text-stone-700">{detail.input_tokens.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-xs text-stone-400 mb-0.5">Output tokens</div>
              <div className="text-sm font-medium text-stone-700">{detail.output_tokens.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-xs text-stone-400 mb-0.5">总 tokens</div>
              <div className="text-sm font-medium text-stone-700">{detail.total_tokens.toLocaleString()}</div>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            <div>
              <div className="text-xs text-stone-400 mb-0.5">额度模式</div>
              <div className="text-sm font-medium text-stone-700">
                {detail.quota_mode === 'known' ? '已设定' : detail.quota_mode === 'estimated' ? '估算' : '未知'}
              </div>
            </div>
            <div>
              <div className="text-xs text-stone-400 mb-0.5">Token 上限</div>
              <div className="text-sm font-medium text-stone-700">
                {detail.token_limit ? detail.token_limit.toLocaleString() : '未设置'}
              </div>
            </div>
            <div>
              <div className="text-xs text-stone-400 mb-0.5">额度错误次数</div>
              <div className="text-sm font-medium text-stone-700">
                {detail.limit_error_count > 0 ? (
                  <span className="text-red-600">{detail.limit_error_count}</span>
                ) : (
                  '0'
                )}
              </div>
            </div>
          </div>

          {detail.last_used_at && (
            <div className="text-xs text-stone-400">
              最近使用: {new Date(detail.last_used_at).toLocaleString('zh-CN')}
            </div>
          )}

          {detail.cooldown_until && (
            <div className="text-xs text-blue-600">
              冷却至: {new Date(detail.cooldown_until).toLocaleString('zh-CN')}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2 pt-2">
            {(detail.quota_mode === 'unknown' || detail.quota_mode === 'estimated') && (
              <button
                onClick={() => setShowConfig(!showConfig)}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-lavender-700 bg-lavender-50 hover:bg-lavender-100 rounded-lg transition-colors"
              >
                <Settings size={12} />
                设置额度
              </button>
            )}
            {detail.quota_status !== 'normal' && detail.quota_status !== 'unknown' && (
              <button
                onClick={() => onResetStatus?.(item.model_id)}
                className="px-3 py-1.5 text-xs font-medium text-stone-600 bg-white border border-stone-200 hover:bg-stone-50 rounded-lg transition-colors"
              >
                标记为正常
              </button>
            )}
          </div>

          {showConfig && (
            <QuotaConfigForm
              initialTokenLimit={detail.token_limit}
              initialRequestLimit={detail.request_limit}
              initialCostLimit={detail.cost_limit}
              initialResetPeriod={detail.reset_period}
              initialResetDate={detail.reset_date}
              onSave={handleSaveConfig}
              onCancel={() => setShowConfig(false)}
            />
          )}
        </div>
      )}
    </div>
  );
}
