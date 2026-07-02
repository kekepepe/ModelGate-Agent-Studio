import type { ReactNode } from 'react';
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import type { DashboardModelUsage } from '../types/dashboard';

interface ModelUsagePieChartProps {
  data: DashboardModelUsage[];
}

const COLORS = ['#8b5cf6', '#a8a29e', '#f59e0b', '#10b981', '#ef4444', '#60a5fa'];

export default function ModelUsagePieChart({ data }: ModelUsagePieChartProps) {
  const chartData = data.filter((item) => item.tokens_used > 0);
  if (chartData.length === 0) {
    return <EmptyChart title="Model Usage Distribution" message="暂无模型使用数据" />;
  }

  return (
    <ChartCard title="Model Usage Distribution">
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie
            data={chartData}
            dataKey="tokens_used"
            nameKey="display_name"
            innerRadius={52}
            outerRadius={90}
            paddingAngle={2}
          >
            {chartData.map((item, index) => (
              <Cell key={item.model_id} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(value, _name, props) => [Number(value).toLocaleString(), props.payload.display_name]} />
        </PieChart>
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
