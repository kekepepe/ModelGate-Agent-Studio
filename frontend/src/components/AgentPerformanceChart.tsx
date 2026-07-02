import type { ReactNode } from 'react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { DashboardAgentPerformance } from '../types/dashboard';

interface AgentPerformanceChartProps {
  data: DashboardAgentPerformance[];
}

export default function AgentPerformanceChart({ data }: AgentPerformanceChartProps) {
  const chartData = data.map((item) => ({
    ...item,
    success_percent: Math.round(item.success_rate * 100),
  }));

  if (chartData.length === 0) {
    return <EmptyChart title="Agent Performance" message="暂无 Agent 执行数据" />;
  }

  return (
    <ChartCard title="Agent Performance">
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
          <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#78716c' }} stroke="#d6d3d1" />
          <YAxis tick={{ fontSize: 11, fill: '#78716c' }} stroke="#d6d3d1" domain={[0, 100]} />
          <Tooltip formatter={(value) => [`${value}%`, '成功率']} />
          <Bar dataKey="success_percent" fill="#10b981" radius={[4, 4, 0, 0]} />
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
