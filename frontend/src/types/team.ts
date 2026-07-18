export type TeamRolePreset = {
  role: string;
  label: string;
  purpose: string;
  modelHint: string;
};

export type TeamPreset = {
  id: string;
  name: string;
  description: string;
  category: string;
  accent: 'blue' | 'green' | 'purple' | 'amber';
  roles: TeamRolePreset[];
  capabilities: string[];
  executionPolicy: {
    preferSingleAgent: boolean;
    maxParallel: number;
    independentReview: 'high_risk' | 'always' | 'on_demand';
    isolationRequiredForParallelWrites: boolean;
  };
  defaultGoal: string;
  defaultCriteria: string[];
};

export const TEAM_PRESETS: TeamPreset[] = [
  {
    id: 'code-delivery',
    name: '代码交付团队',
    description: '把需求拆解、编码、验证和审查串成一次可追踪交付。',
    category: 'Development',
    accent: 'blue',
    roles: [
      { role: 'planner', label: 'Planner', purpose: '拆解目标与验收条件', modelHint: 'Reasoning model' },
      { role: 'coder', label: 'Coder', purpose: '实现与运行验证', modelHint: 'Code model' },
      { role: 'reviewer', label: 'Reviewer', purpose: '独立检查质量与风险', modelHint: 'Review model' },
    ],
    capabilities: ['planning', 'code_read', 'code_edit', 'test', 'review'],
    executionPolicy: { preferSingleAgent: true, maxParallel: 2, independentReview: 'high_risk', isolationRequiredForParallelWrites: true },
    defaultGoal: '完成一个可验证的代码交付',
    defaultCriteria: ['功能按要求实现', '测试与构建通过', '代码经过独立审查'],
  },
  {
    id: 'deep-research',
    name: '深度调研团队',
    description: '从问题拆解、资料检索到综合结论与风险校验。',
    category: 'Research',
    accent: 'green',
    roles: [
      { role: 'planner', label: 'Planner', purpose: '定义问题和证据标准', modelHint: 'Reasoning model' },
      { role: 'research', label: 'Researcher', purpose: '检索和整理证据', modelHint: 'Long-context model' },
      { role: 'summarizer', label: 'Synthesizer', purpose: '综合结论与结构', modelHint: 'Writing model' },
      { role: 'reviewer', label: 'Reviewer', purpose: '检查来源与遗漏', modelHint: 'Review model' },
    ],
    capabilities: ['planning', 'research', 'data_analysis', 'document_write', 'review'],
    executionPolicy: { preferSingleAgent: true, maxParallel: 3, independentReview: 'on_demand', isolationRequiredForParallelWrites: true },
    defaultGoal: '完成一份来源清晰、结论可追溯的调研报告',
    defaultCriteria: ['关键判断有证据支持', '区分事实、推断与风险', '给出可执行结论'],
  },
  {
    id: 'document-production',
    name: '文档生产团队',
    description: '围绕既有材料产出结构完整、可审阅的正式文档。',
    category: 'Content',
    accent: 'purple',
    roles: [
      { role: 'planner', label: 'Planner', purpose: '确定结构与完成标准', modelHint: 'Reasoning model' },
      { role: 'research', label: 'Researcher', purpose: '提取事实和材料', modelHint: 'Long-context model' },
      { role: 'summarizer', label: 'Writer', purpose: '形成完整正文', modelHint: 'Writing model' },
      { role: 'reviewer', label: 'Reviewer', purpose: '检查一致性与可交付性', modelHint: 'Review model' },
    ],
    capabilities: ['planning', 'research', 'document_write', 'review'],
    executionPolicy: { preferSingleAgent: true, maxParallel: 2, independentReview: 'on_demand', isolationRequiredForParallelWrites: true },
    defaultGoal: '根据现有材料完成一份正式交付文档',
    defaultCriteria: ['结构符合目标用途', '内容有材料依据', '格式和表述可直接交付'],
  },
  {
    id: 'custom-team',
    name: '自定义团队',
    description: '从现有 Agent 资产中组合自己的角色、模型和交接策略。',
    category: 'Custom',
    accent: 'amber',
    roles: [
      { role: 'planner', label: 'Planner', purpose: '规划团队协作', modelHint: 'Choose model' },
      { role: 'coder', label: 'Executor', purpose: '完成主要任务', modelHint: 'Choose model' },
      { role: 'reviewer', label: 'Reviewer', purpose: '审查最终产出', modelHint: 'Choose model' },
    ],
    capabilities: ['planning', 'research', 'code_read', 'code_edit', 'test', 'review', 'document_write'],
    executionPolicy: { preferSingleAgent: true, maxParallel: 3, independentReview: 'high_risk', isolationRequiredForParallelWrites: true },
    defaultGoal: '',
    defaultCriteria: ['达到自定义完成标准'],
  },
];

export function getTeamPreset(id?: string | null): TeamPreset {
  return TEAM_PRESETS.find((preset) => preset.id === id) || TEAM_PRESETS[0];
}
