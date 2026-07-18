import { useState } from 'react';
import { useEvolutionSummary, useApproveMemory, useApproveSkill } from '../hooks/useKnowledge';
import type { MemoryDraft, SkillDraft } from '../types/knowledge';
import { MEMORY_TYPE_LABELS } from '../types/knowledge';
import KnowledgeSourcesPanel from '../components/KnowledgeSourcesPanel';

export default function EvolutionReviewPage() {
  const { data, isLoading } = useEvolutionSummary();
  const approveMemory = useApproveMemory();
  const approveSkill = useApproveSkill();
  const [tab, setTab] = useState<'sources' | 'memories' | 'skills'>('sources');

  return (
    <div className="max-w-[1200px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-stone-900">Evolution Review</h1>
          <p className="text-sm text-stone-500 mt-1">
            {data ? `${data.pending_review} pending review · ${data.total_memories} memories · ${data.total_skills} skills` : 'Loading...'}
          </p>
        </div>
      </div>

      <div className="flex gap-4 mb-4">
        <button
          onClick={() => setTab('sources')}
          className={`px-3 py-1.5 text-sm rounded-lg border ${tab === 'sources' ? 'bg-stone-800 text-white border-stone-800' : 'bg-white text-stone-600 border-stone-200'}`}
        >
          Knowledge Sources
        </button>
        <button
          onClick={() => setTab('memories')}
          className={`px-3 py-1.5 text-sm rounded-lg border ${tab === 'memories' ? 'bg-stone-800 text-white border-stone-800' : 'bg-white text-stone-600 border-stone-200'}`}
        >
          Memories ({data?.total_memories || 0})
        </button>
        <button
          onClick={() => setTab('skills')}
          className={`px-3 py-1.5 text-sm rounded-lg border ${tab === 'skills' ? 'bg-stone-800 text-white border-stone-800' : 'bg-white text-stone-600 border-stone-200'}`}
        >
          Skills ({data?.total_skills || 0})
        </button>
      </div>

      {tab === 'sources' && <KnowledgeSourcesPanel />}

      {tab !== 'sources' && isLoading && (
        <div className="space-y-3">
          <div className="h-20 bg-stone-200 rounded animate-pulse" />
          <div className="h-20 bg-stone-200 rounded animate-pulse" />
        </div>
      )}

      {!isLoading && tab === 'memories' && data?.memory_drafts.length === 0 && (
        <div className="text-center text-stone-400 text-sm py-12">暂无记忆草稿，执行 Goal 后自动生成</div>
      )}

      {!isLoading && tab === 'skills' && data?.skill_drafts.length === 0 && (
        <div className="text-center text-stone-400 text-sm py-12">暂无技能草稿，完成多任务执行后自动生成</div>
      )}

      {!isLoading && tab === 'memories' && (
        <div className="space-y-3">
          {data?.memory_drafts.map((mem) => (
            <MemoryCard
              key={mem.id}
              memory={mem}
              onApprove={(approved) => approveMemory.mutate({ id: mem.id, approved })}
              isApproving={approveMemory.isPending}
            />
          ))}
        </div>
      )}

      {!isLoading && tab === 'skills' && (
        <div className="space-y-3">
          {data?.skill_drafts.map((skill) => (
            <SkillCard
              key={skill.id}
              skill={skill}
              onApprove={(approved) => approveSkill.mutate({ id: skill.id, approved })}
              isApproving={approveSkill.isPending}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function MemoryCard({ memory, onApprove, isApproving }: { memory: MemoryDraft; onApprove: (approved: boolean) => void; isApproving: boolean }) {
  const isPending = memory.human_approved === null;
  const isApproved = memory.human_approved === true;
  return (
    <div className={`bg-white rounded-xl border p-4 ${isPending ? 'border-lavender-300 bg-lavender-50' : isApproved ? 'border-green-200' : 'border-stone-200'}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs px-1.5 py-0.5 rounded bg-stone-100 text-stone-600 font-medium">
              {MEMORY_TYPE_LABELS[memory.type] || memory.type}
            </span>
            <span className="text-xs text-stone-400">Confidence: {(memory.confidence * 100).toFixed(0)}%</span>
          </div>
          <h3 className="text-sm font-semibold text-stone-800">{memory.title}</h3>
          <p className="text-sm text-stone-600 mt-1 whitespace-pre-wrap line-clamp-3">{memory.content}</p>
          <p className="mt-2 text-xs text-stone-500">
            来源 Goal：{memory.source_goal_id || '未记录'}{memory.reason ? ` · 生成依据：${memory.reason}` : ''}
          </p>
          {memory.tags.length > 0 && (
            <div className="flex gap-1 mt-2">
              {memory.tags.map((tag) => (
                <span key={tag} className="text-[10px] px-1.5 py-0.5 bg-stone-100 text-stone-500 rounded">{tag}</span>
              ))}
            </div>
          )}
        </div>
        {isPending && (
          <div className="flex gap-2 flex-shrink-0">
            <button
              onClick={() => onApprove(true)}
              disabled={isApproving}
              className="px-3 py-1 text-xs bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-40"
            >Approve</button>
            <button
              onClick={() => onApprove(false)}
              disabled={isApproving}
              className="px-3 py-1 text-xs bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-40"
            >Reject</button>
          </div>
        )}
        {isApproved && <span className="text-xs text-green-600 flex-shrink-0">✓ Approved</span>}
        {memory.human_approved === false && <span className="text-xs text-red-600 flex-shrink-0">✗ Rejected</span>}
      </div>
    </div>
  );
}

function SkillCard({ skill, onApprove, isApproving }: { skill: SkillDraft; onApprove: (approved: boolean) => void; isApproving: boolean }) {
  const isPending = skill.human_approved === null;
  const isApproved = skill.human_approved === true;
  return (
    <div className={`bg-white rounded-xl border p-4 ${isPending ? 'border-lavender-300 bg-lavender-50' : isApproved ? 'border-green-200' : 'border-stone-200'}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${skill.status === 'approved' ? 'bg-green-100 text-green-700' : skill.status === 'rejected' ? 'bg-red-100 text-red-700' : 'bg-stone-100 text-stone-600'}`}>
              {skill.status}
            </span>
          </div>
          <h3 className="text-sm font-semibold text-stone-800">{skill.name}</h3>
          {skill.scenario && <p className="text-sm text-stone-500 mt-1">{skill.scenario}</p>}
          <p className="mt-2 text-xs text-stone-500">来源运行：{skill.source_run_id || '未记录'}</p>
          <div className="grid grid-cols-3 gap-2 mt-2 text-xs text-stone-600">
            <div><span className="text-stone-400">Steps: </span>{skill.steps.length}</div>
            <div><span className="text-stone-400">Agents: </span>{skill.recommended_agents.length}</div>
            <div><span className="text-stone-400">Tools: </span>{skill.tools.length}</div>
          </div>
        </div>
        {isPending && (
          <div className="flex gap-2 flex-shrink-0">
            <button onClick={() => onApprove(true)} disabled={isApproving} className="px-3 py-1 text-xs bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-40">Approve</button>
            <button onClick={() => onApprove(false)} disabled={isApproving} className="px-3 py-1 text-xs bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-40">Reject</button>
          </div>
        )}
        {isApproved && <span className="text-xs text-green-600 flex-shrink-0">✓ Approved</span>}
        {skill.human_approved === false && <span className="text-xs text-red-600 flex-shrink-0">✗ Rejected</span>}
      </div>
    </div>
  );
}
