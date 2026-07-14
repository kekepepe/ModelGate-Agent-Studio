import { lazy, Suspense } from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import './styles/animations.css'

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

function App() {
  return (
    <div className="min-h-screen flex flex-col bg-stone-50">
      <nav className="bg-white border-b border-stone-200 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1400px] mx-auto flex items-center gap-6 h-14">
          <Link to="/" className="text-base font-semibold text-stone-900">
            ModelGate
          </Link>
          <div className="flex items-center gap-4 text-sm">
            <Link to="/dashboard" className="text-stone-600 hover:text-stone-900">
              Dashboard
            </Link>
            <Link to="/agents" className="text-stone-600 hover:text-stone-900">
              Agent Registry
            </Link>
            <Link to="/models" className="text-stone-600 hover:text-stone-900">
              Model Manager
            </Link>
            <Link to="/tools" className="text-stone-600 hover:text-stone-900">
              Tools
            </Link>
            <Link to="/logs" className="text-stone-600 hover:text-stone-900">
              Logs
            </Link>
            <Link to="/workspace" className="text-stone-600 hover:text-stone-900">
              Workspace
            </Link>
            <Link to="/evolution" className="text-stone-600 hover:text-stone-900">
              Evolution
            </Link>
          </div>
        </div>
      </nav>
      <main className="flex-1">
        <Suspense fallback={<RouteLoadingFallback />}>
          <Routes>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/agents" element={<AgentRegistryPage />} />
            <Route path="/models" element={<ModelManagerPage />} />
            <Route path="/router" element={<ModelRouterPage />} />
            <Route path="/quota" element={<QuotaOverviewPage />} />
            <Route path="/handoffs" element={<HandoffPage />} />
            <Route path="/tools" element={<ToolManagerPage />} />
            <Route path="/logs" element={<LogsPage />} />
            <Route path="/workspace" element={<WorkspacePage />} />
            <Route path="/evolution" element={<EvolutionReviewPage />} />
            <Route path="/" element={<DashboardPage />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  )
}

function RouteLoadingFallback() {
  return (
    <div className="flex min-h-48 items-center justify-center text-sm text-stone-400">
      正在加载工作区…
    </div>
  )
}

export default App
