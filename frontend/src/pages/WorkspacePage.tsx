import { lazy, Suspense, useCallback, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useWorkspaceState, useTaskDetail, useExecuteGoal, usePauseGoal, useResumeGoal, useRuntimeEvents, useStopGoal, useRetryTask } from '../hooks/useWorkspace';
import { useAgents } from '../hooks/useAgents';
import { useAcceptHandoff, useHandoff, useTriggerHandoff, useUpdateHandoffResult } from '../hooks/useHandoffs';
import TopStatusBar from '../components/TopStatusBar';
import GoalInputPanel from '../components/GoalInputPanel';
import TaskTree from '../components/TaskTree';
import AgentDetailModal from '../components/AgentDetailModal';
import CardFlowRenderer from '../components/CardFlowRenderer';
import BottomConsole from '../components/BottomConsole';
import HandoffConfirmModal from '../components/HandoffConfirmModal';
import HandoffDetailDrawer from '../components/HandoffDetailDrawer';
import type { WorkspaceTask } from '../types/workspace';
import type { HandoffReason, HandoffResult } from '../types/handoff';
import { getTeamPreset } from '../types/team';
import { buildWorkspaceViewModel, type WorkspaceViewMode } from '../utils/workspaceViewModel';

const PixelOfficeRenderer = lazy(() => import('../components/PixelOfficeRenderer'));

export default function WorkspacePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const teamPreset = getTeamPreset(searchParams.get('team'));
  const [goalId, setGoalId] = useState<string | null>(() => searchParams.get('goal'));
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<WorkspaceViewMode>(() => window.localStorage.getItem('modelgate-workspace-view') === 'pixel' ? 'pixel' : 'card');

  const { data: state, isLoading } = useWorkspaceState(goalId);
  const { data: taskDetail, isLoading: isTaskLoading } = useTaskDetail(selectedTaskId);
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
    setSearchParams((current) => {
      const next = new URLSearchParams(current);
      next.set('goal', newGoalId);
      return next;
    }, { replace: true });
  }, [setSearchParams]);

  const agents = agentsData?.items || [];
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
    <div className="workspace-shell flex min-h-0 flex-1 flex-col">
      <TopStatusBar
        goal={state?.goal || null}
        tasks={state?.tasks || []}
        teamName={teamPreset.name}
        showWhenEmpty
        mode={viewMode}
        onModeChange={handleModeChange}
        onExecute={goalId ? () => executeGoal.mutate(goalId) : undefined}
        onPause={goalId ? () => pauseGoal.mutate(goalId) : undefined}
        onResume={goalId ? () => resumeGoal.mutate(goalId) : undefined}
        onStop={goalId && !['completed', 'failed', 'cancelled'].includes(state?.goal?.status || '') ? () => stopGoal.mutate(goalId) : undefined}
        onExport={handleExport}
        isBusy={executeGoal.isPending || pauseGoal.isPending || resumeGoal.isPending || stopGoal.isPending}
      />

      <div className="workspace-body flex min-h-0 flex-1 overflow-hidden">
        <aside className="workspace-sidebar">
          <GoalInputPanel
            onGoalCreated={handleGoalCreated}
            activeGoalId={goalId}
            goalTitle={state?.goal?.title || null}
            goal={state?.goal || null}
            preset={teamPreset}
          />
          <TaskTree
            tasks={state?.tasks || []}
            goalTitle={state?.goal?.title || null}
            onTaskClick={setSelectedTaskId}
            selectedTaskId={selectedTaskId}
          />
        </aside>

        <main className="workspace-main">
          {isLoading && goalId ? <div className="workspace-loading-overlay">Loading workspace state…</div> : null}
          {viewMode === 'card' ? <CardFlowRenderer viewModel={viewModel} selectedTaskId={selectedTaskId} onSelectTask={setSelectedTaskId} onOpenHandoff={setSelectedHandoffId} /> : <Suspense fallback={<div className="workspace-loading-overlay">Preparing Pixel Office…</div>}>
            <PixelOfficeRenderer viewModel={viewModel} onSelectTask={setSelectedTaskId} onRequestHandoff={setHandoffTaskId} onOpenHandoff={setSelectedHandoffId} onPause={state?.goal?.status === 'running' && goalId ? () => pauseGoal.mutate(goalId) : undefined} />
          </Suspense>}
        </main>
      </div>

      <BottomConsole goalId={goalId} tasks={state?.tasks || []} handoffs={state?.handoffs || []} />

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
