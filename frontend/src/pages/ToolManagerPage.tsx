import { useState } from 'react';
import { Plus, X, AlertTriangle, Loader2, Trash2, Edit3, Power, PowerOff, Wrench } from 'lucide-react';
import { useTools, useCreateTool, useUpdateTool, useDeleteTool, useToggleTool } from '../hooks/useTools';
import type { ToolDefinition, ToolCreateData, ToolUpdateData } from '../types/tool';

const CATEGORY_OPTIONS = ['文件操作', '终端', '网络', '代码', '测试', '其他'];
const RISK_LEVELS = ['low', 'medium', 'high'] as const;

const RISK_CONFIG: Record<string, { label: string; color: string }> = {
  low: { label: '低风险', color: 'text-green-700 bg-green-100' },
  medium: { label: '中风险', color: 'text-amber-700 bg-amber-100' },
  high: { label: '高风险', color: 'text-red-700 bg-red-100' },
};

interface ToolFormProps {
  tool: ToolDefinition | null;
  onSave: (data: ToolCreateData | ToolUpdateData) => void;
  onCancel: () => void;
  isSubmitting: boolean;
  error: string | null;
}

function ToolForm({ tool, onSave, onCancel, isSubmitting, error }: ToolFormProps) {
  const isEdit = !!tool;
  const [name, setName] = useState(tool?.name || '');
  const [displayName, setDisplayName] = useState(tool?.display_name || '');
  const [description, setDescription] = useState(tool?.description || '');
  const [category, setCategory] = useState(tool?.category || '文件操作');
  const [riskLevel, setRiskLevel] = useState<'low' | 'medium' | 'high'>(tool?.risk_level || 'low');
  const [paramsJson, setParamsJson] = useState(
    tool ? JSON.stringify(tool.parameters, null, 2) : '{\n  \n}'
  );
  const [paramsError, setParamsError] = useState<string | null>(null);

  const handleSubmit = () => {
    let parameters;
    try {
      parameters = JSON.parse(paramsJson);
    } catch {
      setParamsError('Parameters 必须是合法 JSON');
      return;
    }
    setParamsError(null);
    const data: ToolCreateData = {
      name,
      display_name: displayName,
      description,
      category,
      risk_level: riskLevel,
      parameters,
    };
    onSave(data);
  };

  return (
    <div className="fixed inset-0 bg-black/20 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-6 py-4 border-b border-stone-200">
          <h2 className="text-lg font-semibold text-stone-900">
            {isEdit ? '编辑工具' : '注册工具'}
          </h2>
          <button onClick={onCancel} className="text-stone-400 hover:text-stone-600">
            <X size={20} />
          </button>
        </div>
        <div className="px-6 py-4 space-y-4">
          {error && (
            <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-lg p-3">
              <AlertTriangle size={16} className="text-red-600 mt-0.5 shrink-0" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}
          {paramsError && (
            <div className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-lg p-3">
              <AlertTriangle size={16} className="text-amber-600 mt-0.5 shrink-0" />
              <p className="text-sm text-amber-800">{paramsError}</p>
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-stone-600 mb-1">
              Name <span className="text-red-600">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={isEdit}
              className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300 disabled:bg-stone-100"
              placeholder="snake_case 格式，如 file_write"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-stone-600 mb-1">
              显示名称 <span className="text-red-600">*</span>
            </label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-stone-600 mb-1">描述</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-stone-600 mb-1">分类</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300"
              >
                {CATEGORY_OPTIONS.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-stone-600 mb-1">风险级别</label>
              <select
                value={riskLevel}
                onChange={(e) => setRiskLevel(e.target.value as 'low' | 'medium' | 'high')}
                className="w-full px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300"
              >
                {RISK_LEVELS.map((r) => (
                  <option key={r} value={r}>{RISK_CONFIG[r].label}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-stone-600 mb-1">
              Parameters (JSON Schema) <span className="text-red-600">*</span>
            </label>
            <textarea
              value={paramsJson}
              onChange={(e) => setParamsJson(e.target.value)}
              className="w-full px-3 py-2 text-sm font-mono border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300"
              rows={6}
            />
          </div>
        </div>

        <div className="flex justify-end gap-3 px-6 py-4 border-t border-stone-200">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-stone-600 hover:text-stone-900"
          >
            取消
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || !name || !displayName}
            className="inline-flex items-center gap-2 px-4 py-2 bg-stone-800 text-white text-sm font-medium rounded-lg hover:bg-stone-900 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting && <Loader2 size={14} className="animate-spin" />}
            {isEdit ? '保存' : '注册'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function ToolManagerPage() {
  const [filters, setFilters] = useState({ category: '', risk_level: '' });
  const [showForm, setShowForm] = useState(false);
  const [editingTool, setEditingTool] = useState<ToolDefinition | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const { data, isLoading, error } = useTools({
    ...filters,
    is_enabled: undefined,
  });
  const createTool = useCreateTool();
  const updateTool = useUpdateTool(editingTool?.id || '');
  const deleteTool = useDeleteTool();
  const toggleTool = useToggleTool();

  const handleAdd = () => {
    setEditingTool(null);
    setFormError(null);
    setShowForm(true);
  };

  const handleEdit = (tool: ToolDefinition) => {
    setEditingTool(tool);
    setFormError(null);
    setShowForm(true);
  };

  const handleDelete = (toolId: string) => {
    if (!confirm('确定要删除这个工具吗？')) return;
    deleteTool.mutate(toolId);
  };

  const handleToggle = (toolId: string) => {
    toggleTool.mutate(toolId);
  };

  const handleSave = (toolData: ToolCreateData | ToolUpdateData) => {
    setFormError(null);
    if (editingTool) {
      updateTool.mutate(toolData as ToolUpdateData, {
        onSuccess: () => setShowForm(false),
        onError: (err: Error) => setFormError(err.message || '保存失败'),
      });
    } else {
      createTool.mutate(toolData as ToolCreateData, {
        onSuccess: () => setShowForm(false),
        onError: (err: Error) => setFormError(err.message || '创建失败'),
      });
    }
  };

  const tools = data?.items || [];

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-stone-900">Tool Manager</h1>
          <p className="text-sm text-stone-500 mt-0.5">管理可用工具定义</p>
        </div>
        <button
          onClick={handleAdd}
          className="inline-flex items-center gap-2 px-4 py-2 bg-stone-800 text-white text-sm font-medium rounded-lg hover:bg-stone-900 transition-colors"
        >
          <Plus size={16} />
          注册工具
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <select
          value={filters.category}
          onChange={(e) => setFilters((prev) => ({ ...prev, category: e.target.value }))}
          className="px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300"
        >
          <option value="">所有分类</option>
          {CATEGORY_OPTIONS.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <select
          value={filters.risk_level}
          onChange={(e) => setFilters((prev) => ({ ...prev, risk_level: e.target.value }))}
          className="px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300"
        >
          <option value="">所有风险级别</option>
          {RISK_LEVELS.map((r) => (
            <option key={r} value={r}>{RISK_CONFIG[r].label}</option>
          ))}
        </select>
      </div>

      {/* Error State */}
      {error && (
        <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <AlertTriangle size={16} className="text-red-600 mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-medium text-red-800">加载失败</p>
            <p className="text-xs text-red-600 mt-1">{(error as Error).message || '未知错误'}</p>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={24} className="animate-spin text-stone-400" />
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && tools.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-stone-400">
          <Wrench size={48} className="mb-4" />
          <p className="text-sm font-medium">暂无注册工具</p>
          <p className="text-xs mt-1">点击"注册工具"添加第一个工具</p>
        </div>
      )}

      {/* Table */}
      {!isLoading && !error && tools.length > 0 && (
        <div className="bg-white border border-stone-200 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-stone-100 bg-stone-50/50">
                <th className="text-left px-4 py-3 text-xs font-medium text-stone-500 uppercase tracking-wide">Name</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-stone-500 uppercase tracking-wide">显示名称</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-stone-500 uppercase tracking-wide">分类</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-stone-500 uppercase tracking-wide">风险</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-stone-500 uppercase tracking-wide">状态</th>
                <th className="text-right px-4 py-3 text-xs font-medium text-stone-500 uppercase tracking-wide">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100">
              {tools.map((tool) => (
                <tr key={tool.id} className="hover:bg-stone-50/50">
                  <td className="px-4 py-3">
                    <span className="text-sm font-mono text-stone-800">{tool.name}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-stone-700">{tool.display_name}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-stone-500">{tool.category}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${RISK_CONFIG[tool.risk_level]?.color || ''}`}>
                      {RISK_CONFIG[tool.risk_level]?.label || tool.risk_level}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1 text-xs ${tool.is_enabled ? 'text-green-700' : 'text-stone-400'}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${tool.is_enabled ? 'bg-green-500' : 'bg-stone-400'}`} />
                      {tool.is_enabled ? '启用' : '禁用'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => handleToggle(tool.id)}
                        className="p-1.5 rounded hover:bg-stone-100 text-stone-400 hover:text-stone-600"
                        title={tool.is_enabled ? '禁用' : '启用'}
                      >
                        {tool.is_enabled ? <PowerOff size={14} /> : <Power size={14} />}
                      </button>
                      <button
                        onClick={() => handleEdit(tool)}
                        className="p-1.5 rounded hover:bg-stone-100 text-stone-400 hover:text-stone-600"
                        title="编辑"
                      >
                        <Edit3 size={14} />
                      </button>
                      <button
                        onClick={() => handleDelete(tool.id)}
                        className="p-1.5 rounded hover:bg-stone-100 text-stone-400 hover:text-red-600"
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
        </div>
      )}

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between mt-4 text-sm text-stone-500">
          <span>共 {data.total} 个工具</span>
          <span>第 {data.page} / {data.total_pages} 页</span>
        </div>
      )}

      {/* Add/Edit Form Modal */}
      {showForm && (
        <ToolForm
          tool={editingTool}
          onSave={handleSave}
          onCancel={() => setShowForm(false)}
          isSubmitting={createTool.isPending || updateTool.isPending}
          error={formError}
        />
      )}
    </div>
  );
}
