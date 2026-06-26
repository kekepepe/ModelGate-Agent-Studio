import { useState, useEffect } from 'react';
import { X, AlertTriangle } from 'lucide-react';
import type { AgentStation, AgentCreateData, AgentUpdateData } from '../types/agent';
import { MOCK_MODELS, MOCK_TOOLS } from '../types/agent';

interface AgentConfigFormProps {
  agent?: AgentStation;
  initialData?: Partial<AgentCreateData>;
  onSave: (data: AgentCreateData | AgentUpdateData) => void;
  onCancel: () => void;
  isSubmitting?: boolean;
  error?: string | null;
}

const defaultForm: AgentCreateData = {
  name: '',
  role: 'coder',
  description: '',
  default_model_id: '',
  backup_model_ids: [],
  allowed_tools: [],
  system_prompt: '',
  output_format: 'markdown',
  max_steps_per_task: 10,
  allow_handoff: false,
  handoff_threshold_tokens: undefined,
};

export default function AgentConfigForm({ agent, initialData, onSave, onCancel, isSubmitting, error }: AgentConfigFormProps) {
  const isEdit = !!agent;

  const [form, setForm] = useState<AgentCreateData>(defaultForm);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState<string | null>(error || null);

  useEffect(() => {
    if (agent) {
      setForm({
        name: agent.name,
        role: agent.role,
        description: agent.description || '',
        default_model_id: agent.default_model_id,
        backup_model_ids: agent.backup_model_ids || [],
        allowed_tools: agent.allowed_tools || [],
        system_prompt: agent.system_prompt || '',
        output_format: agent.output_format || 'markdown',
        max_steps_per_task: agent.max_steps_per_task,
        allow_handoff: agent.allow_handoff,
        handoff_threshold_tokens: agent.handoff_threshold_tokens,
      });
    } else if (initialData) {
      setForm({ ...defaultForm, ...initialData });
    } else {
      setForm(defaultForm);
    }
    setApiError(null);
  }, [agent, initialData]);

  useEffect(() => {
    setApiError(error || null);
  }, [error]);

  const validate = (): boolean => {
    const errs: Record<string, string> = {};
    if (!form.name?.trim()) errs.name = 'Agent 名称不能为空';
    if (!form.role) errs.role = '请选择角色';
    if (!form.default_model_id) errs.default_model_id = '请选择默认模型';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const isFormValid = form.name?.trim() && form.role && form.default_model_id;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setApiError(null);
    onSave(isEdit ? form as AgentUpdateData : form);
  };

  const handleChange = (field: string, value: unknown) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  };

  const toggleBackupModel = (modelId: string) => {
    const current = form.backup_model_ids || [];
    if (current.includes(modelId)) {
      handleChange('backup_model_ids', current.filter((id) => id !== modelId));
    } else {
      handleChange('backup_model_ids', [...current, modelId]);
    }
  };

  const toggleTool = (toolId: string) => {
    const current = form.allowed_tools || [];
    if (current.includes(toolId)) {
      handleChange('allowed_tools', current.filter((id) => id !== toolId));
    } else {
      handleChange('allowed_tools', [...current, toolId]);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col h-full">
      <div className="flex items-center justify-between px-6 py-4 border-b border-stone-200">
        <h2 className="text-lg font-semibold text-stone-900">
          {isEdit ? '编辑 Agent' : '创建 Agent'}
        </h2>
        <button type="button" onClick={onCancel} className="text-stone-400 hover:text-stone-600">
          <X size={20} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">
        {/* Running Agent Warning */}
        {agent?.status === 'running' && (
          <div className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-lg p-3">
            <AlertTriangle size={16} className="text-amber-600 mt-0.5 shrink-0" />
            <p className="text-sm text-amber-800">
              该 Agent 正在执行任务，配置修改仅对新任务生效。
            </p>
          </div>
        )}

        {/* API Error Banner */}
        {apiError && (
          <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-lg p-3">
            <AlertTriangle size={16} className="text-red-600 mt-0.5 shrink-0" />
            <p className="text-sm text-red-800">{apiError}</p>
          </div>
        )}
        {/* 基本信息 */}
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-stone-400 mb-3">基本信息</h3>
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-stone-600 mb-1">
                名称 <span className="text-red-600">*</span>
              </label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => handleChange('name', e.target.value)}
                className={`w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300 ${
                  errors.name ? 'border-red-500' : 'border-stone-200'
                }`}
                placeholder="输入 Agent 名称"
              />
              {errors.name && <p className="text-xs text-red-600 mt-1">{errors.name}</p>}
            </div>

            <div>
              <label className="block text-xs font-medium text-stone-600 mb-1">
                角色 <span className="text-red-600">*</span>
              </label>
              <select
                value={form.role}
                onChange={(e) => handleChange('role', e.target.value)}
                className={`w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300 ${
                  errors.role ? 'border-red-500' : 'border-stone-200'
                }`}
              >
                <option value="planner">Planner（规划师）</option>
                <option value="coder">Coder（编码师）</option>
                <option value="reviewer">Reviewer（审查员）</option>
                <option value="research">Research（研究员）</option>
                <option value="summarizer">Summarizer（摘要员）</option>
                <option value="supervisor">Supervisor（监督者）</option>
              </select>
              {errors.role && <p className="text-xs text-red-600 mt-1">{errors.role}</p>}
            </div>

            <div>
              <label className="block text-xs font-medium text-stone-600 mb-1">描述</label>
              <textarea
                value={form.description}
                onChange={(e) => handleChange('description', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300"
                rows={2}
                placeholder="描述该 Agent 的职责"
              />
            </div>
          </div>
        </section>

        {/* 模型配置 */}
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-stone-400 mb-3">模型配置</h3>
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-stone-600 mb-1">
                默认模型 <span className="text-red-600">*</span>
              </label>
              <select
                value={form.default_model_id}
                onChange={(e) => handleChange('default_model_id', e.target.value)}
                className={`w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300 ${
                  errors.default_model_id ? 'border-red-500' : 'border-stone-200'
                }`}
              >
                <option value="">请选择模型</option>
                {MOCK_MODELS.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name} ({m.provider})
                  </option>
                ))}
              </select>
              {errors.default_model_id && <p className="text-xs text-red-600 mt-1">{errors.default_model_id}</p>}
            </div>

            <div>
              <label className="block text-xs font-medium text-stone-600 mb-1">备用模型</label>
              <div className="space-y-1">
                {MOCK_MODELS.map((m) => (
                  <label key={m.id} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={(form.backup_model_ids || []).includes(m.id)}
                      onChange={() => toggleBackupModel(m.id)}
                      disabled={form.default_model_id === m.id}
                      className="rounded border-stone-300"
                    />
                    <span className={form.default_model_id === m.id ? 'text-stone-400' : 'text-stone-700'}>
                      {m.name}
                      {form.default_model_id === m.id && '（默认模型）'}
                    </span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* 工具权限 */}
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-stone-400 mb-3">工具权限</h3>
          <div className="space-y-2">
            {MOCK_TOOLS.map((tool) => (
              <label key={tool.id} className="flex items-start gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={(form.allowed_tools || []).includes(tool.id)}
                  onChange={() => toggleTool(tool.id)}
                  className="rounded border-stone-300 mt-0.5"
                />
                <div>
                  <span className="text-stone-700">{tool.name}</span>
                  <span className="text-stone-400 text-xs ml-2">{tool.description}</span>
                  {tool.risk_level === 'high' && (
                    <span className="text-amber-600 text-xs ml-2">⚠️ 高风险</span>
                  )}
                </div>
              </label>
            ))}
          </div>
        </section>

        {/* 系统 Prompt */}
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-stone-400 mb-3">系统 Prompt</h3>
          <textarea
            value={form.system_prompt}
            onChange={(e) => handleChange('system_prompt', e.target.value)}
            className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300"
            rows={6}
            placeholder="输入系统提示词..."
          />
        </section>

        {/* 执行限制 */}
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-stone-400 mb-3">执行限制</h3>
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-stone-600 mb-1">输出格式</label>
              <select
                value={form.output_format}
                onChange={(e) => handleChange('output_format', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300"
              >
                <option value="markdown">Markdown</option>
                <option value="json">JSON</option>
                <option value="code">Code</option>
                <option value="text">Text</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-stone-600 mb-1">最大执行步数</label>
              <input
                type="number"
                min={1}
                max={50}
                value={form.max_steps_per_task}
                onChange={(e) => handleChange('max_steps_per_task', parseInt(e.target.value) || 1)}
                className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300"
              />
            </div>

            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-stone-700">允许 Handoff</label>
              <button
                type="button"
                onClick={() => handleChange('allow_handoff', !form.allow_handoff)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  form.allow_handoff ? 'bg-green-700' : 'bg-stone-300'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    form.allow_handoff ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {form.allow_handoff && (
              <div>
                <label className="block text-xs font-medium text-stone-600 mb-1">
                  Handoff 触发阈值（tokens）
                </label>
                <input
                  type="number"
                  min={1000}
                  max={100000}
                  value={form.handoff_threshold_tokens || ''}
                  onChange={(e) => handleChange('handoff_threshold_tokens', parseInt(e.target.value) || undefined)}
                  className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300"
                  placeholder="建议 1000-100000"
                />
              </div>
            )}
          </div>
        </section>
      </div>

      <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-stone-200 bg-white">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm text-stone-600 hover:text-stone-800"
        >
          取消
        </button>
        <button
          type="submit"
          disabled={isSubmitting || !isFormValid}
          className="px-4 py-2 text-sm bg-stone-800 text-white rounded-lg hover:bg-stone-900 disabled:opacity-50"
        >
          {isSubmitting ? '保存中...' : isEdit ? '保存' : '创建'}
        </button>
      </div>
    </form>
  );
}
