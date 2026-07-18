import { Activity, ArrowRight, Search } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useMemo, useState } from 'react';
import { useRuns } from '../hooks/useRuns';
import type { WorkspaceRunSummary } from '../types/run';
import RunStatusBadge from '../components/workspace/RunStatusBadge';
import { getTeamPreset } from '../types/team';

const FILTERS = [
  { value: '', label: '全部' }, { value: 'active', label: '运行中' }, { value: 'completed', label: '已完成' },
  { value: 'failed', label: '失败' }, { value: 'stopped', label: '已停止' },
];

export default function WorkspaceOverviewPage() {
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');
  const filters = useMemo(() => ({ status: status || undefined, search: search.trim() || undefined }), [status, search]);
  const { data, isLoading, error, refetch } = useRuns(filters);
  const sections = useMemo(() => {
    const items = data?.items || [];
    const active = new Set(['idle', 'planning', 'ready', 'running', 'paused', 'waiting', 'waiting_approval', 'replanning', 'revision_required', 'blocked', 'handoff', 'reviewing']);
    return [
      { title: 'Active Runs', description: '正在规划、执行或等待处理的运行', items: items.filter((run) => active.has(run.status)) },
      { title: 'Recent Runs', description: '最近更新的运行', items: items.slice(0, 6) },
      { title: 'Completed Runs', description: '已完成并可导出产物的运行', items: items.filter((run) => ['completed', 'done'].includes(run.status)).slice(0, 6) },
      { title: 'Failed / Stopped Runs', description: '需要检查错误或已由用户停止的运行', items: items.filter((run) => ['failed', 'error', 'cancelled', 'stopped'].includes(run.status)).slice(0, 6) },
    ];
  }, [data?.items]);

  return <div className="mx-auto max-w-[1400px] px-4 py-8 sm:px-6">
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div><p className="text-xs font-medium uppercase tracking-[0.16em] text-blue-700">Execution control center</p><h1 className="mt-1 text-2xl font-semibold">Workspace</h1><p className="mt-1 text-sm text-stone-500">查找、恢复和跟踪所有 Agent Run。</p></div>
      <Link to="/studio" className="rounded-lg bg-stone-900 px-4 py-2 text-sm font-medium text-white hover:bg-stone-800">从 Studio 创建 Run</Link>
    </div>
    <div className="mt-7 flex flex-wrap items-center gap-2">
      {FILTERS.map((item) => <button key={item.value} onClick={() => setStatus(item.value)} className={`rounded-lg border px-3 py-1.5 text-sm ${status === item.value ? 'border-stone-800 bg-stone-800 text-white' : 'border-stone-200 bg-white text-stone-600 hover:border-stone-300'}`}>{item.label}</button>)}
      <label className="ml-auto flex min-w-64 items-center gap-2 rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm"><Search size={15} className="text-stone-400" /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="搜索 Goal" className="w-full bg-transparent outline-none" /></label>
    </div>
    {isLoading ? <RunListSkeleton /> : error ? <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-5 text-sm text-red-700">加载 Run 失败：{error.message} <button onClick={() => refetch()} className="ml-2 underline">重试</button></div> : data?.items.length ? (!status && !search.trim() ? <div className="mt-8 space-y-10">{sections.map((section) => <RunSection key={section.title} {...section} />)}</div> : <RunSection title="Filtered Runs" description={`${data.total} 个匹配结果`} items={data.items} />) : <EmptyRuns />}
  </div>;
}

function RunCard({ run }: { run: WorkspaceRunSummary }) {
  const team = getTeamPreset(run.team_id);
  const updated = run.updated_at ? new Intl.DateTimeFormat('zh-CN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(run.updated_at)) : '—';
  return <article className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm transition hover:border-stone-300 hover:shadow-md">
    <div className="flex items-start justify-between gap-3"><div className="min-w-0"><p className="text-xs text-stone-400">{team.name} · <span className="font-mono">{run.run_id.slice(0, 12)}</span></p><h2 className="mt-1 truncate font-semibold">{run.name}</h2><p className="mt-1 line-clamp-2 text-sm text-stone-500">{run.goal_summary}</p></div><RunStatusBadge status={run.status} /></div>
    <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-stone-100"><span className="block h-full rounded-full bg-blue-600" style={{ width: `${run.progress}%` }} /></div>
    <div className="mt-2 flex justify-between text-xs text-stone-500"><span>{run.completed_tasks}/{run.total_tasks} Tasks · {run.progress}%</span><span>Quota {run.quota_percent}%</span></div>
    <dl className="mt-4 grid grid-cols-3 gap-2 rounded-xl bg-stone-50 p-3 text-xs"><div><dt className="text-stone-400">当前阶段</dt><dd className="mt-1 truncate font-medium">{run.current_stage}</dd></div><div><dt className="text-stone-400">Agents</dt><dd className="mt-1 font-medium">{run.active_agents} active</dd></div><div><dt className="text-stone-400">更新</dt><dd className="mt-1 truncate font-medium">{updated}</dd></div></dl>
    <div className="mt-4 flex flex-wrap items-center gap-2"><Link to={`/workspace/runs/${run.run_id}`} className="inline-flex items-center gap-1.5 rounded-lg bg-stone-900 px-3 py-2 text-sm text-white">进入 Workspace <ArrowRight size={14} /></Link><Link to={`/logs?runId=${run.run_id}&goalId=${run.goal_id}`} className="rounded-lg border border-stone-200 px-3 py-2 text-sm text-stone-600">Logs</Link><Link to={`/evolution?runId=${run.run_id}&goalId=${run.goal_id}`} className="rounded-lg border border-stone-200 px-3 py-2 text-sm text-stone-600">Evolution</Link><Link to={`/assets?runId=${run.run_id}`} className="rounded-lg border border-stone-200 px-3 py-2 text-sm text-stone-600">Assets</Link></div>
  </article>;
}

function RunSection({ title, description, items }: { title: string; description: string; items: WorkspaceRunSummary[] }) {
  return <section aria-labelledby={`run-section-${title.replaceAll(' ', '-').toLowerCase()}`} className="mt-7"><div className="mb-4 flex items-end justify-between"><div><h2 id={`run-section-${title.replaceAll(' ', '-').toLowerCase()}`} className="text-base font-semibold">{title}</h2><p className="mt-0.5 text-xs text-stone-500">{description}</p></div><span className="text-xs text-stone-400">{items.length} runs</span></div>{items.length ? <div className="grid gap-4 lg:grid-cols-2">{items.map((run) => <RunCard key={`${title}-${run.run_id}`} run={run} />)}</div> : <div className="rounded-xl border border-dashed border-stone-200 bg-white px-4 py-8 text-center text-sm text-stone-400">此分组暂无 Run</div>}</section>;
}

function EmptyRuns() { return <div className="mt-10 rounded-2xl border border-dashed border-stone-300 bg-white px-6 py-16 text-center"><Activity className="mx-auto text-stone-300" /><h2 className="mt-4 font-semibold">当前没有匹配的 Workspace Run</h2><p className="mt-1 text-sm text-stone-500">从 Studio 选择一支 Agent 团队并创建 Goal。</p><Link to="/studio" className="mt-5 inline-block rounded-lg bg-stone-900 px-4 py-2 text-sm text-white">前往 Studio</Link></div>; }
function RunListSkeleton() { return <div className="mt-6 grid gap-4 lg:grid-cols-2">{[0, 1, 2, 3].map((item) => <div key={item} className="h-56 animate-pulse rounded-2xl border border-stone-200 bg-white p-5"><div className="h-4 w-2/3 rounded bg-stone-100" /><div className="mt-3 h-3 w-full rounded bg-stone-100" /><div className="mt-8 h-16 rounded-xl bg-stone-100" /></div>)}</div>; }
