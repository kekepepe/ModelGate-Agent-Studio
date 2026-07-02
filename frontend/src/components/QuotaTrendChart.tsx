import type { ReactNode } from 'react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { DashboardTrendPoint } from '../types/dashboard';

interface QuotaTrendChartProps {
  data: DashboardTrendPoint[];
  compact?: boolean;
}

export default function QuotaTrendChart({ data, compact }: QuotaTrendChartProps) {
  if (data.length === 0 || data.every((item) => item.quota_usage_percent === 0)) {
    return <EmptyChart title="Quota Trend" message="暂无 Quota 趋势数据" compact={compact} />;
  }

  return (
    <ChartCard title="Quota Trend">
      <ResponsiveContainer width="100%" height={compact ? 220 : 260}>
        <AreaChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
          <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#78716c' }} stroke="#d6d3d1" />
          <YAxis tick={{ fontSize: 11, fill: '#78716c' }} stroke="#d6d3d1" domain={[0, 100]} />
          <Tooltip formatter={(value) => [`${Number(value).toFixed(1)}%`, 'Quota 使用率']} />
          <Area type="monotone" dataKey="quota_usage_percent" stroke="#f59e0b" fill="#fef3c7" strokeWidth={2} />
        </AreaChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

function ChartCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="bg-white border border-stone-200 rounded-xl p-4">
      <h2 className="text-sm font-semibold text-stone-800 mb-4">{title}</h2>
      {children}
    </div>
  );
}

function EmptyChart({ title, message, compact }: { title: string; message: string; compact?: boolean }) {
  return (
    <ChartCard title={title}>
      <div className={`${compact ? 'h-[220px]' : 'h-[260px]'} flex items-center justify-center text-sm text-stone-400 border border-dashed border-stone-200 rounded-lg`}>
        {message}
      </div>
    </ChartCard>
  );
}
