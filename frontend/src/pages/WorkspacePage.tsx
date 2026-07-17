import { lazy, Suspense, useCallback, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useWorkspaceState, useTaskDetail, useExecuteGoal, useRuntimeStatus, usePauseGoal, useResumeGoal, useRuntimeEvents, useStopGoal, useRetryTask } from '../hooks/useWorkspace';
import { useAgents } from '../hooks/useAgents';
import { useAcceptHandoff, useHandoff, useTriggerHandoff, useUpdateHandoffResult } from '../hooks/useHandoffs';
import TopStatusBar from '../components/TopStatusBar';
import GoalInputPanel from '../components/GoalInputPanel';
import TaskTree from '../components/TaskTree';
import AgentDetailModal from '../components/AgentDetailModal';
import CardFlowRenderer from '../components/CardFlowRenderer';
import BottomConsole from '../components/BottomConsole';
import FinalOutputPanel from '../components/FinalOutputPanel';
import HandoffConfirmModal from '../components/HandoffConfirmModal';
import HandoffDetailDrawer from '../components/HandoffDetailDrawer';
import type { WorkspaceTask } from '../types/workspace';
import type { HandoffReason, HandoffResult } from '../types/handoff';
import { getTeamPreset } from '../types/team';
import { buildWorkspaceViewModel, type WorkspaceViewMode } from '../utils/workspaceViewModel';

const PixelOfficeRenderer = lazy(() => import('../components/PixelOfficeRenderer'));

export default function WorkspacePage() {
  const [searchParams] = useSearchParams();
  const teamPreset = getTeamPreset(searchParams.get('team'));
  const [goalId, setGoalId] = useState<string | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<WorkspaceViewMode>(() => window.localStorage.getItem('modelgate-workspace-view') === 'pixel' ? 'pixel' : 'card');

  const { data: state, isLoading } = useWorkspaceState(goalId);
  const { data: taskDetail, isLoading: isTaskLoading } = useTaskDetail(selectedTaskId);
  const { data: runtimeStatus } = useRuntimeStatus(goalId);
  useRuntimeEvents(goalId);
  const { data: agentsData } = useAgents({ page_size: 100 });
  const executeGoal = useExecuteGoal();
  const pauseGoal = usePauseGoal();
  const resumeGoal = useResumeGoal();
  const stopGoal = useStopGoal();
  const retryTask = useRetryTask();
  const triggerHandoff = useTriggerHandoff();
  const acceptHandoff = useAcceptHandoff();
  const updateHandoffResult = useUpdateHandoffResult();
  const [handoffTaskId, setHandoffTaskId] = useState<string | null>(null);
  const [selectedHandoffId, setSelectedHandoffId] = useState<string>('');
  const [handoffError, setHandoffError] = useState<string | null>(null);
  const { data: selectedHandoff, isLoading: isHandoffLoading, error: selectedHandoffError } = useHandoff(selectedHandoffId);

  const viewModel = useMemo(
    () => state ? buildWorkspaceViewModel(state, teamPreset) : { stations: [], edges: [], handoffs: [] },
    [state, teamPreset],
  );

  const handleGoalCreated = useCallback((newGoalId: string) => {
    setGoalId(newGoalId);
  }, []);

  const agents = agentsData?.items || [];
  const taskOutputs = (state?.tasks || [])
    .filter((task) => Boolean(task.output))
    .map((task) => ({ id: task.id, title: task.title, output: task.output! }));
  const latestTaskOutput = taskOutputs.at(-1)?.output || null;
  const activeHandoffTask = handoffTaskId ? state?.tasks.find((task) => task.id === handoffTaskId) : null;
  const selectedTask = mergeTaskDetail(taskDetail || null, state?.tasks.find((task) => task.id === selectedTaskId) || null);
  const handleModeChange = (mode: WorkspaceViewMode) => {
    setViewMode(mode);
    window.localStorage.setItem('modelgate-workspace-view', mode);
  };
  const handleExport = () => {
    if (!state?.goal) return;
    const payload = JSON.stringify({ goal: state.goal, team: teamPreset.name, tasks: state.tasks, handoffs: state.handoffs }, null, 2);
    const url = URL.createObjectURL(new Blob([payload], { type: 'application/json' }));
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `modelgate-${state.goal.id}-summary.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };
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
      <TopStatusBar
        goal={state?.goal || null}
        tasks={state?.tasks || []}
        teamName={teamPreset.name}
        mode={viewMode}
        onModeChange={handleModeChange}
        onExecute={goalId ? () => executeGoal.mutate(goalId) : undefined}
        onPause={goalId ? () => pauseGoal.mutate(goalId) : undefined}
        onResume={goalId ? () => resumeGoal.mutate(goalId) : undefined}
        onStop={goalId && !['completed', 'failed', 'cancelled'].includes(state?.goal?.status || '') ? () => stopGoal.mutate(goalId) : undefined}
        onExport={handleExport}
        isBusy={executeGoal.isPending || pauseGoal.isPending || resumeGoal.isPending || stopGoal.isPending}
      />

      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel */}
        <aside className="w-[280px] border-r border-stone-200 bg-white flex flex-col flex-shrink-0 overflow-y-auto">
          <GoalInputPanel
            onGoalCreated={handleGoalCreated}
            activeGoalId={goalId}
            goalTitle={state?.goal?.title || null}
            preset={teamPreset}
          />
          <TaskTree
            tasks={state?.tasks || []}
            onTaskClick={setSelectedTaskId}
            selectedTaskId={selectedTaskId}
          />
        </aside>

        {/* Center - two renderers consume the same Workspace state. */}
        <main className="flex-1 overflow-y-auto bg-stone-50 p-4">
          {!goalId && (
            <div className="flex min-h-full flex-col">
              <div className="mb-3 flex items-center justify-between rounded-xl border border-stone-200 bg-white px-4 py-3">
                <div><p className="text-xs font-semibold text-stone-800">{teamPreset.name}</p><p className="mt-0.5 text-[11px] text-stone-500">{teamPreset.roles.map((role) => role.label).join(' → ')}</p></div>
                <div className="text-[11px] text-stone-400">启动后可在 Card Flow / Pixel Office 间切换</div>
              </div>
              <div className="flex flex-1 items-center justify-center rounded-xl border border-dashed border-stone-300 bg-white text-sm text-stone-400">
                在左侧确认 Goal 与完成标准，然后点击“创建并规划”启动工作区。
              </div>
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
              {/* Final output when goal completed */}
              {(taskOutputs.length > 0 || (runtimeStatus && ['completed', 'failed', 'handoff', 'cancelled'].includes(runtimeStatus.goal_status))) && (
                <FinalOutputPanel
                  output={runtimeStatus?.final_output || latestTaskOutput}
                  status={runtimeStatus?.goal_status || state.goal?.status || 'running'}
                  tasksCompleted={runtimeStatus?.completed_tasks || taskOutputs.length}
                  tasksFailed={runtimeStatus?.failed_tasks || 0}
                  tasksHandoff={runtimeStatus?.handoff_tasks || 0}
                  tasksTotal={state.tasks.length}
                  totalTokens={runtimeStatus?.total_tokens_used || state.tasks.reduce((total, task) => total + task.tokens_used, 0)}
                  logCount={runtimeStatus?.log_count || 0}
                  finalSummary={runtimeStatus?.final_summary}
                  taskOutputs={taskOutputs}
                  onOpenTask={setSelectedTaskId}
                />
              )}

              {viewMode === 'card' ? (
                <CardFlowRenderer viewModel={viewModel} selectedTaskId={selectedTaskId} onSelectTask={setSelectedTaskId} onOpenHandoff={setSelectedHandoffId} />
              ) : (
                <Suspense fallback={<div className="flex min-h-[620px] items-center justify-center rounded-xl border border-stone-200 bg-white text-sm text-stone-400">Preparing Pixel Office…</div>}>
                  <PixelOfficeRenderer
                    viewModel={viewModel}
                    onSelectTask={setSelectedTaskId}
                    onRequestHandoff={setHandoffTaskId}
                    onOpenHandoff={setSelectedHandoffId}
                    onPause={state.goal?.status === 'running' && goalId ? () => pauseGoal.mutate(goalId) : undefined}
                  />
                </Suspense>
              )}
            </div>
          )}
        </main>
      </div>

      <BottomConsole goalId={goalId} />

      <AgentDetailModal
        task={selectedTask}
        isLoading={isTaskLoading}
        onClose={() => setSelectedTaskId(null)}
        handoffs={state?.tasks.find((task) => task.id === selectedTaskId)?.handoffs || []}
        onOpenHandoff={setSelectedHandoffId}
        onPause={state?.goal?.status === 'running' && goalId ? () => pauseGoal.mutate(goalId) : undefined}
        onRetry={selectedTask && ['failed', 'blocked', 'revision_required', 'completed_unverified', 'cancelled'].includes(selectedTask.status) ? () => retryTask.mutate(selectedTask.id) : undefined}
        onHandoff={selectedTask && ['assigned', 'running', 'failed', 'handoff'].includes(selectedTask.status) ? () => setHandoffTaskId(selectedTask.id) : undefined}
      />

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
