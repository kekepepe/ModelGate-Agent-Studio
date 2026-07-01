import { Routes, Route, Link } from 'react-router-dom'
import AgentRegistryPage from './pages/AgentRegistryPage'
import ModelRouterPage from './pages/ModelRouterPage'
import QuotaOverviewPage from './pages/QuotaOverviewPage'
import HandoffPage from './pages/HandoffPage'
import LogsPage from './pages/LogsPage'
import WorkspacePage from './pages/WorkspacePage'
import EvolutionReviewPage from './pages/EvolutionReviewPage'
import './styles/animations.css'

function App() {
  return (
    <div className="min-h-screen flex flex-col bg-stone-50">
      <nav className="bg-white border-b border-stone-200 px-4 sm:px-6 lg:px-8">
        <div className="max-w-[1400px] mx-auto flex items-center gap-6 h-14">
          <Link to="/" className="text-base font-semibold text-stone-900">
            ModelGate
          </Link>
          <div className="flex items-center gap-4 text-sm">
            <Link to="/agents" className="text-stone-600 hover:text-stone-900">
              Agent Registry
            </Link>
            <Link to="/router" className="text-stone-600 hover:text-stone-900">
              Model Router
            </Link>
            <Link to="/quota" className="text-stone-600 hover:text-stone-900">
              Quota Manager
            </Link>
            <Link to="/handoffs" className="text-stone-600 hover:text-stone-900">
              Handoff Manager
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
        <Routes>
          <Route path="/agents" element={<AgentRegistryPage />} />
          <Route path="/router" element={<ModelRouterPage />} />
          <Route path="/quota" element={<QuotaOverviewPage />} />
          <Route path="/handoffs" element={<HandoffPage />} />
          <Route path="/logs" element={<LogsPage />} />
          <Route path="/workspace" element={<WorkspacePage />} />
          <Route path="/evolution" element={<EvolutionReviewPage />} />
          <Route path="/" element={<AgentRegistryPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
