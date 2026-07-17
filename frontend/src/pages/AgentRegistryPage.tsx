import { useState } from 'react';
import { Plus, Search } from 'lucide-react';
import { useAgents, useAgent, useAgentTemplates, useCreateAgent, useUpdateAgent } from '../hooks/useAgents';
import type { AgentListItem, AgentTemplate, AgentCreateData, AgentUpdateData } from '../types/agent';
import AgentList from '../components/AgentList';
import AgentConfigForm from '../components/AgentConfigForm';
import AgentTemplateCards from '../components/AgentTemplateCards';

export default function AgentRegistryPage() {
  const [filters, setFilters] = useState({ search: '', role: '', status: '' });
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [showFormModal, setShowFormModal] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<AgentTemplate | null>(null);
  const [editingAgent, setEditingAgent] = useState<AgentListItem | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const { data: agentsData, isLoading, error } = useAgents(filters);
  const { data: agentDetail } = useAgent(editingAgent?.id || '');
  const { data: templates } = useAgentTemplates();
  const createAgent = useCreateAgent();
  const updateAgent = useUpdateAgent(editingAgent?.id || '');

  const handleCreate = () => {
    setEditingAgent(null);
    setSelectedTemplate(null);
    setFormError(null);
    setShowTemplateModal(true);
  };

  const handleSelectTemplate = (template: AgentTemplate) => {
    setSelectedTemplate(template);
    setShowTemplateModal(false);
    setShowFormModal(true);
  };

  const handleCustomCreate = () => {
    setSelectedTemplate(null);
    setShowTemplateModal(false);
    setShowFormModal(true);
  };

  const handleSelectAgent = (agent: AgentListItem) => {
    setEditingAgent(agent);
    setSelectedTemplate(null);
    setFormError(null);
    setShowFormModal(true);
  };

  const handleSave = (data: AgentCreateData | AgentUpdateData) => {
    setFormError(null);
    if (editingAgent) {
      updateAgent.mutate(data as AgentUpdateData, {
        onSuccess: () => {
          setShowFormModal(false);
          setEditingAgent(null);
        },
        onError: (err: Error) => {
          setFormError(err.message || '保存失败，请重试');
        },
      });
    } else {
      const createData: AgentCreateData = {
        name: (data as AgentCreateData).name || '',
        role: (data as AgentCreateData).role,
        description: (data as AgentCreateData).description,
        default_model_id: (data as AgentCreateData).default_model_id,
        backup_model_ids: (data as AgentCreateData).backup_model_ids,
        allowed_tools: (data as AgentCreateData).allowed_tools,
        system_prompt: (data as AgentCreateData).system_prompt,
        output_format: (data as AgentCreateData).output_format,
        max_steps_per_task: (data as AgentCreateData).max_steps_per_task,
        max_tokens_per_task: (data as AgentCreateData).max_tokens_per_task,
        max_duration_seconds: (data as AgentCreateData).max_duration_seconds,
        max_consecutive_failures: (data as AgentCreateData).max_consecutive_failures,
        allow_handoff: (data as AgentCreateData).allow_handoff,
        handoff_threshold_tokens: (data as AgentCreateData).handoff_threshold_tokens,
      };
      if (selectedTemplate) {
        createData.template_id = selectedTemplate.role;
      }
      createAgent.mutate(createData, {
        onSuccess: () => {
          setShowFormModal(false);
          setSelectedTemplate(null);
        },
        onError: (err: Error) => {
          setFormError(err.message || '创建失败，请重试');
        },
      });
    }
  };

  const handleCancel = () => {
    setShowFormModal(false);
    setShowTemplateModal(false);
    setEditingAgent(null);
    setSelectedTemplate(null);
    setFormError(null);
  };

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-stone-900">Agent Registry</h1>
          <p className="text-sm text-stone-500 mt-0.5">管理系统中的所有 Agent 工位</p>
        </div>
        <button
          onClick={handleCreate}
          className="inline-flex items-center gap-2 px-4 py-2 bg-stone-800 text-white text-sm font-medium rounded-lg hover:bg-stone-900 transition-colors"
        >
          <Plus size={16} />
          创建 Agent
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
            placeholder="搜索 Agent 名称..."
            className="w-full pl-9 pr-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300"
          />
        </div>
        <select
          value={filters.role}
          onChange={(e) => setFilters((prev) => ({ ...prev, role: e.target.value }))}
          className="px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300"
        >
          <option value="">所有角色</option>
          <option value="planner">Planner</option>
          <option value="coder">Coder</option>
          <option value="reviewer">Reviewer</option>
          <option value="research">Research</option>
          <option value="summarizer">Summarizer</option>
          <option value="supervisor">Supervisor</option>
        </select>
        <select
          value={filters.status}
          onChange={(e) => setFilters((prev) => ({ ...prev, status: e.target.value }))}
          className="px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300"
        >
          <option value="">所有状态</option>
          <option value="idle">空闲</option>
          <option value="running">执行中</option>
          <option value="handoff">交接中</option>
          <option value="blocked">阻塞</option>
          <option value="error">错误</option>
        </select>
      </div>

      {/* List */}
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
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 text-sm text-stone-600 hover:text-stone-800"
            >
              重试
            </button>
          </div>
        )}

        {!isLoading && !error && (
          <AgentList
            agents={agentsData?.items || []}
            onSelect={handleSelectAgent}
          />
        )}
      </div>

      {/* Template Modal */}
      {showTemplateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
          <div className="bg-white rounded-xl shadow-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-stone-200">
              <h2 className="text-lg font-semibold text-stone-900">选择 Agent 模板</h2>
              <button onClick={handleCancel} className="text-stone-400 hover:text-stone-600">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6">
              <AgentTemplateCards
                templates={templates || []}
                onSelect={handleSelectTemplate}
                onCustom={handleCustomCreate}
              />
            </div>
          </div>
        </div>
      )}

      {/* Form Modal */}
      {showFormModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
          <div className="bg-white rounded-xl shadow-lg w-full max-w-2xl max-h-[90vh] flex flex-col">
            <AgentConfigForm
              agent={agentDetail}
              initialData={!editingAgent && selectedTemplate ? (selectedTemplate.default_config as Partial<AgentCreateData>) : undefined}
              onSave={handleSave}
              onCancel={handleCancel}
              isSubmitting={createAgent.isPending || updateAgent.isPending}
              error={formError}
            />
          </div>
        </div>
      )}
    </div>
  );
}
