import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import TaskFlow from '../TaskFlow';

describe('TaskFlow', () => {
  it('presents task cards as a numbered serial workflow', () => {
    render(
      <TaskFlow taskCount={2} handoffCount={1}>
        <div>规划任务</div>
        <div>实现任务</div>
      </TaskFlow>,
    );

    expect(screen.getByRole('region', { name: '任务协作流' })).toBeInTheDocument();
    expect(screen.getByText('当前计划按步骤串行推进；每一步都保留执行者、模型、风险与交接记录。')).toBeInTheDocument();
    expect(screen.getByText('2 步')).toBeInTheDocument();
    expect(screen.getByText('1 次交接')).toBeInTheDocument();
    expect(screen.getByRole('list', { name: '任务执行顺序' })).toHaveTextContent('规划任务');
    expect(screen.getByRole('list', { name: '任务执行顺序' })).toHaveTextContent('实现任务');
  });
});
