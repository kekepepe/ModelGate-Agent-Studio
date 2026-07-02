import type { ReactNode } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { DashboardTrendPoint } from '../types/dashboard';

interface TokenUsageChartProps {
  data: DashboardTrendPoint[];
}

export default function TokenUsageChart({ data }: TokenUsageChartProps) {
  if (data.length === 0 || data.every((item) => item.tokens === 0)) {
    return <EmptyChart title="Token Usage Trend" message="暂无 Token 趋势数据" />;
  }

  return (
    <ChartCard title="Token Usage Trend">
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
          <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#78716c' }} stroke="#d6d3d1" />
          <YAxis tick={{ fontSize: 11, fill: '#78716c' }} stroke="#d6d3d1" />
          <Tooltip formatter={(value) => Number(value).toLocaleString()} />
          <Line type="monotone" dataKey="tokens" stroke="#8b5cf6" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
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

function EmptyChart({ title, message }: { title: string; message: string }) {
  return (
    <ChartCard title={title}>
      <div className="h-[260px] flex items-center justify-center text-sm text-stone-400 border border-dashed border-stone-200 rounded-lg">
        {message}
      </div>
    </ChartCard>
  );
}
