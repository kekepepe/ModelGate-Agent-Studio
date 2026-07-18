import { Bot, Boxes, ChartNoAxesCombined } from 'lucide-react';
import { Link, NavLink } from 'react-router-dom';
import { useDashboardStats } from '../../hooks/useDashboard';
import { useRun } from '../../hooks/useRuns';

export default function GlobalHeader({ runId, goalId }: { runId?: string; goalId?: string }) {
  const { data } = useDashboardStats();
  const { data: contextualRun } = useRun(runId);
  const resolvedGoalId = goalId || contextualRun?.goal_id;
  const contextual = (path: string, kind: 'run' | 'evolution' = 'run') => {
    const params = new URLSearchParams();
    if (runId) params.set('runId', runId);
    if (kind === 'evolution' && resolvedGoalId) params.set('goalId', resolvedGoalId);
    return params.size ? `${path}?${params}` : path;
  };

  return (
    <header className="sticky top-0 z-50 h-14 border-b border-stone-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-full max-w-[1600px] items-center gap-6 px-4 sm:px-6">
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
        <Link to="/dashboard" className="ml-auto hidden shrink-0 items-center gap-2 rounded-lg border border-stone-200 px-3 py-1.5 text-xs text-stone-600 hover:bg-stone-50 lg:flex">
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
