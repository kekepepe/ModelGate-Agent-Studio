import { useState } from 'react';

interface QuotaConfigFormProps {
  initialTokenLimit?: number;
  initialRequestLimit?: number;
  initialCostLimit?: number;
  initialResetPeriod?: string;
  initialResetDate?: number;
  onSave: (data: {
    token_limit?: number;
    request_limit?: number;
    cost_limit?: number;
    reset_period?: string;
    reset_date?: number;
  }) => void;
  onCancel: () => void;
}

const PERIOD_OPTIONS = [
  { value: 'daily', label: '每日' },
  { value: 'weekly', label: '每周' },
  { value: 'monthly', label: '每月' },
  { value: 'never', label: '永不' },
];

export default function QuotaConfigForm({
  initialTokenLimit,
  initialRequestLimit,
  initialCostLimit,
  initialResetPeriod,
  initialResetDate,
  onSave,
  onCancel,
}: QuotaConfigFormProps) {
  const [tokenLimit, setTokenLimit] = useState(initialTokenLimit?.toString() || '');
  const [requestLimit, setRequestLimit] = useState(initialRequestLimit?.toString() || '');
  const [costLimit, setCostLimit] = useState(initialCostLimit?.toString() || '');
  const [resetPeriod, setResetPeriod] = useState(initialResetPeriod || 'monthly');
  const [resetDate, setResetDate] = useState(initialResetDate?.toString() || '');

  const showResetDate = resetPeriod === 'monthly';

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const limit = tokenLimit ? parseInt(tokenLimit, 10) : undefined;
    const reqLimit = requestLimit ? parseInt(requestLimit, 10) : undefined;
    const cLimit = costLimit ? parseFloat(costLimit) : undefined;
    const rDate = resetDate ? parseInt(resetDate, 10) : undefined;
    onSave({
      token_limit: limit,
      request_limit: reqLimit,
      cost_limit: cLimit,
      reset_period: resetPeriod,
      reset_date: rDate,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="bg-stone-50 rounded-lg p-4 space-y-3">
      <div>
        <label className="block text-xs font-medium text-stone-600 mb-1">
          Token 上限 <span className="text-red-500">*</span>
        </label>
        <input
          type="number"
          min={1}
          value={tokenLimit}
          onChange={(e) => setTokenLimit(e.target.value)}
          placeholder="例如: 1000000"
          className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-300"
          required
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-stone-600 mb-1">
            请求数上限
          </label>
          <input
            type="number"
            min={1}
            value={requestLimit}
            onChange={(e) => setRequestLimit(e.target.value)}
            placeholder="次"
            className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-300"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-stone-600 mb-1">
            费用上限 (USD)
          </label>
          <input
            type="number"
            min={0}
            step="0.01"
            value={costLimit}
            onChange={(e) => setCostLimit(e.target.value)}
            placeholder="USD"
            className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-300"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-stone-600 mb-1">
            重置周期
          </label>
          <select
            value={resetPeriod}
            onChange={(e) => setResetPeriod(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-300 bg-white"
          >
            {PERIOD_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
        {showResetDate && (
          <div>
            <label className="block text-xs font-medium text-stone-600 mb-1">
              重置日期 (1-31)
            </label>
            <input
              type="number"
              min={1}
              max={31}
              value={resetDate}
              onChange={(e) => setResetDate(e.target.value)}
              placeholder="1-31"
              className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-300"
            />
          </div>
        )}
      </div>

      <div className="flex gap-2 pt-1">
        <button
          type="button"
          onClick={onCancel}
          className="flex-1 px-3 py-2 text-xs font-medium text-stone-600 bg-white border border-stone-200 hover:bg-stone-100 rounded-lg transition-colors"
        >
          取消
        </button>
        <button
          type="submit"
          className="flex-1 px-3 py-2 text-xs font-medium text-white bg-lavender-600 hover:bg-lavender-700 rounded-lg transition-colors"
        >
          保存
        </button>
      </div>
    </form>
  );
}
