import { lazy, Suspense } from 'react'
import { Navigate, Routes, Route } from 'react-router-dom'
import './styles/animations.css'
import AppShell from './components/app-shell/AppShell'

// Keep the application shell responsive and load each workspace surface only
// when its route is visited. This is especially important for Logs, Evolution
// and Dashboard, which pull in heavier visualization dependencies.
const AgentRegistryPage = lazy(() => import('./pages/AgentRegistryPage'))
const ModelRouterPage = lazy(() => import('./pages/ModelRouterPage'))
const QuotaOverviewPage = lazy(() => import('./pages/QuotaOverviewPage'))
const HandoffPage = lazy(() => import('./pages/HandoffPage'))
const LogsPage = lazy(() => import('./pages/LogsPage'))
const WorkspacePage = lazy(() => import('./pages/WorkspacePage'))
const EvolutionReviewPage = lazy(() => import('./pages/EvolutionReviewPage'))
const ModelManagerPage = lazy(() => import('./pages/ModelManagerPage'))
const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const ToolManagerPage = lazy(() => import('./pages/ToolManagerPage'))
const StudioPage = lazy(() => import('./pages/StudioPage'))
const WorkspaceOverviewPage = lazy(() => import('./pages/WorkspaceOverviewPage'))
const CreateRunPage = lazy(() => import('./pages/CreateRunPage'))
const AssetsPage = lazy(() => import('./pages/AssetsPage'))

function App() {
  return (
    <Suspense fallback={<RouteLoadingFallback />}>
      <Routes>
        <Route element={<AppShell />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/agents" element={<AgentRegistryPage />} />
            <Route path="/models" element={<ModelManagerPage />} />
            <Route path="/router" element={<ModelRouterPage />} />
            <Route path="/quota" element={<QuotaOverviewPage />} />
            <Route path="/handoffs" element={<HandoffPage />} />
            <Route path="/tools" element={<ToolManagerPage />} />
            <Route path="/logs" element={<LogsPage />} />
            <Route path="/workspace" element={<WorkspaceOverviewPage />} />
            <Route path="/workspace/new" element={<CreateRunPage />} />
            <Route path="/workspace/runs/:runId" element={<WorkspacePage />} />
            <Route path="/workspace/:legacyId" element={<LegacyRunRedirect />} />
            <Route path="/run/:legacyId" element={<LegacyRunRedirect />} />
            <Route path="/agent-workspace/:legacyId" element={<LegacyRunRedirect />} />
            <Route path="/assets" element={<AssetsPage />} />
            <Route path="/evolution" element={<EvolutionReviewPage />} />
            <Route path="/studio" element={<StudioPage />} />
            <Route path="/" element={<Navigate to="/studio" replace />} />
        </Route>
      </Routes>
    </Suspense>
  )
}

function LegacyRunRedirect() {
  const legacyId = window.location.pathname.split('/').filter(Boolean).at(-1)
  return <Navigate to={`/workspace/runs/${legacyId}`} replace />
}

function RouteLoadingFallback() {
  return (
    <div className="flex min-h-48 items-center justify-center text-sm text-stone-400">
      正在加载工作区…
    </div>
  )
}

export default App
