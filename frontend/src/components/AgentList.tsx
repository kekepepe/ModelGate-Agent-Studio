import type { AgentListItem } from '../types/agent';
import RoleTag from './RoleTag';
import StatusIndicator from './StatusIndicator';
import AgentStatusToggle from './AgentStatusToggle';

interface AgentListProps {
  agents: AgentListItem[];
  onSelect: (agent: AgentListItem) => void;
}

export default function AgentList({ agents, onSelect }: AgentListProps) {
  if (agents.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="w-12 h-12 rounded-full bg-stone-100 flex items-center justify-center mb-4">
          <svg className="w-6 h-6 text-stone-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        </div>
        <h3 className="text-base font-medium text-stone-600 mb-1">还没有配置 Agent Station</h3>
        <p className="text-sm text-stone-400 max-w-xs mb-6">
          Agent Station 是多模型协作中的角色工位。每个工位有固定职责，可绑定不同模型执行。
        </p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-stone-200">
      {agents.map((agent) => (
        <div
          key={agent.id}
          onClick={() => onSelect(agent)}
          className={`flex items-center gap-4 px-4 py-3 cursor-pointer transition-colors hover:bg-stone-50 ${
            !agent.is_enabled ? 'opacity-60' : ''
          }`}
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-0.5">
              <span className="text-sm font-medium text-stone-800 truncate">{agent.name}</span>
              <RoleTag role={agent.role} />
            </div>
            <div className="flex items-center gap-3 text-xs text-stone-400">
              <span>模型: {agent.default_model_id}</span>
            </div>
          </div>

          <div className="flex items-center gap-4 shrink-0">
            <StatusIndicator status={agent.is_enabled ? agent.status : 'disabled'} />
            <AgentStatusToggle
              agentId={agent.id}
              isEnabled={agent.is_enabled}
              hasRunningTask={agent.status === 'running'}
            />
            <button
              onClick={(e) => {
                e.stopPropagation();
                onSelect(agent);
              }}
              className="text-xs text-stone-500 hover:text-stone-800 px-2 py-1"
            >
              编辑
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
