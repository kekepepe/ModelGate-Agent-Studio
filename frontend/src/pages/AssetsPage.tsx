import { FileBox, RotateCcw } from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import { useRunAssets } from '../hooks/useRuns';

export default function AssetsPage() {
  const [params] = useSearchParams();
  const runId = params.get('runId') || undefined;
  const { data, isLoading, error } = useRunAssets(runId);
  return <div className="mx-auto max-w-[1200px] px-4 py-8 sm:px-6"><div className="flex items-start justify-between gap-4"><div><h1 className="text-2xl font-semibold">Assets</h1><p className="mt-1 text-sm text-stone-500">运行产物、生成文件与验证状态。</p></div>{runId ? <Link to={`/workspace/runs/${runId}`} className="inline-flex items-center gap-1.5 rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm"><RotateCcw size={14} />返回当前 Workspace</Link> : null}</div>
    {runId ? <div className="mt-5 rounded-lg border border-blue-200 bg-blue-50 px-3 py-2 text-sm text-blue-800">当前筛选 Run：<span className="font-mono">{runId}</span></div> : <div className="mt-8 rounded-2xl border border-dashed border-stone-300 bg-white p-10 text-center text-sm text-stone-500">请从 Workspace Run 进入 Assets，以保留运行上下文。</div>}
    {isLoading ? <div className="mt-6 h-32 animate-pulse rounded-xl bg-stone-100" /> : error ? <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">加载产物失败：{error.message}</div> : data?.items.length ? <div className="mt-6 divide-y divide-stone-100 overflow-hidden rounded-xl border border-stone-200 bg-white">{data.items.map((item) => <div key={item.id} className="flex items-center gap-3 p-4"><FileBox size={18} className="text-blue-600" /><div className="min-w-0 flex-1"><p className="truncate text-sm font-medium">{item.path || item.id}</p><p className="mt-0.5 text-xs text-stone-400">{item.type} · {item.verification_status || 'unverified'}</p></div></div>)}</div> : runId ? <div className="mt-8 rounded-2xl border border-dashed border-stone-300 bg-white p-10 text-center text-sm text-stone-500">这个 Run 尚未注册产物。</div> : null}
  </div>;
}
