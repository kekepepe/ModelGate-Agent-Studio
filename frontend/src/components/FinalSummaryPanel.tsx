import { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  CircleDollarSign,
  Clock,
  Coins,
  FileText,
  Hourglass,
  Info,
  Layers,
  Sparkles,
  Users,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { AgentStatusBadge } from './ui/agent-status-badge';
import { cn } from '@/lib/utils';
import type { FinalSummary } from '../types/runtime';

/**
 * V1.0-6d — FinalSummaryPanel.
 *
 * Inspired by Star-Office-UI's "Memo" / "昨日小记" panel
 * (ringhyacinth/Star-Office-UI, 7K+ stars, Feb 2026): when the
 * run completes, a structured summary card shows what was done
 * (and what wasn't) without burying the user in logs.
 *
 * Adapts the same idea to ModelGate: when a Run reaches status
 * 'completed', render a card with the 7 fields produced by
 * `_build_final_summary` in runtime_service.
 *
 * Fields shown:
 *   - completed:    list of completed task titles
 *   - incomplete:   list of task titles that did not finish
 *   - quality:      Supervisor review verdict
 *   - risks:        risk flags and caveats
 *   - models:       which models were used
 *   - handoff_count: how many agent handoffs happened
 *   - cost:         honest "currency estimate unavailable" block
 *   - multi_agent:  multi-agent metrics
 */
interface FinalSummaryPanelProps {
  summary: FinalSummary | null | undefined;
  goalTitle?: string;
  /** Optional: when true, always render the panel (even for not-completed) */
  forceOpen?: boolean;
}

export default function FinalSummaryPanel({
  summary,
  goalTitle,
  forceOpen,
}: FinalSummaryPanelProps) {
  const [expanded, setExpanded] = useState(true);

  // Hide entirely when there is no summary yet AND caller didn't force
  if (!summary && !forceOpen) return null;
  if (!summary) {
    return (
      <Card className="border-dashed bg-stone-50">
        <CardContent className="flex items-center gap-2 py-3 text-xs text-stone-500">
          <Hourglass size={13} /> 暂无 Final Summary — Goal 完成后会自动生成。
        </CardContent>
      </Card>
    );
  }

  const { completed, incomplete, quality, risks, models, handoff_count, cost, multi_agent } = summary;
  const allDone = incomplete.length === 0;
  const qualityPassed = quality?.passed === true;

  return (
    <Card
      className="border-emerald-200 bg-gradient-to-b from-emerald-50/40 to-white"
      aria-label="Final summary"
    >
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="flex items-center gap-2 text-sm font-semibold text-stone-800">
          <Sparkles size={14} className="text-emerald-600" />
          Final Summary
          <span className="text-[11px] font-normal text-stone-500">
            {goalTitle ? `· ${goalTitle}` : '· 仿 Star-Office-UI Memo 面板'}
          </span>
        </CardTitle>
        <div className="flex items-center gap-2">
          {allDone ? (
            <AgentStatusBadge state="completed" label="All tasks done" dot={false} className="px-1.5 py-0 text-[10px]" />
          ) : (
            <AgentStatusBadge state="failed" label={`${incomplete.length} 未完成`} dot={false} className="px-1.5 py-0 text-[10px]" />
          )}
          <button
            type="button"
            onClick={() => setExpanded((v) => !v)}
            className="rounded-md p-1 text-stone-500 hover:bg-stone-100"
            aria-label={expanded ? '收起' : '展开'}
          >
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>
      </CardHeader>

      {expanded && (
        <CardContent className="space-y-3 pt-0 text-xs">
          {/* Top stat row */}
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <Stat icon={<CheckCircle2 size={13} className="text-emerald-600" />} label="已完成" value={completed.length.toString()} />
            <Stat icon={<Hourglass size={13} className="text-amber-600" />} label="未完成" value={incomplete.length.toString()} />
            <Stat icon={<Layers size={13} className="text-blue-600" />} label="Handoff 次数" value={handoff_count.toString()} />
            <Stat icon={<Users size={13} className="text-violet-600" />} label="Agent 数" value={models.length.toString()} />
          </div>

          <Separator />

          {/* Quality verdict */}
          <section>
            <SectionHeader icon={<Info size={12} />} title="Quality · Supervisor 审查" />
            {quality ? (
              <div className="rounded-md border border-stone-200 bg-stone-50 p-2">
                <div className="flex items-center gap-2">
                  <span className="text-stone-500">状态：</span>
                  {qualityPassed ? (
                    <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100">通过</Badge>
                  ) : (
                    <Badge className="bg-amber-100 text-amber-800 hover:bg-amber-100">
                      {quality.status || 'not_available'}
                    </Badge>
                  )}
                </div>
                {quality.summary && (
                  <p className="mt-1 text-stone-600">{quality.summary}</p>
                )}
                {quality.reviewer_model_id && (
                  <p className="mt-1 text-[10px] text-stone-400">Reviewer: {quality.reviewer_model_id}</p>
                )}
              </div>
            ) : (
              <p className="text-stone-400 italic">未配置 Supervisor 审查</p>
            )}
          </section>

          {/* Completed / Incomplete lists */}
          <section className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            <TaskList
              icon={<CheckCircle2 size={12} className="text-emerald-600" />}
              title="已完成 Task"
              items={completed}
              empty="（无）"
            />
            <TaskList
              icon={<Clock size={12} className="text-amber-600" />}
              title="未完成 Task"
              items={incomplete}
              empty="（无）"
            />
          </section>

          {/* Models used */}
          <section>
            <SectionHeader icon={<Coins size={12} />} title="模型使用" />
            {models.length === 0 ? (
              <p className="text-stone-400 italic">本次 Run 未使用任何模型（Mock 模式？）</p>
            ) : (
              <ul className="space-y-1">
                {models.map((m) => (
                  <li
                    key={m.id}
                    className="flex items-center justify-between rounded border border-stone-200 bg-white px-2 py-1"
                  >
                    <span className="font-mono text-[11px] text-stone-700">{m.id}</span>
                    <span className="flex items-center gap-2">
                      <span className="text-stone-600">{m.name}</span>
                      {typeof m.cost_level === 'number' && (
                        <Badge variant="secondary" className="text-[10px]">
                          cost {m.cost_level}/5
                        </Badge>
                      )}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* Risks */}
          <section>
            <SectionHeader
              icon={<AlertTriangle size={12} className="text-amber-600" />}
              title={`风险与提示 (${risks.length})`}
            />
            {risks.length === 0 ? (
              <p className="text-stone-400 italic">无显著风险</p>
            ) : (
              <ul className="space-y-1">
                {risks.map((risk, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 rounded border border-amber-200 bg-amber-50 px-2 py-1 text-amber-900"
                  >
                    <AlertTriangle size={11} className="mt-0.5 shrink-0" />
                    <span>{risk}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* Cost block — honest about not having pricing */}
          <section>
            <SectionHeader icon={<CircleDollarSign size={12} />} title="成本估算" />
            <div
              className={cn(
                'rounded-md border p-2 text-[11px]',
                cost?.available
                  ? 'border-emerald-200 bg-emerald-50 text-emerald-900'
                  : 'border-stone-200 bg-stone-50 text-stone-600',
              )}
            >
              {cost?.available ? (
                <span>
                  {cost.currency_estimate} （按模型单价表估算）
                </span>
              ) : (
                <span>
                  <FileText size={11} className="mr-1 inline" />
                  {cost?.note ?? '尚未配置 Provider 单价表，不展示货币金额。'}
                </span>
              )}
            </div>
          </section>

          {/* Multi-agent metrics — collapsed into compact line */}
          {multi_agent && (
            <section className="rounded border border-stone-200 bg-stone-50 p-2 text-[10px] text-stone-500">
              <strong className="text-stone-700">Multi-Agent：</strong>
              {JSON.stringify(multi_agent).slice(0, 200)}
              {JSON.stringify(multi_agent).length > 200 ? '…' : ''}
            </section>
          )}
        </CardContent>
      )}
    </Card>
  );
}

function Stat({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center gap-2 rounded-md border border-stone-200 bg-white px-2 py-1.5">
      {icon}
      <div className="flex flex-col">
        <span className="text-[10px] uppercase tracking-wider text-stone-500">{label}</span>
        <span className="font-mono text-sm font-semibold text-stone-800">{value}</span>
      </div>
    </div>
  );
}

function SectionHeader({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <h4 className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-stone-600">
      {icon} {title}
    </h4>
  );
}

function TaskList({
  icon,
  title,
  items,
  empty,
}: {
  icon: React.ReactNode;
  title: string;
  items: string[];
  empty: string;
}) {
  return (
    <div>
      <SectionHeader icon={icon} title={title} />
      {items.length === 0 ? (
        <p className="text-stone-400 italic">{empty}</p>
      ) : (
        <ul className="space-y-1">
          {items.map((t, i) => (
            <li
              key={i}
              className="flex items-start gap-2 rounded border border-stone-200 bg-white px-2 py-1"
            >
              <span className="text-stone-400">•</span>
              <span className="truncate text-stone-700" title={t}>{t}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
