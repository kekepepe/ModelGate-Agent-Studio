import { ArrowRight, Boxes, Copy, Play, Settings2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { TEAM_PRESETS, type TeamPreset } from '../types/team';

const ACCENT_STYLES: Record<TeamPreset['accent'], { top: string; icon: string; button: string }> = {
  blue: { top: 'border-t-blue-500', icon: 'bg-blue-50 text-blue-700', button: 'bg-blue-600 hover:bg-blue-700' },
  green: { top: 'border-t-emerald-500', icon: 'bg-emerald-50 text-emerald-700', button: 'bg-emerald-700 hover:bg-emerald-800' },
  purple: { top: 'border-t-purple-500', icon: 'bg-purple-50 text-purple-700', button: 'bg-purple-700 hover:bg-purple-800' },
  amber: { top: 'border-t-amber-500', icon: 'bg-amber-50 text-amber-700', button: 'bg-stone-800 hover:bg-stone-900' },
};

export default function StudioPage() {
  const navigate = useNavigate();

  const openWorkspace = (preset: TeamPreset) => {
    navigate(`/workspace?team=${preset.id}`);
  };

  return (
    <div className="mx-auto w-full max-w-[1400px] px-5 py-8 sm:px-8">
      <header className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-stone-950">选择一支 Agent 团队</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-stone-500">
            从交付目标开始，而不是先填写底层 Agent 表单。每支团队都会进入可切换的 Card Flow 与 Pixel Office 工作区。
          </p>
        </div>
        <button
          type="button"
          onClick={() => openWorkspace(TEAM_PRESETS[3])}
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-stone-300 bg-white px-4 py-2 text-sm font-medium text-stone-700 hover:border-stone-400 hover:bg-stone-50"
        >
          <Boxes size={16} /> 自定义团队
        </button>
      </header>

      <section aria-label="团队模板" className="grid gap-5 lg:grid-cols-2">
        {TEAM_PRESETS.map((preset) => (
          <TeamPresetCard key={preset.id} preset={preset} onRun={() => openWorkspace(preset)} />
        ))}
      </section>

      <section className="mt-10 border-t border-stone-200 pt-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-stone-800">最近运行</h2>
            <p className="mt-1 text-xs text-stone-500">完成首个 Goal 后，这里会显示团队版本、运行状态和最近产物。</p>
          </div>
          <button type="button" onClick={() => navigate('/dashboard')} className="text-xs font-medium text-blue-700 hover:text-blue-900">
            查看运行概览
          </button>
        </div>
        <div className="mt-4 rounded-xl border border-dashed border-stone-300 bg-white px-5 py-8 text-center text-sm text-stone-400">
          还没有最近运行。选择上方团队并点击“立即运行”。
        </div>
      </section>
    </div>
  );
}

function TeamPresetCard({ preset, onRun }: { preset: TeamPreset; onRun: () => void }) {
  const accent = ACCENT_STYLES[preset.accent];
  return (
    <article className={`group flex min-h-[260px] flex-col rounded-xl border border-stone-200 border-t-4 ${accent.top} bg-white p-5 shadow-sm transition-shadow hover:shadow-md`}>
      <div className="flex items-start justify-between gap-4">
        <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${accent.icon}`}>
          <Boxes size={20} />
        </div>
        <span className="text-[11px] font-medium uppercase tracking-[0.14em] text-stone-400">{preset.category}</span>
      </div>
      <h2 className="mt-4 text-lg font-semibold text-stone-900">{preset.name}</h2>
      <p className="mt-1 text-sm leading-6 text-stone-500">{preset.description}</p>

      <div className="mt-5 flex items-center overflow-x-auto pb-1" aria-label={`${preset.name}角色流`}>
        {preset.roles.map((role, index) => (
          <div key={`${preset.id}-${role.role}`} className="flex shrink-0 items-center">
            <div className="rounded-lg border border-stone-200 bg-stone-50 px-3 py-2">
              <p className="text-xs font-semibold text-stone-700">{role.label}</p>
              <p className="mt-0.5 text-[10px] text-stone-400">{role.modelHint}</p>
            </div>
            {index < preset.roles.length - 1 ? <ArrowRight size={15} className="mx-1.5 text-stone-300" /> : null}
          </div>
        ))}
      </div>

      <div className="mt-auto flex items-center gap-2 pt-5">
        <button type="button" onClick={onRun} className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-white ${accent.button}`}>
          <Play size={15} fill="currentColor" /> 立即运行
        </button>
        <button type="button" onClick={onRun} className="inline-flex items-center gap-2 rounded-lg border border-stone-300 px-3 py-2 text-sm font-medium text-stone-600 hover:bg-stone-50">
          <Settings2 size={15} /> 配置
        </button>
        <button type="button" aria-label={`复制${preset.name}`} className="ml-auto rounded-lg p-2 text-stone-400 hover:bg-stone-100 hover:text-stone-700">
          <Copy size={16} />
        </button>
      </div>
    </article>
  );
}
