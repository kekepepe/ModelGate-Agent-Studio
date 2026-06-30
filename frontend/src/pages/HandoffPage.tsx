import { useMemo, useState } from 'react';
import { Plus, RefreshCw, Search } from 'lucide-react';
import { useAgents } from '../hooks/useAgents';
import { useAcceptHandoff, useCreateDemoTask, useHandoff, useHandoffs, useTriggerHandoff, useUpdateHandoffResult } from '../hooks/useHandoffs';
import type { HandoffListItem, HandoffReason, HandoffResult } from '../types/handoff';
import HandoffConfirmModal from '../components/HandoffConfirmModal';
import HandoffDetailDrawer from '../components/HandoffDetailDrawer';
import HandoffList from '../components/HandoffList';

export default function HandoffPage() {
  const [filters, setFilters] = useState({ search: '', reason: '', status: '', page: 1, page_size: 20 });
  const [selectedHandoffId, setSelectedHandoffId] = useState('');
  const [showCreateDemo, setShowCreateDemo] = useState(false);
  const [pendingTask, setPendingTask] = useState<{ taskId: string; fromAgentId: string } | null>(null);
  const [modalError, setModalError] = useState<string | null>(null);

  const { data, isLoading, error, refetch } = useHandoffs(filters);
  const { data: detail, isLoading: detailLoading, error: detailError } = useHandoff(selectedHandoffId);
  const { data: agentsData } = useAgents({ page_size: 100 });
  const createDemoTask = useCreateDemoTask();
  const triggerHandoff = useTriggerHandoff();
  const acceptHandoff = useAcceptHandoff();
  const updateResult = useUpdateHandoffResult();

  const agents = agentsData?.items || [];
  const hasFilters = Boolean(filters.search || filters.reason || filters.status);
  const selectedFromAgentId = pendingTask?.fromAgentId || detail?.from_agent_id;

  const summary = useMemo(() => {
    const items = data?.items || [];
    return {
      total: data?.total || 0,
      active: items.filter((h) => ['requested', 'generating_summary', 'ready', 'accepted'].includes(h.status)).length,
      completed: items.filter((h) => h.status === 'completed').length,
      failed: items.filter((h) => h.status === 'failed').length,
    };
  }, [data]);

  const clearFilters = () => setFilters({ search: '', reason: '', status: '', page: 1, page_size: 20 });

  const handleCreateDemoTask = () => {
    const fromAgent = agents[0];
    const toAgent = agents.find((agent) => agent.id !== fromAgent?.id);
    if (!fromAgent || !toAgent) {
      setModalError('至少需要两个 Agent 才能演示 Handoff');
      return;
    }
    setModalError(null);
    createDemoTask.mutate({
      goal_id: `goal-${Date.now()}`,
      title: 'Demo handoff task',
      description: '这是一个用于演示 Handoff Manager 的任务。',
      assigned_agent_id: fromAgent.id,
      assigned_model_id: fromAgent.default_model_id,
      current_output: '已完成初步分析，接下来需要继续执行实现与复查。',
    }, {
      onSuccess: (task) => {
        setPendingTask({ taskId: task.id, fromAgentId: fromAgent.id });
        setShowCreateDemo(false);
      },
      onError: (err: Error) => setModalError(err.message || '创建演示任务失败'),
    });
  };

  const handleConfirmHandoff = (request: { to_agent_id: string; to_model_id?: string; reason: HandoffReason; reason_description?: string }) => {
    if (!pendingTask) return;
    setModalError(null);
    triggerHandoff.mutate({ taskId: pendingTask.taskId, request }, {
      onSuccess: (result) => {
        setPendingTask(null);
        setSelectedHandoffId(result.handoff_id);
      },
      onError: (err: Error) => setModalError(err.message || '触发交接失败'),
    });
  };

  const handleAccept = () => {
    if (!selectedHandoffId) return;
    acceptHandoff.mutate({ handoffId: selectedHandoffId });
  };

  const handleSaveResult = (result: { result_after_handoff: HandoffResult; result_note?: string }) => {
    if (!selectedHandoffId) return;
    updateResult.mutate({ handoffId: selectedHandoffId, request: { ...result, status: 'completed' } });
  };

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-stone-900">Handoff Manager</h1>
          <p className="text-sm text-stone-500 mt-0.5">追踪任务在 Agent 和模型之间的结构化交接</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => refetch()}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-stone-600 bg-white border border-stone-200 rounded-lg hover:bg-stone-50 transition-colors"
          >
            <RefreshCw size={14} />
            刷新
          </button>
          <button
            onClick={() => setShowCreateDemo(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-stone-800 text-white text-sm font-medium rounded-lg hover:bg-stone-900 transition-colors"
          >
            <Plus size={16} />
            演示交接
          </button>
        </div>
      </div>

      {modalError && !pendingTask && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 text-red-700 px-3 py-2 text-sm">
          {modalError}
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <SummaryCard label="全部" value={summary.total} tone="stone" />
        <SummaryCard label="进行中" value={summary.active} tone="lavender" />
        <SummaryCard label="已完成" value={summary.completed} tone="green" />
        <SummaryCard label="失败" value={summary.failed} tone="red" />
      </div>

      <div className="flex flex-wrap items-center gap-3 mb-4">
        <div className="relative flex-1 min-w-[220px] max-w-sm">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-stone-400" />
          <input
            value={filters.search}
            onChange={(e) => setFilters((prev) => ({ ...prev, search: e.target.value, page: 1 }))}
            placeholder="搜索 Handoff / Goal / Task..."
            className="w-full pl-9 pr-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300 bg-white"
          />
        </div>
        <select
          value={filters.reason}
          onChange={(e) => setFilters((prev) => ({ ...prev, reason: e.target.value, page: 1 }))}
          className="px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300 bg-white"
        >
          <option value="">所有原因</option>
          <option value="quota_exceeded">额度不足</option>
          <option value="error">模型错误</option>
          <option value="quality_issue">质量问题</option>
          <option value="role_mismatch">角色不匹配</option>
          <option value="manual">手动交接</option>
          <option value="context_limit">上下文限制</option>
          <option value="other">其他</option>
        </select>
        <select
          value={filters.status}
          onChange={(e) => setFilters((prev) => ({ ...prev, status: e.target.value, page: 1 }))}
          className="px-3 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-300 bg-white"
        >
          <option value="">所有状态</option>
          <option value="requested">等待处理</option>
          <option value="generating_summary">生成摘要中</option>
          <option value="ready">可接手</option>
          <option value="accepted">已接手</option>
          <option value="completed">已完成</option>
          <option value="failed">失败</option>
        </select>
      </div>

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
            <button onClick={() => refetch()} className="mt-4 px-4 py-2 text-sm text-stone-600 hover:text-stone-800">
              重试
            </button>
          </div>
        )}

        {!isLoading && !error && (
          <HandoffList
            handoffs={data?.items || []}
            onSelect={(handoff: HandoffListItem) => setSelectedHandoffId(handoff.id)}
            onClearFilters={clearFilters}
            hasFilters={hasFilters}
          />
        )}
      </div>

      {data && data.total > data.page_size && (
        <div className="mt-4 flex items-center justify-end gap-2 text-sm text-stone-500">
          <button
            disabled={filters.page <= 1}
            onClick={() => setFilters((prev) => ({ ...prev, page: Math.max(1, prev.page - 1) }))}
            className="px-3 py-1.5 border border-stone-200 rounded-lg bg-white disabled:opacity-50"
          >
            Prev
          </button>
          <span>Page {filters.page}</span>
          <button
            disabled={filters.page * filters.page_size >= data.total}
            onClick={() => setFilters((prev) => ({ ...prev, page: prev.page + 1 }))}
            className="px-3 py-1.5 border border-stone-200 rounded-lg bg-white disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}

      {showCreateDemo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
          <div className="w-full max-w-md rounded-xl bg-white border border-stone-200 shadow-lg">
            <div className="px-5 py-4 border-b border-stone-200">
              <h2 className="text-base font-semibold text-stone-900">创建演示任务</h2>
              <p className="text-sm text-stone-400 mt-1">创建一个最小任务后立即触发 Handoff。</p>
            </div>
            <div className="p-5 text-sm text-stone-600">
              {agents.length < 2 ? '请先在 Agent Registry 中创建至少两个 Agent。' : '将使用前两个可用 Agent 演示交接流程。'}
            </div>
            <div className="px-5 py-4 border-t border-stone-200 flex justify-end gap-2">
              <button onClick={() => setShowCreateDemo(false)} className="px-3 py-2 text-sm text-stone-600">取消</button>
              <button
                onClick={handleCreateDemoTask}
                disabled={createDemoTask.isPending || agents.length < 2}
                className="px-4 py-2 text-sm bg-stone-800 text-white rounded-lg disabled:opacity-50"
              >
                {createDemoTask.isPending ? '创建中...' : '创建并继续'}
              </button>
            </div>
          </div>
        </div>
      )}

      {pendingTask && (
        <HandoffConfirmModal
          taskId={pendingTask.taskId}
          agents={agents}
          fromAgentId={selectedFromAgentId}
          onConfirm={handleConfirmHandoff}
          onCancel={() => setPendingTask(null)}
          isSubmitting={triggerHandoff.isPending}
          error={modalError}
        />
      )}

      {selectedHandoffId && (
        <HandoffDetailDrawer
          handoff={detail}
          isLoading={detailLoading}
          error={detailError as Error | null}
          onClose={() => setSelectedHandoffId('')}
          onAccept={handleAccept}
          onSaveResult={handleSaveResult}
          isAccepting={acceptHandoff.isPending}
          isSavingResult={updateResult.isPending}
        />
      )}
    </div>
  );
}

function SummaryCard({ label, value, tone }: { label: string; value: number; tone: 'stone' | 'lavender' | 'green' | 'red' }) {
  const classes = {
    stone: 'text-stone-700 bg-white border-stone-200',
    lavender: 'text-lavender-800 bg-lavender-50 border-lavender-200',
    green: 'text-green-800 bg-green-50 border-green-200',
    red: 'text-red-800 bg-red-50 border-red-200',
  }[tone];
  return (
    <div className={`rounded-xl border p-5 ${classes}`}>
      <div className="text-xs font-medium opacity-70 mb-2">{label}</div>
      <div className="text-3xl font-bold">{value}</div>
    </div>
  );
}
