import { Bot, Boxes, ChartNoAxesCombined } from 'lucide-react';
import { useMemo } from 'react';
import { Link, NavLink } from 'react-router-dom';
import { useDashboardStats } from '../../hooks/useDashboard';
import { useRun } from '../../hooks/useRuns';
import { useAgents } from '../../hooks/useAgents';
import { AgentStatusBadge } from '../ui/agent-status-badge';

/**
 * Star-Office-UI's 6 state display order. Used for the topbar
 * distribution chips so the most-relevant counts are shown first
 * (running, writing, ... before disabled/queued).
 */
const STATE_ORDER: string[] = [
  'running',
  'writing',
  'researching',
  'executing',
  'syncing',
  'paused',
  'error',
  'failed',
  'handoff',
  'idle',
  'completed',
  'pending',
  'queued',
  'reviewing',
  'cancelled',
  'stopped',
  'disabled',
];

export default function GlobalHeader({ runId, goalId }: { runId?: string; goalId?: string }) {
  const { data } = useDashboardStats();
  const { data: contextualRun } = useRun(runId);
  const { data: agentsResp } = useAgents({ is_enabled: true, page_size: 100 });
  const resolvedGoalId = goalId || contextualRun?.goal_id;
  const contextual = (path: string, kind: 'run' | 'evolution' = 'run') => {
    const params = new URLSearchParams();
    if (runId) params.set('runId', runId);
    if (kind === 'evolution' && resolvedGoalId) params.set('goalId', resolvedGoalId);
    return params.size ? `${path}?${params}` : path;
  };

  // Station state distribution — rendered as a single row of compact chips
  // (仿 Star-Office-UI's status bar idea: "[●5 idle] [●3 running] [●1 error]").
  const distribution = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const a of agentsResp?.items ?? []) {
      counts[a.status] = (counts[a.status] ?? 0) + 1;
    }
    // Stable order: STATE_ORDER first, then any remaining states
    const ordered: Array<[string, number]> = [];
    const seen = new Set<string>();
    for (const s of STATE_ORDER) {
      if (counts[s]) {
        ordered.push([s, counts[s]]);
        seen.add(s);
      }
    }
    for (const [s, n] of Object.entries(counts)) {
      if (!seen.has(s)) ordered.push([s, n]);
    }
    return ordered;
  }, [agentsResp]);

  return (
    <header className="sticky top-0 z-50 h-14 border-b border-stone-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-full max-w-[1600px] items-center gap-3 px-4 sm:px-6">
        <Link to="/studio" aria-label="ModelGate Studio" className="flex shrink-0 items-center gap-2 text-sm font-semibold">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg border border-blue-200 bg-blue-50 text-blue-700"><Bot size={17} /></span>
          <span>ModelGate</span>
        </Link>
        <nav aria-label="Primary navigation" className="flex min-w-0 items-center gap-1 overflow-x-auto">
          <GlobalNavLink to="/studio">Studio</GlobalNavLink>
          <GlobalNavLink to="/workspace">Workspace</GlobalNavLink>
          <GlobalNavLink to={contextual('/assets')}>Assets</GlobalNavLink>
          <GlobalNavLink to={contextual('/evolution', 'evolution')}>Evolution</GlobalNavLink>
          <GlobalNavLink to={contextual('/logs')}>Logs</GlobalNavLink>
        </nav>

        {/* V1.0-6b: Station state distribution (仿 Star-Office-UI control bar) */}
        {distribution.length > 0 && (
          <div
            className="ml-auto hidden items-center gap-1 xl:flex"
            aria-label="Station state distribution"
            title="仿 Star-Office-UI 状态分布条"
          >
            {distribution.map(([state, n]) => (
              <AgentStatusBadge
                key={state}
                state={state}
                label={n.toString()}
                dot
                className="px-1.5 py-0 font-mono text-[10px]"
              />
            ))}
          </div>
        )}

        <Link
          to="/dashboard"
          className="hidden shrink-0 items-center gap-2 rounded-lg border border-stone-200 px-3 py-1.5 text-xs text-stone-600 hover:bg-stone-50 lg:flex"
        >
          <ChartNoAxesCombined size={14} />
          <span>{data?.active_goals ?? '—'} active runs</span>
          <span className="text-stone-300">·</span>
          <Boxes size={13} />
          <span>{(data?.total_tokens_today ?? 0).toLocaleString()} tokens</span>
        </Link>
      </div>
    </header>
  );
}

function GlobalNavLink({ to, children }: { to: string; children: React.ReactNode }) {
  return <NavLink to={to} className={({ isActive }) => `rounded-md px-3 py-2 text-sm font-medium transition-colors ${isActive ? 'bg-stone-100 text-stone-950' : 'text-stone-500 hover:bg-stone-50 hover:text-stone-900'}`}>{children}</NavLink>;
}
