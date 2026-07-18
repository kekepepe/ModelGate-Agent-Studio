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
          multi_agent: {
            mode: 'parallel_multi_agent', why_multi_agent: 'Frontend and backend are isolated.',
            activated_agent_count: 2, active_agent_count: 0, active_parallelism: 0,
            coordination_task_count: 2, coordination_tokens: 300, productive_tokens: 1500,
            coordination_token_ratio: 0.1667, coordination_duration_ms: 200,
            parallel_task_count: 2, single_agent_serial_baseline_ms: 2000,
            parallel_observed_estimate_ms: 1100, potential_parallel_saving_ms: 900,
            estimated_net_time_benefit_ms: 700, benefit_positive: true,
            measurement_note: 'Estimated from recorded Task durations.',
            mode_comparison: {
              single_agent: { duration_ms: 2000, tokens: 1500, basis: 'productive' },
              sequential_multi_agent: { duration_ms: 2200, tokens: 1800, basis: 'serial' },
              parallel_multi_agent: { duration_ms: 1300, tokens: 1800, basis: 'parallel' },
            },
          },
        }}
      />,
    );

    expect(screen.getByRole('region', { name: '运行总结' })).toBeInTheDocument();
    expect(screen.getByText('质量检查通过')).toBeInTheDocument();
    expect(screen.getByText('Coder model')).toBeInTheDocument();
    expect(screen.getByText(/执行期间发生 1 次 Handoff/)).toBeInTheDocument();
    expect(screen.getByText('parallel multi agent')).toBeInTheDocument();
    expect(screen.getByText(/Frontend and backend are isolated/)).toBeInTheDocument();
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
