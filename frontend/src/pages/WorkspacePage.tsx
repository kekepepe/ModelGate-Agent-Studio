import { useState, useCallback } from 'react';
import { useWorkspaceState, useTaskDetail, useExecuteGoal, useRuntimeStatus } from '../hooks/useWorkspace';
import { useAgents } from '../hooks/useAgents';
import { useAcceptHandoff, useHandoff, useTriggerHandoff, useUpdateHandoffResult } from '../hooks/useHandoffs';
import TopStatusBar from '../components/TopStatusBar';
import GoalInputPanel from '../components/GoalInputPanel';
import TaskCard from '../components/TaskCard';
import TaskFlow from '../components/TaskFlow';
import TaskTree from '../components/TaskTree';
import TaskDetailPanel from '../components/TaskDetailPanel';
import BottomConsole from '../components/BottomConsole';
import FinalOutputPanel from '../components/FinalOutputPanel';
import HandoffConfirmModal from '../components/HandoffConfirmModal';
import HandoffDetailDrawer from '../components/HandoffDetailDrawer';
import type { WorkspaceTask, WorkspaceWorker } from '../types/workspace';
import type { HandoffReason, HandoffResult } from '../types/handoff';

export default function WorkspacePage() {
  const [goalId, setGoalId] = useState<string | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

  const { data: state, isLoading } = useWorkspaceState(goalId);
  const { data: taskDetail, isLoading: isTaskLoading } = useTaskDetail(selectedTaskId);
  const { data: runtimeStatus } = useRuntimeStatus(goalId);
  const { data: agentsData } = useAgents({ page_size: 100 });
  const executeGoal = useExecuteGoal();
  const triggerHandoff = useTriggerHandoff();
  const acceptHandoff = useAcceptHandoff();
  const updateHandoffResult = useUpdateHandoffResult();
  const [handoffTaskId, setHandoffTaskId] = useState<string | null>(null);
  const [selectedHandoffId, setSelectedHandoffId] = useState<string>('');
  const [handoffError, setHandoffError] = useState<string | null>(null);
  const { data: selectedHandoff, isLoading: isHandoffLoading, error: selectedHandoffError } = useHandoff(selectedHandoffId);

  const handleGoalCreated = useCallback((newGoalId: string) => {
    setGoalId(newGoalId);
  }, []);

  // Group workers by agent_id for quick lookup
  const workerMap = new Map<string, WorkspaceWorker>();
  state?.workers?.forEach((w) => {
    if (w.agent_id && (!workerMap.has(w.agent_id) || w.status === 'running')) {
      workerMap.set(w.agent_id, w);
    }
  });

  const agents = agentsData?.items || [];
  const activeHandoffTask = handoffTaskId ? state?.tasks.find((task) => task.id === handoffTaskId) : null;
  const handleConfirmHandoff = (request: { to_agent_id: string; to_model_id?: string; reason: HandoffReason; reason_description?: string }) => {
    if (!handoffTaskId) return;
    setHandoffError(null);
    triggerHandoff.mutate({ taskId: handoffTaskId, request }, {
      onSuccess: (result) => {
        setHandoffTaskId(null);
        setSelectedHandoffId(result.handoff_id);
      },
      onError: (error: Error) => setHandoffError(error.message || '触发交接失败'),
    });
  };

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <TopStatusBar goal={state?.goal || null} tasks={state?.tasks || []} />

      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel */}
        <aside className="w-[280px] border-r border-stone-200 bg-white flex flex-col flex-shrink-0 overflow-y-auto">
          <GoalInputPanel
            onGoalCreated={handleGoalCreated}
            activeGoalId={goalId}
            goalTitle={state?.goal?.title || null}
          />
          <TaskTree
            tasks={state?.tasks || []}
            onTaskClick={setSelectedTaskId}
            selectedTaskId={selectedTaskId}
          />
        </aside>

        {/* Center - Agent Station Board */}
        <main className="flex-1 overflow-y-auto bg-stone-50 p-4">
          {!goalId && (
            <div className="flex items-center justify-center h-full text-stone-400 text-sm">
              在左侧输入 Goal 并点击 [开始] 以启动工作区
            </div>
          )}

          {goalId && isLoading && (
            <div className="space-y-4">
              <div className="h-40 bg-stone-200 rounded-xl animate-pulse" />
              <div className="h-40 bg-stone-200 rounded-xl animate-pulse" />
            </div>
          )}

          {goalId && state && (
            <div className="space-y-4">
              {/* Goal progress and primary execution action */}
              <div className="flex items-center gap-3">
                <div className="grid grid-cols-4 gap-3 flex-1">
                  <StatCard label="总 Task" value={state.tasks.length.toString()} />
                  <StatCard label="运行中" value={state.tasks.filter((t) => t.status === 'running').length.toString()} color="text-blue-600" />
                  <StatCard label="已完成" value={state.tasks.filter((t) => t.status === 'completed').length.toString()} color="text-green-600" />
                  <StatCard label="交接中" value={state.tasks.filter((t) => t.status === 'handoff').length.toString()} color="text-purple-600" />
                </div>
                {state.goal && ['planning', 'running'].includes(state.goal.status) && (
                  <button
                    onClick={() => executeGoal.mutate(goalId!)}
                    disabled={executeGoal.isPending}
                    className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-40 flex-shrink-0"
                  >
                    {executeGoal.isPending ? '执行中...' : '▶ 执行'}
                  </button>
                )}
              </div>

              {/* Final output when goal completed */}
              {runtimeStatus && ['completed', 'failed', 'handoff'].includes(runtimeStatus.goal_status) && (
                <FinalOutputPanel
                  output={runtimeStatus.final_output}
                  status={runtimeStatus.goal_status}
                  tasksCompleted={runtimeStatus.completed_tasks}
                  tasksFailed={runtimeStatus.failed_tasks}
                  tasksHandoff={runtimeStatus.handoff_tasks}
                  totalTokens={runtimeStatus.total_tokens_used}
                  logCount={runtimeStatus.log_count}
                  finalSummary={runtimeStatus.final_summary}
                />
              )}

              {/* The centre remains a task flow; Handoff is handled on the relevant task. */}
              {state.tasks.length > 0 && (
                <TaskFlow taskCount={state.tasks.length} handoffCount={state.handoffs?.length || 0}>
                    {state.tasks.map((task) => (
                      <TaskCard
                        key={task.id}
                        id={task.id}
                        title={task.title}
                        status={task.status as any}
                        priority={task.priority}
                        tokensUsed={task.tokens_used}
                        isSelected={selectedTaskId === task.id}
                        onSelect={setSelectedTaskId}
                        agentName={state.agents.find((agent) => agent.id === task.assigned_agent_id)?.name || task.agent_name}
                        modelName={workerMap.get(task.assigned_agent_id || '')?.model_name || task.model_name}
                        outputSnippet={task.output}
                        handoff={task.handoff}
                        onRequestHandoff={setHandoffTaskId}
                        onOpenHandoff={setSelectedHandoffId}
                        quotaStatus={task.quota?.quota_status}
                        quotaUsagePercent={task.quota?.usage_percent}
                      />
                    ))}
                </TaskFlow>
              )}
            </div>
          )}
        </main>

        {/* Right Panel - Task Detail */}
        <div
          className={`${selectedTaskId ? 'w-[360px]' : 'w-0'} flex-shrink-0 transition-all duration-300 overflow-hidden border-l border-stone-200`}
        >
          {selectedTaskId && (
            <TaskDetailPanel
              task={mergeTaskDetail(taskDetail || null, state?.tasks.find((task) => task.id === selectedTaskId) || null)}
              isLoading={isTaskLoading}
              onClose={() => setSelectedTaskId(null)}
              handoffs={state?.tasks.find((task) => task.id === selectedTaskId)?.handoffs || []}
              onOpenHandoff={setSelectedHandoffId}
            />
          )}
        </div>
      </div>

      <BottomConsole goalId={goalId} />

      {activeHandoffTask && (
        <HandoffConfirmModal
          taskId={activeHandoffTask.id}
          agents={agents}
          fromAgentId={activeHandoffTask.assigned_agent_id || undefined}
          onConfirm={handleConfirmHandoff}
          onCancel={() => { setHandoffTaskId(null); setHandoffError(null); }}
          isSubmitting={triggerHandoff.isPending}
          error={handoffError}
        />
      )}

      {selectedHandoffId && (
        <HandoffDetailDrawer
          handoff={selectedHandoff}
          isLoading={isHandoffLoading}
          error={selectedHandoffError as Error | null}
          onClose={() => setSelectedHandoffId('')}
          onAccept={() => acceptHandoff.mutate({ handoffId: selectedHandoffId })}
          onSaveResult={(result: { result_after_handoff: HandoffResult; result_note?: string }) =>
            updateHandoffResult.mutate({ handoffId: selectedHandoffId, request: { ...result, status: 'completed' } })
          }
          isAccepting={acceptHandoff.isPending}
          isSavingResult={updateHandoffResult.isPending}
        />
      )}
    </div>
  );
}

function mergeTaskDetail(
  taskDetail: WorkspaceTask | null,
  workspaceTask: WorkspaceTask | null,
) {
  if (!taskDetail) return workspaceTask;
  if (!workspaceTask) return taskDetail;
  // The aggregate state carries router/quota/log/context data while the detail
  // endpoint contributes the latest relational labels. Keep both in one panel.
  return { ...taskDetail, ...workspaceTask };
}

function StatCard({ label, value, color = 'text-stone-800' }: { label: string; value: string; color?: string }) {
  return (
    <div className="bg-white rounded-lg border border-stone-200 p-3 text-center">
      <div className="text-[10px] text-stone-400 uppercase tracking-wide">{label}</div>
      <div className={`text-lg font-semibold ${color} mt-0.5`}>{value}</div>
    </div>
  );
}
