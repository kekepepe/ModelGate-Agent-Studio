import { Outlet, useLocation } from 'react-router-dom';
import GlobalHeader from './GlobalHeader';

export default function AppShell() {
  const location = useLocation();
  const runMatch = location.pathname.match(/^\/workspace\/runs\/([^/]+)/);
  const runId = runMatch?.[1];
  const params = new URLSearchParams(location.search);
  const contextRunId = runId || params.get('runId') || undefined;
  const goalId = params.get('goalId') || undefined;

  return (
    <div className="min-h-screen bg-stone-50 text-stone-900">
      <GlobalHeader runId={contextRunId} goalId={goalId} />
      <main className={runId ? 'app-shell-run-main' : 'min-h-[calc(100vh-3.5rem)]'}>
        <Outlet />
      </main>
    </div>
  );
}
