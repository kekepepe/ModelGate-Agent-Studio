import { Routes, Route, Link } from 'react-router-dom'
import AgentRegistryPage from './pages/AgentRegistryPage'
import ModelRouterPage from './pages/ModelRouterPage'

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
          </div>
        </div>
      </nav>
      <main className="flex-1">
        <Routes>
          <Route path="/agents" element={<AgentRegistryPage />} />
          <Route path="/router" element={<ModelRouterPage />} />
          <Route path="/" element={<AgentRegistryPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
