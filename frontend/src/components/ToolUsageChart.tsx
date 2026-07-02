import type { ReactNode } from 'react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { DashboardToolUsage } from '../types/dashboard';

interface ToolUsageChartProps {
  data: DashboardToolUsage[];
}

export default function ToolUsageChart({ data }: ToolUsageChartProps) {
  if (data.length === 0) {
    return <EmptyChart title="Tool Usage" message="暂无工具调用数据" />;
  }

  return (
    <ChartCard title="Tool Usage">
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
          <XAxis dataKey="tool_name" tick={{ fontSize: 11, fill: '#78716c' }} stroke="#d6d3d1" />
          <YAxis tick={{ fontSize: 11, fill: '#78716c' }} stroke="#d6d3d1" />
          <Tooltip formatter={(value, name) => [Number(value).toLocaleString(), name === 'call_count' ? '调用次数' : name]} />
          <Bar dataKey="call_count" fill="#60a5fa" radius={[4, 4, 0, 0]} />
        </BarChart>
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
