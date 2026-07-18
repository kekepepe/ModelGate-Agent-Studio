export const RUN_STATUS_LABELS: Record<string, string> = {
  idle: '草稿', planning: '规划中', ready: '已就绪', running: '运行中', paused: '已暂停',
  waiting: '等待中', waiting_approval: '等待审批', handoff: '交接中', reviewing: '审查中',
  completed: '已完成', failed: '失败', cancelled: '已停止', stopped: '已停止', blocked: '已阻塞',
  replanning: '重新规划', revision_required: '需要修订',
};

export function runStatusLabel(status: string) {
  return RUN_STATUS_LABELS[status] || status;
}
