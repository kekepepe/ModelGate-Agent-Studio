import { useState, useCallback } from 'react';
import { useWorkspaceState, useTaskDetail } from '../hooks/useWorkspace';
import TopStatusBar from '../components/TopStatusBar';
import GoalInputPanel from '../components/GoalInputPanel';
import TaskCard from '../components/TaskCard';
import TaskTree from '../components/TaskTree';
import AgentStationCard from '../components/AgentStationCard';
import TaskDetailPanel from '../components/TaskDetailPanel';
import BottomConsole from '../components/BottomConsole';
import type { WorkspaceWorker } from '../types/workspace';

export default function WorkspacePage() {
  const [goalId, setGoalId] = useState<string | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);

  const { data: state, isLoading } = useWorkspaceState(goalId);
  const { data: taskDetail } = useTaskDetail(selectedTaskId);

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

  return (
    <div className="flex flex-col h-[calc(100vh-56px)]">
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
              {/* Quick overview cards */}
              <div className="grid grid-cols-4 gap-3">
                <StatCard label="总 Task" value={state.tasks.length.toString()} />
                <StatCard label="运行中" value={state.tasks.filter((t) => t.status === 'running').length.toString()} color="text-blue-600" />
                <StatCard label="已完成" value={state.tasks.filter((t) => t.status === 'completed').length.toString()} color="text-green-600" />
                <StatCard label="交接中" value={state.tasks.filter((t) => t.status === 'handoff').length.toString()} color="text-purple-600" />
              </div>

              {/* Tasks section */}
              {state.tasks.length > 0 && (
                <div>
                  <h3 className="text-sm font-semibold text-stone-700 mb-3">Tasks</h3>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
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
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* Agent Station Board */}
              <div>
                <h3 className="text-sm font-semibold text-stone-700 mb-3">Agent Stations</h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                  {state.agents.map((agent) => (
                    <AgentStationCard
                      key={agent.id}
                      agent={agent}
                      worker={workerMap.get(agent.id) || null}
                      tasks={state.tasks.map((t) => ({
                        id: t.id,
                        title: t.title,
                        status: t.status,
                        agent_id: t.assigned_agent_id,
                      }))}
                      onTaskClick={setSelectedTaskId}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}
        </main>

        {/* Right Panel - Task Detail */}
        <div
          className={`${selectedTaskId ? 'w-[360px]' : 'w-0'} flex-shrink-0 transition-all duration-300 overflow-hidden border-l border-stone-200`}
        >
          {selectedTaskId && (
            <TaskDetailPanel
              task={taskDetail || null}
              onClose={() => setSelectedTaskId(null)}
            />
          )}
        </div>
      </div>

      <BottomConsole goalId={goalId} />
    </div>
  );
}

function StatCard({ label, value, color = 'text-stone-800' }: { label: string; value: string; color?: string }) {
  return (
    <div className="bg-white rounded-lg border border-stone-200 p-3 text-center">
      <div className="text-[10px] text-stone-400 uppercase tracking-wide">{label}</div>
      <div className={`text-lg font-semibold ${color} mt-0.5`}>{value}</div>
    </div>
  );
}
