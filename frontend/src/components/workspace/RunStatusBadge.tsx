import { runStatusLabel } from '../../utils/runStatus';

export default function RunStatusBadge({ status }: { status: string }) {
  const tone = ['completed'].includes(status) ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
    : ['failed', 'blocked'].includes(status) ? 'bg-red-50 text-red-700 border-red-200'
      : ['cancelled', 'stopped'].includes(status) ? 'bg-stone-100 text-stone-600 border-stone-200'
        : ['running', 'handoff', 'reviewing'].includes(status) ? 'bg-blue-50 text-blue-700 border-blue-200'
          : 'bg-amber-50 text-amber-700 border-amber-200';
  return <span className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-medium ${tone}`}>{runStatusLabel(status)}</span>;
}
