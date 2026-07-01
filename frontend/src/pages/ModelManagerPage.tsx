import { useState } from 'react';
import { Plus, Search, X, AlertTriangle, Loader2, Trash2, Edit3, Power, PowerOff } from 'lucide-react';
import { useModels, useCreateModel, useUpdateModel, useDeleteModel, useToggleModel } from '../hooks/useModels';
import type { Model, ModelCreateData, ModelUpdateData } from '../types/model';

const PROVIDER_OPTIONS = [
  'openai', 'anthropic', 'deepseek', 'moonshot', 'google', 'meta', 'mistral', 'custom',
];

const CAPABILITY_OPTIONS = [
  'coding', 'reasoning', 'vision', 'multilingual', 'long_context', 'tool_calling',
  'fast', 'cheap', 'high_quality', 'chat', 'embedding',
];

export default function ModelManagerPage() {
  const [filters, setFilters] = useState({ search: '', provider: '' });
  const [showForm, setShowForm] = useState(false);
  const [editingModel, setEditingModel] = useState<Model | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const { data, isLoading, error } = useModels(filters);
  const createModel = useCreateModel();
  const updateModel = useUpdateModel(editingModel?.id || '');
  const deleteModel = useDeleteModel();
  const toggleModel = useToggleModel();

  const handleAdd = () => {
    setEditingModel(null);
    setFormError(null);
    setShowForm(true);
  };

  const handleEdit = (model: Model) => {
    setEditingModel(model);
    setFormError(null);
    setShowForm(true);
  };

  const handleDelete = (modelId: string) => {
    if (!confirm('确定要删除这个模型吗？')) return;
    deleteModel.mutate(modelId);
  };

  const handleToggle = (modelId: string) => {
    toggleModel.mutate(modelId);
  };

  const handleSave = (data: ModelCreateData | ModelUpdateData) => {
    setFormError(null);
    if (editingModel) {
      updateModel.mutate(data as ModelUpdateData, {
        onSuccess: () => setShowForm(false),
        onError: (err: Error) => setFormError(err.message || '保存失败'),
      });
    } else {
      createModel.mutate(data as ModelCreateData, {
        onSuccess: () => setShowForm(false),
        onError: (err: Error) => setFormError(err.message || '创建失败'),
      });
    }
  };

  const models = data?.items || [];

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-stone-900">Model Manager</h1>
          <p className="text-sm text-stone-500 mt-0.5">管理所有可用模型配置</p>
        </div>
        <button
          onClick={handleAdd}
          className="inline-flex items-center gap-2 px-4 py-2 bg-stone-800 text-white text-sm font-medium rounded-lg hover:bg-stone-900 transition-colors"
        >
          <Plus size={16} />
          添加模型
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <div className="relative flex-1 max-w-sm">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-stone-400" />
          <input
            type="text"
            value={filters.search}
            onChange={(e) => setFilters((prev) => ({ ...prev, search: e.target.value }))}
            placeholder="搜索模型名称..."
            className="w-full pl-9 pr-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300"
          />
        </div>
        <select
          value={filters.provider}
          onChange={(e) => setFilters((prev) => ({ ...prev, provider: e.target.value }))}
          className="px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300"
        >
          <option value="">所有 Provider</option>
          {PROVIDER_OPTIONS.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="bg-white border border-stone-200 rounded-xl overflow-hidden">
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-stone-300 border-t-stone-800 rounded-full animate-spin" />
          </div>
        )}

        {error && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="text-stone-400 mb-2">加载失败</div>
            <p className="text-sm text-stone-500">{(error as Error).message}</p>
          </div>
        )}

        {!isLoading && !error && models.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="text-stone-400 mb-2">暂无模型</div>
            <p className="text-sm text-stone-500">点击右上角"添加模型"创建第一个模型</p>
          </div>
        )}

        {!isLoading && !error && models.length > 0 && (
          <table className="w-full text-sm">
            <thead className="bg-stone-50 border-b border-stone-200">
              <tr>
                <th className="text-left px-4 py-3 font-medium text-stone-600">模型</th>
                <th className="text-left px-4 py-3 font-medium text-stone-600">Provider</th>
                <th className="text-left px-4 py-3 font-medium text-stone-600">Cost</th>
                <th className="text-left px-4 py-3 font-medium text-stone-600">Speed</th>
                <th className="text-left px-4 py-3 font-medium text-stone-600">Context</th>
                <th className="text-left px-4 py-3 font-medium text-stone-600">Tags</th>
                <th className="text-left px-4 py-3 font-medium text-stone-600">状态</th>
                <th className="text-right px-4 py-3 font-medium text-stone-600">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100">
              {models.map((model) => (
                <tr key={model.id} className="hover:bg-stone-50/50">
                  <td className="px-4 py-3">
                    <div className="font-medium text-stone-900">{model.display_name}</div>
                    <div className="text-xs text-stone-400">{model.model_name}</div>
                  </td>
                  <td className="px-4 py-3 text-stone-600">{model.provider}</td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-stone-100 text-stone-700">
                      {'$'.repeat(model.cost_level)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-stone-100 text-stone-700">
                      {'⚡'.repeat(model.speed_level)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-stone-600">
                    {(model.max_context_tokens / 1000).toFixed(0)}K
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {model.capability_tags.slice(0, 3).map((tag) => (
                        <span key={tag} className="px-1.5 py-0.5 rounded text-xs bg-lavender-50 text-lavender-700 border border-lavender-100">
                          {tag}
                        </span>
                      ))}
                      {model.capability_tags.length > 3 && (
                        <span className="px-1.5 py-0.5 rounded text-xs text-stone-400">+{model.capability_tags.length - 3}</span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handleToggle(model.id)}
                      className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors ${
                        model.is_enabled
                          ? 'bg-green-50 text-green-700 border border-green-200'
                          : 'bg-stone-100 text-stone-500 border border-stone-200'
                      }`}
                    >
                      {model.is_enabled ? <Power size={12} /> : <PowerOff size={12} />}
                      {model.is_enabled ? '启用' : '禁用'}
                    </button>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => handleEdit(model)}
                        className="p-1.5 text-stone-400 hover:text-stone-700 hover:bg-stone-100 rounded transition-colors"
                        title="编辑"
                      >
                        <Edit3 size={14} />
                      </button>
                      <button
                        onClick={() => handleDelete(model.id)}
                        className="p-1.5 text-stone-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                        title="删除"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Form Modal */}
      {showForm && (
        <ModelFormModal
          model={editingModel}
          onSave={handleSave}
          onCancel={() => setShowForm(false)}
          isSubmitting={createModel.isPending || updateModel.isPending}
          error={formError}
        />
      )}
    </div>
  );
}

/* ─── Model Form Modal ─── */

interface ModelFormModalProps {
  model?: Model | null;
  onSave: (data: ModelCreateData | ModelUpdateData) => void;
  onCancel: () => void;
  isSubmitting?: boolean;
  error?: string | null;
}

function ModelFormModal({ model, onSave, onCancel, isSubmitting, error }: ModelFormModalProps) {
  const isEdit = !!model;
  const [form, setForm] = useState<ModelCreateData>({
    provider: model?.provider || 'openai',
    model_name: model?.model_name || '',
    display_name: model?.display_name || '',
    capability_tags: model?.capability_tags || [],
    max_context_tokens: model?.max_context_tokens || 8192,
    cost_level: model?.cost_level || 3,
    speed_level: model?.speed_level || 3,
    is_enabled: model?.is_enabled ?? true,
    is_default: model?.is_default ?? false,
  });

  const handleChange = (field: keyof ModelCreateData, value: unknown) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const toggleTag = (tag: string) => {
    const current = form.capability_tags || [];
    if (current.includes(tag)) {
      handleChange('capability_tags', current.filter((t) => t !== tag));
    } else {
      handleChange('capability_tags', [...current, tag]);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(isEdit ? { ...form } : form);
  };

  const isValid = form.provider && form.model_name.trim() && form.display_name.trim();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-lg max-h-[90vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-stone-200">
          <h2 className="text-lg font-semibold text-stone-900">
            {isEdit ? '编辑模型' : '添加模型'}
          </h2>
          <button onClick={onCancel} className="text-stone-400 hover:text-stone-600">
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto px-6 py-5 space-y-5">
          {error && (
            <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-lg p-3">
              <AlertTriangle size={16} className="text-red-600 mt-0.5 shrink-0" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-stone-600 mb-1">Provider *</label>
              <select
                value={form.provider}
                onChange={(e) => handleChange('provider', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300"
              >
                {PROVIDER_OPTIONS.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-stone-600 mb-1">模型名称 *</label>
              <input
                type="text"
                value={form.model_name}
                onChange={(e) => handleChange('model_name', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300"
                placeholder="如 gpt-4-turbo"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-stone-600 mb-1">显示名称 *</label>
            <input
              type="text"
              value={form.display_name}
              onChange={(e) => handleChange('display_name', e.target.value)}
              className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300"
              placeholder="如 GPT-4 Turbo"
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-stone-600 mb-1">Cost Level (1-5)</label>
              <input
                type="number"
                min={1}
                max={5}
                value={form.cost_level}
                onChange={(e) => handleChange('cost_level', parseInt(e.target.value) || 3)}
                className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-stone-600 mb-1">Speed Level (1-5)</label>
              <input
                type="number"
                min={1}
                max={5}
                value={form.speed_level}
                onChange={(e) => handleChange('speed_level', parseInt(e.target.value) || 3)}
                className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-stone-600 mb-1">Max Tokens</label>
              <input
                type="number"
                min={1}
                value={form.max_context_tokens}
                onChange={(e) => handleChange('max_context_tokens', parseInt(e.target.value) || 8192)}
                className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-stone-600 mb-2">能力标签</label>
            <div className="flex flex-wrap gap-2">
              {CAPABILITY_OPTIONS.map((tag) => (
                <button
                  key={tag}
                  type="button"
                  onClick={() => toggleTag(tag)}
                  className={`px-2.5 py-1 rounded text-xs border transition-colors ${
                    (form.capability_tags || []).includes(tag)
                      ? 'bg-lavender-50 text-lavender-700 border-lavender-300'
                      : 'bg-white text-stone-500 border-stone-200 hover:border-stone-300'
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-6">
            <label className="flex items-center gap-2 text-sm text-stone-600 cursor-pointer">
              <input
                type="checkbox"
                checked={form.is_enabled}
                onChange={(e) => handleChange('is_enabled', e.target.checked)}
                className="rounded border-stone-300 text-lavender-600"
              />
              启用
            </label>
            <label className="flex items-center gap-2 text-sm text-stone-600 cursor-pointer">
              <input
                type="checkbox"
                checked={form.is_default}
                onChange={(e) => handleChange('is_default', e.target.checked)}
                className="rounded border-stone-300 text-lavender-600"
              />
              设为默认
            </label>
          </div>
        </form>

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
            disabled={isSubmitting || !isValid}
            onClick={handleSubmit}
            className="px-4 py-2 text-sm bg-stone-800 text-white rounded-lg hover:bg-stone-900 disabled:opacity-50 inline-flex items-center gap-2"
          >
            {isSubmitting && <Loader2 size={14} className="animate-spin" />}
            {isEdit ? '保存' : '创建'}
          </button>
        </div>
      </div>
    </div>
  );
}
