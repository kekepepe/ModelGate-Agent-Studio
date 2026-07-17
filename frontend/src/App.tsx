import { lazy, Suspense } from 'react'
import { Routes, Route, Link, NavLink } from 'react-router-dom'
import { Bot, ChevronDown } from 'lucide-react'
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
const StudioPage = lazy(() => import('./pages/StudioPage'))

function App() {
  return (
    <div className="min-h-screen flex flex-col bg-stone-50">
      <nav className="bg-white border-b border-stone-200 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1400px] mx-auto flex items-center gap-7 h-14">
          <Link to="/" className="flex items-center gap-2 text-base font-semibold text-stone-900">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-blue-200 bg-blue-50 text-blue-700">
              <Bot size={16} />
            </span>
            ModelGate
          </Link>
          <div className="flex items-center gap-1 text-sm">
            <PrimaryNavLink to="/" end>Studio</PrimaryNavLink>
            <PrimaryNavLink to="/workspace">Workspace</PrimaryNavLink>
            <div className="group relative">
              <button type="button" className="inline-flex items-center gap-1 rounded-md px-3 py-2 text-sm font-medium text-stone-500 hover:bg-stone-50 hover:text-stone-900">
                Assets <ChevronDown size={13} />
              </button>
              <div className="invisible absolute left-0 top-full z-50 mt-1 w-44 translate-y-1 rounded-lg border border-stone-200 bg-white p-1 opacity-0 shadow-lg transition-all group-hover:visible group-hover:translate-y-0 group-hover:opacity-100 group-focus-within:visible group-focus-within:translate-y-0 group-focus-within:opacity-100">
                <AssetLink to="/agents" label="Agents" detail="角色与工位" />
                <AssetLink to="/models" label="Models" detail="Provider 与模型" />
                <AssetLink to="/tools" label="Tools" detail="工具与权限" />
              </div>
            </div>
            <PrimaryNavLink to="/evolution">Evolution</PrimaryNavLink>
            <PrimaryNavLink to="/logs">Logs</PrimaryNavLink>
          </div>
          <Link to="/dashboard" className="ml-auto text-xs font-medium text-stone-400 hover:text-stone-700">运行概览</Link>
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
            <Route path="/" element={<StudioPage />} />
          </Routes>
        </Suspense>
      </main>
    </div>
  )
}

function PrimaryNavLink({ to, end = false, children }: { to: string; end?: boolean; children: React.ReactNode }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) => `rounded-md px-3 py-2 text-sm font-medium transition-colors ${
        isActive ? 'bg-stone-100 text-stone-900' : 'text-stone-500 hover:bg-stone-50 hover:text-stone-900'
      }`}
    >
      {children}
    </NavLink>
  )
}

function AssetLink({ to, label, detail }: { to: string; label: string; detail: string }) {
  return (
    <Link to={to} className="block rounded-md px-3 py-2 hover:bg-stone-50">
      <span className="block text-sm font-medium text-stone-700">{label}</span>
      <span className="block text-[11px] text-stone-400">{detail}</span>
    </Link>
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
