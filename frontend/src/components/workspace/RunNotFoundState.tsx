import { AlertTriangle, RefreshCcw } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function RunNotFoundState({ runId, message, onRetry }: { runId: string; message?: string; onRetry: () => void }) {
  return <div className="flex min-h-[calc(100vh-3.5rem)] w-full items-center justify-center px-6">
    <div className="max-w-md rounded-2xl border border-stone-200 bg-white p-8 text-center shadow-sm">
      <AlertTriangle className="mx-auto text-amber-600" size={30} />
      <h1 className="mt-4 text-lg font-semibold">无法打开这个 Run</h1>
      <p className="mt-2 text-sm text-stone-500">{message || `Run ${runId} 不存在、已删除，或后端暂时不可用。`}</p>
      <div className="mt-6 flex justify-center gap-2">
        <button onClick={onRetry} className="inline-flex items-center gap-1.5 rounded-lg border border-stone-200 px-3 py-2 text-sm"><RefreshCcw size={14} />重试</button>
        <Link to="/workspace" className="rounded-lg bg-stone-900 px-3 py-2 text-sm text-white">返回 Workspace</Link>
        <Link to="/studio" className="rounded-lg border border-stone-200 px-3 py-2 text-sm">返回 Studio</Link>
      </div>
    </div>
  </div>;
}
