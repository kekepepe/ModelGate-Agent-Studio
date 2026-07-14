import { describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import FinalOutputPanel from '../FinalOutputPanel';

describe('FinalOutputPanel', () => {
  it('renders the inspectable completion report when runtime provides one', () => {
    render(
      <FinalOutputPanel
        status="completed"
        tasksCompleted={3}
        tasksFailed={0}
        tasksHandoff={1}
        totalTokens={1800}
        logCount={12}
        finalSummary={{
          completed: ['Plan', 'Build', 'Review'],
          incomplete: [],
          quality: { status: 'completed', passed: true, summary: 'All required checks passed.' },
          risks: ['执行期间发生 1 次 Handoff'],
          models: [{ id: 'm-1', name: 'Coder model', cost_level: 2 }],
          handoff_count: 1,
          cost: { available: false, note: '尚未配置 Provider 单价表；当前只展示模型相对 cost_level，不虚构货币成本。' },
        }}
      />,
    );

    expect(screen.getByRole('region', { name: '运行总结' })).toBeInTheDocument();
    expect(screen.getByText('质量检查通过')).toBeInTheDocument();
    expect(screen.getByText('Coder model')).toBeInTheDocument();
    expect(screen.getByText(/执行期间发生 1 次 Handoff/)).toBeInTheDocument();
  });

  it('lists each task output and opens the selected task', () => {
    const onOpenTask = vi.fn();
    render(
      <FinalOutputPanel
        status="completed"
        tasksCompleted={1}
        tasksFailed={0}
        tasksHandoff={0}
        totalTokens={500}
        logCount={3}
        taskOutputs={[{ id: 'task-1', title: '实现登录页', output: '登录页面代码已生成。' }]}
        onOpenTask={onOpenTask}
      />,
    );

    fireEvent.click(screen.getByText('实现登录页'));
    expect(onOpenTask).toHaveBeenCalledWith('task-1');
  });
});
