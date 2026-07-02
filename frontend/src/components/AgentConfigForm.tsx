import { useState, useEffect } from 'react';
import { X, AlertTriangle, Loader2, ChevronLeft, Check } from 'lucide-react';
import type { AgentStation, AgentCreateData, AgentUpdateData } from '../types/agent';
import { useModels } from '../hooks/useModels';
import { useTools } from '../hooks/useTools';

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
  const [step, setStep] = useState(1);

  const [form, setForm] = useState<AgentCreateData>(defaultForm);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState<string | null>(error || null);

  const { data: modelsData, isLoading: modelsLoading } = useModels({ is_enabled: true });
  const { data: toolsData, isLoading: toolsLoading } = useTools({ is_enabled: true });

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
    setStep(1);
    setApiError(null);
    setErrors({});
  }, [agent, initialData]);

  useEffect(() => {
    setApiError(error || null);
  }, [error]);

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

  const validateStep1 = (): boolean => {
    const errs: Record<string, string> = {};
    if (!form.name?.trim()) errs.name = 'Agent 名称不能为空';
    if (!form.role) errs.role = '请选择角色';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const validateStep2 = (): boolean => {
    const errs: Record<string, string> = {};
    if (!form.default_model_id) errs.default_model_id = '请选择默认模型';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const canGoNext = () => {
    if (step === 1) return form.name?.trim() && form.role;
    if (step === 2) return !!form.default_model_id;
    return true;
  };

  const handleNext = () => {
    if (step === 1 && !validateStep1()) return;
    if (step === 2 && !validateStep2()) return;
    setStep((s) => Math.min(s + 1, 3));
  };

  const handlePrev = () => {
    setStep((s) => Math.max(s - 1, 1));
  };

  const handleSubmit = () => {
    if (!validateStep1() || !validateStep2()) return;
    setApiError(null);
    onSave(isEdit ? form as AgentUpdateData : form);
  };

  const models = modelsData?.items || [];
  const tools = toolsData?.items || [];

  // Summary helpers
  const selectedModel = models.find((m) => m.id === form.default_model_id);
  const selectedBackupModels = models.filter((m) => form.backup_model_ids?.includes(m.id));
  const selectedTools = tools.filter((t) => form.allowed_tools?.includes(t.name));

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-stone-200">
        <div>
          <h2 className="text-lg font-semibold text-stone-900">
            {isEdit ? '编辑 Agent' : '创建 Agent'}
          </h2>
          <div className="flex items-center gap-2 mt-1">
            {[1, 2, 3].map((s) => (
              <div key={s} className="flex items-center gap-1">
                <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-medium ${
                  s < step ? 'bg-green-600 text-white' :
                  s === step ? 'bg-stone-800 text-white' :
                  'bg-stone-200 text-stone-500'
                }`}>
                  {s < step ? <Check size={12} /> : s}
                </div>
                <span className={`text-xs ${s === step ? 'text-stone-800 font-medium' : 'text-stone-400'}`}>
                  {s === 1 ? '基本信息' : s === 2 ? '模型与工具' : '确认'}
                </span>
                {s < 3 && <div className="w-4 h-px bg-stone-200 mx-1" />}
              </div>
            ))}
          </div>
        </div>
        <button type="button" onClick={onCancel} className="text-stone-400 hover:text-stone-600">
          <X size={20} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
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

        {/* ─── Step 1: 基本信息 ─── */}
        {step === 1 && (
          <div className="space-y-5">
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
          </div>
        )}

        {/* ─── Step 2: 模型与工具 ─── */}
        {step === 2 && (
          <div className="space-y-5">
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
                    {modelsLoading && (
                      <option disabled>加载中...</option>
                    )}
                    {models.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.display_name} ({m.provider})
                      </option>
                    ))}
                  </select>
                  {errors.default_model_id && (
                    <p className="text-xs text-red-600 mt-1">{errors.default_model_id}</p>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-medium text-stone-600 mb-1">备用模型</label>
                  <div className="space-y-1">
                    {modelsLoading && (
                      <div className="flex items-center gap-2 text-sm text-stone-400">
                        <Loader2 size={14} className="animate-spin" /> 加载中...
                      </div>
                    )}
                    {models.map((m) => (
                      <label key={m.id} className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          checked={(form.backup_model_ids || []).includes(m.id)}
                          onChange={() => toggleBackupModel(m.id)}
                          disabled={form.default_model_id === m.id}
                          className="rounded border-stone-300"
                        />
                        <span className={form.default_model_id === m.id ? 'text-stone-400' : 'text-stone-700'}>
                          {m.display_name}
                          {form.default_model_id === m.id && '（默认模型）'}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            </section>

            <section>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-stone-400 mb-3">工具权限</h3>
              {toolsLoading && (
                <div className="text-sm text-stone-400">加载工具列表...</div>
              )}
              {!toolsLoading && tools.length === 0 && (
                <div className="text-sm text-stone-400">暂无可用的工具</div>
              )}
              {!toolsLoading && tools.length > 0 && (
              <div className="space-y-2">
                {tools.map((tool) => (
                  <label key={tool.id} className="flex items-start gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={(form.allowed_tools || []).includes(tool.name)}
                      onChange={() => toggleTool(tool.name)}
                      className="rounded border-stone-300 mt-0.5"
                    />
                    <div>
                      <span className="text-stone-700">{tool.display_name}</span>
                      <span className="text-stone-400 text-xs ml-2">{tool.description}</span>
                      {tool.risk_level === 'high' && (
                        <span className="text-amber-600 text-xs ml-2">高风险</span>
                      )}
                      {tool.risk_level === 'medium' && (
                        <span className="text-amber-500 text-xs ml-2">中风险</span>
                      )}
                    </div>
                  </label>
                ))}
              </div>
              )}
            </section>
          </div>
        )}

        {/* ─── Step 3: 高级配置 + 汇总确认 ─── */}
        {step === 3 && (
          <div className="space-y-5">
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

            {/* Summary Card */}
            <section className="bg-stone-50 border border-stone-200 rounded-xl p-4">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-stone-500 mb-3">配置汇总</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-stone-500">名称</span>
                  <span className="font-medium text-stone-800">{form.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-stone-500">角色</span>
                  <span className="font-medium text-stone-800">{form.role}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-stone-500">默认模型</span>
                  <span className="font-medium text-stone-800">{selectedModel?.display_name || '-'}</span>
                </div>
                {selectedBackupModels.length > 0 && (
                  <div className="flex justify-between">
                    <span className="text-stone-500">备用模型</span>
                    <span className="font-medium text-stone-800">{selectedBackupModels.map((m) => m.display_name).join(', ')}</span>
                  </div>
                )}
                {selectedTools.length > 0 && (
                  <div className="flex justify-between">
                    <span className="text-stone-500">工具权限</span>
                    <span className="font-medium text-stone-800">{selectedTools.map((t) => t.name).join(', ')}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-stone-500">输出格式</span>
                  <span className="font-medium text-stone-800">{form.output_format}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-stone-500">允许 Handoff</span>
                  <span className="font-medium text-stone-800">{form.allow_handoff ? '是' : '否'}</span>
                </div>
              </div>
            </section>
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="flex items-center justify-between px-6 py-4 border-t border-stone-200 bg-white">
        <div>
          {step > 1 && (
            <button
              type="button"
              onClick={handlePrev}
              className="inline-flex items-center gap-1 px-4 py-2 text-sm text-stone-600 hover:text-stone-800"
            >
              <ChevronLeft size={16} />
              上一步
            </button>
          )}
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm text-stone-600 hover:text-stone-800"
          >
            取消
          </button>

          {step < 3 ? (
            <button
              type="button"
              onClick={handleNext}
              disabled={!canGoNext()}
              className="px-4 py-2 text-sm bg-stone-800 text-white rounded-lg hover:bg-stone-900 disabled:opacity-50"
            >
              下一步
            </button>
          ) : (
            <button
              type="button"
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="px-4 py-2 text-sm bg-stone-800 text-white rounded-lg hover:bg-stone-900 disabled:opacity-50 inline-flex items-center gap-2"
            >
              {isSubmitting && <Loader2 size={14} className="animate-spin" />}
              {isEdit ? '保存' : '创建'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
