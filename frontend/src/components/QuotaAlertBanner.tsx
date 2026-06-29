import { AlertTriangle, X } from 'lucide-react';
import type { QuotaStatus } from '../types/quota';
import { STATUS_LABELS } from '../types/quota';

interface AlertItem {
  modelId: string;
  modelName: string;
  status: QuotaStatus;
  usagePercent?: number | null;
}

interface QuotaAlertBannerProps {
  alerts: AlertItem[];
  onDismiss?: (modelId: string) => void;
}

export default function QuotaAlertBanner({ alerts, onDismiss }: QuotaAlertBannerProps) {
  if (!alerts || alerts.length === 0) return null;

  // Show highest priority alert
  const priority: Record<QuotaStatus, number> = {
    limited: 3,
    cooldown: 2,
    near_limit: 1,
    warning: 0,
    normal: -1,
    unknown: -1,
  };

  const sorted = [...alerts].sort((a, b) => priority[b.status] - priority[a.status]);
  const topAlert = sorted[0];

  const isLimited = topAlert.status === 'limited';
  const isCooldown = topAlert.status === 'cooldown';

  const bgClass = isLimited
    ? 'bg-red-50 border-red-200 text-red-800'
    : isCooldown
    ? 'bg-blue-50 border-blue-200 text-blue-800'
    : 'bg-yellow-50 border-yellow-200 text-yellow-800';

  return (
    <div className={`border rounded-lg px-4 py-3 mb-4 flex items-start gap-3 ${bgClass}`}>
      <AlertTriangle size={18} className="shrink-0 mt-0.5" />
      <div className="flex-1 text-sm">
        <span className="font-medium">
          {isLimited
            ? `模型 ${topAlert.modelName} 已受限`
            : isCooldown
            ? `模型 ${topAlert.modelName} 冷却中`
            : `模型 ${topAlert.modelName} ${STATUS_LABELS[topAlert.status]}`}
        </span>
        {topAlert.usagePercent !== null && topAlert.usagePercent !== undefined && (
          <span className="ml-1">
            （使用率 {(topAlert.usagePercent * 100).toFixed(1)}%）
          </span>
        )}
        {sorted.length > 1 && (
          <span className="ml-1 opacity-70">+ 还有 {sorted.length - 1} 个模型预警</span>
        )}
      </div>
      {!isLimited && onDismiss && (
        <button
          onClick={() => onDismiss(topAlert.modelId)}
          className="shrink-0 opacity-60 hover:opacity-100 transition-opacity"
        >
          <X size={14} />
        </button>
      )}
    </div>
  );
}
