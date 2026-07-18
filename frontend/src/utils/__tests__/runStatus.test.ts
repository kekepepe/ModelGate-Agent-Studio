import { describe, expect, it } from 'vitest';
import { runStatusLabel } from '../runStatus';

describe('runStatusLabel', () => {
  it('maps runtime and stopped states to product copy', () => {
    expect(runStatusLabel('running')).toBe('运行中');
    expect(runStatusLabel('cancelled')).toBe('已停止');
    expect(runStatusLabel('completed')).toBe('已完成');
  });

  it('keeps unknown backend states visible', () => {
    expect(runStatusLabel('future_state')).toBe('future_state');
  });
});
