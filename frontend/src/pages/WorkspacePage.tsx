import { lazy, Suspense, useMemo, useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { useTaskDetail, useExecuteGoal, usePauseGoal, useResumeGoal, useRuntimeEvents, useRuntimeStatus, useStopGoal, useRetryTask, useConfirmPlan, useUpdatePlan } from '../hooks/useWorkspace';
import { useExportRun, useRunWorkspace } from '../hooks/useRuns';
import { useAgents } from '../hooks/useAgents';
import { useAcceptHandoff, useHandoff, useTriggerHandoff, useUpdateHandoffResult } from '../hooks/useHandoffs';
import GoalInputPanel from '../components/GoalInputPanel';
import PlanOverviewPanel from '../components/PlanOverviewPanel';
import TaskTree from '../components/TaskTree';
import AgentDetailModal from '../components/AgentDetailModal';
import CardFlowRenderer from '../components/CardFlowRenderer';
import ThreeZoneCardFlow from '../components/ThreeZoneCardFlow';
import BottomConsole from '../components/BottomConsole';
import HandoffConfirmModal from '../components/HandoffConfirmModal';
import HandoffDetailDrawer from '../components/HandoffDetailDrawer';
import type { WorkspaceTask } from '../types/workspace';
import type { HandoffReason, HandoffResult } from '../types/handoff';
import { getTeamPreset } from '../types/team';
import { buildWorkspaceViewModel, type WorkspaceViewMode } from '../utils/workspaceViewModel';
import WorkspaceRunHeader from '../components/workspace/WorkspaceRunHeader';
import RunNotFoundState from '../components/workspace/RunNotFoundState';

const PixelOfficeRenderer = lazy(() => import('../components/PixelOfficeRenderer'));

export default function WorkspacePage() {
  const { runId = '' } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<WorkspaceViewMode>(() => {
    const requested = searchParams.get('view');
    const persisted = window.localStorage.getItem(`workspace:view:${runId}`);
    if (requested === 'zones' || (!requested && persisted === 'zones')) return 'zones';
    if (requested === 'pixel' || (!requested && persisted === 'pixel')) return 'pixel';
    return 'card';
  });

  const { data: state, isLoading, error: workspaceError, refetch } = useRunWorkspace(runId);
  const goalId = state?.goal?.id || null;
  const teamPreset = getTeamPreset(state?.goal?.team_preset);
  const { data: taskDetail, isLoading: isTaskLoading } = useTaskDetail(selectedTaskId);
  const { data: runtimeStatus } = useRuntimeStatus(goalId);
  useRuntimeEvents(goalId);
  const { data: agentsData } = useAgents({ page_size: 100 });
  const executeGoal = useExecuteGoal();
  const confirmPlan = useConfirmPlan();
  const updatePlan = useUpdatePlan();
  const pauseGoal = usePauseGoal();
  const resumeGoal = useResumeGoal();
  const stopGoal = useStopGoal();
  const exportRun = useExportRun();
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
  const activeTasks = useMemo(() => {
    if (!state) return [];
    const activeTaskIds = state.active_plan?.tasks
      .map((task) => task.runtime_task_id)
      .filter((taskId): taskId is string => Boolean(taskId)) || [];
    if (activeTaskIds.length === 0) return state.tasks;
    const taskById = new Map(state.tasks.map((task) => [task.id, task]));
    return activeTaskIds.flatMap((taskId) => {
      const task = taskById.get(taskId);
      return task ? [task] : [];
    });
  }, [state]);

  const agents = agentsData?.items || [];
  const activeHandoffTask = handoffTaskId ? state?.tasks.find((task) => task.id === handoffTaskId) : null;
  const selectedTask = mergeTaskDetail(taskDetail || null, state?.tasks.find((task) => task.id === selectedTaskId) || null);
  const handleModeChange = (mode: WorkspaceViewMode) => {
    setViewMode(mode);
    window.localStorage.setItem(`workspace:view:${runId}`, mode);
    setSearchParams((current) => {
      const next = new URLSearchParams(current);
      next.set('view', mode);
      return next;
    }, { replace: true });
  };
  const handleExport = async () => {
    const exported = await exportRun.mutateAsync(runId);
    const url = URL.createObjectURL(new Blob([exported.content], { type: 'application/json' }));
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = exported.file_name;
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

  if (isLoading && !state) {
    return <div className="workspace-run-skeleton"><div /><div /><div /></div>;
  }
  if (workspaceError || !state?.goal) {
    return <RunNotFoundState runId={runId} onRetry={() => refetch()} />;
  }

  return (
    <div className="workspace-shell flex min-h-0 flex-1 flex-col">
      <WorkspaceRunHeader
        runId={runId}
        goal={state.goal}
        tasks={activeTasks}
        teamName={teamPreset.name}
        mode={viewMode}
        onModeChange={handleModeChange}
        onExecute={goalId ? () => executeGoal.mutate(goalId) : undefined}
        onPause={goalId ? () => pauseGoal.mutate(goalId) : undefined}
        onResume={goalId ? () => resumeGoal.mutate(goalId) : undefined}
        onStop={goalId && !['completed', 'failed', 'cancelled'].includes(state?.goal?.status || '') ? () => stopGoal.mutate(goalId) : undefined}
        onExport={handleExport}
        isBusy={executeGoal.isPending || pauseGoal.isPending || resumeGoal.isPending || stopGoal.isPending || exportRun.isPending}
        metrics={state?.multi_agent_metrics}
      />

      <div className="workspace-body flex min-h-0 flex-1 overflow-hidden">
        <aside className="workspace-sidebar">
          <GoalInputPanel
            onGoalCreated={() => undefined}
            activeGoalId={goalId}
            goalTitle={state?.goal?.title || null}
            goal={state?.goal || null}
            preset={teamPreset}
          />
          <PlanOverviewPanel
            activePlan={state?.active_plan}
            versions={state?.plan_versions}
            changes={state?.replan_events}
            completionEvidence={state?.completion_evidence}
            onConfirm={goalId && state?.active_plan ? () => confirmPlan.mutateAsync({ goalId, version: state.active_plan!.version }).then(() => undefined) : undefined}
            onModify={goalId && state?.active_plan ? (objectives) => updatePlan.mutateAsync({
              goalId,
              plan: {
                ...state.active_plan!,
                tasks: state.active_plan!.tasks.map((task, index) => ({ ...task, objective: objectives[index] })),
              },
              reason: 'User modified Task objectives before execution.',
            }).then(() => undefined) : undefined}
            onDowngrade={goalId && state?.active_plan ? () => updatePlan.mutateAsync({
              goalId,
              plan: {
                ...state.active_plan!,
                task_mode: state.active_plan!.tasks.length === 1 ? 'single_agent' : 'sequential_multi_agent',
                tasks: state.active_plan!.tasks.map((task) => ({ ...task, parallel_safe: false })),
              },
              reason: 'User downgraded parallel execution to a sequential plan.',
            }).then(() => undefined) : undefined}
            isMutating={confirmPlan.isPending || updatePlan.isPending}
            mutationError={(confirmPlan.error || updatePlan.error)?.message || null}
          />
          <TaskTree
            tasks={activeTasks}
            goalTitle={state?.goal?.title || null}
            onTaskClick={setSelectedTaskId}
            selectedTaskId={selectedTaskId}
          />
        </aside>

        <main className="workspace-main">
          {isLoading && goalId ? <div className="workspace-loading-overlay">Refreshing workspace state…</div> : null}
          {viewMode === 'card' ? (
            <CardFlowRenderer viewModel={viewModel} selectedTaskId={selectedTaskId} onSelectTask={setSelectedTaskId} onOpenHandoff={setSelectedHandoffId} />
          ) : viewMode === 'zones' ? (
            <ThreeZoneCardFlow viewModel={viewModel} selectedTaskId={selectedTaskId} onSelectTask={setSelectedTaskId} />
          ) : (
            <Suspense fallback={<div className="workspace-loading-overlay">Preparing Pixel Office…</div>}>
              <PixelOfficeRenderer viewModel={viewModel} onSelectTask={setSelectedTaskId} onRequestHandoff={setHandoffTaskId} onOpenHandoff={setSelectedHandoffId} onPause={state?.goal?.status === 'running' && goalId ? () => pauseGoal.mutate(goalId) : undefined} />
            </Suspense>
          )}
        </main>
      </div>

      <BottomConsole
        goalId={goalId}
        tasks={activeTasks}
        handoffs={state?.handoffs || []}
        runtimeStatus={runtimeStatus}
        onOpenTask={setSelectedTaskId}
      />

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
