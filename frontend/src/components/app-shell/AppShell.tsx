import { Outlet, useLocation } from 'react-router-dom';
import GlobalHeader from './GlobalHeader';
import ActiveStationsSidebar from './ActiveStationsSidebar';

export default function AppShell() {
  const location = useLocation();
  const runMatch = location.pathname.match(/^\/workspace\/runs\/([^/]+)/);
  const runId = runMatch?.[1];
  const params = new URLSearchParams(location.search);
  const contextRunId = runId || params.get('runId') || undefined;
  const goalId = params.get('goalId') || undefined;

  return (
    <div className="flex min-h-screen flex-col bg-stone-50 text-stone-900">
      <GlobalHeader runId={contextRunId} goalId={goalId} />
      <div className="flex min-h-0 flex-1">
        <ActiveStationsSidebar />
        <main className={runId ? 'app-shell-run-main flex-1' : 'min-h-[calc(100vh-3.5rem)] flex-1'}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
