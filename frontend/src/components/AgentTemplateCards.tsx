import { Compass, Code, Eye, Search, FileText, Shield } from 'lucide-react';
import { ROLE_CONFIG } from '../types/agent';
import type { AgentTemplate } from '../types/agent';

const ROLE_ICONS: Record<string, React.ReactNode> = {
  planner: <Compass size={24} />,
  coder: <Code size={24} />,
  reviewer: <Eye size={24} />,
  research: <Search size={24} />,
  summarizer: <FileText size={24} />,
  supervisor: <Shield size={24} />,
};

interface AgentTemplateCardsProps {
  templates: AgentTemplate[];
  onSelect: (template: AgentTemplate) => void;
  onCustom: () => void;
}

export default function AgentTemplateCards({ templates, onSelect, onCustom }: AgentTemplateCardsProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {templates.map((template) => {
        const config = ROLE_CONFIG[template.role] || { bg: 'bg-stone-100', text: 'text-stone-600', iconColor: '#57534e' };
        const icon = ROLE_ICONS[template.role];
        const defaultModel = template.default_config.default_model_id as string;
        const allowHandoff = template.default_config.allow_handoff as boolean;

        return (
          <button
            key={template.id}
            onClick={() => onSelect(template)}
            className="text-left bg-white border border-stone-200 rounded-xl p-5 hover:border-lavender-300 hover:shadow-sm transition-all duration-200 active:scale-[0.98]"
          >
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center mb-3"
              style={{ backgroundColor: config.bg.replace('bg-', '') === config.bg ? config.bg : undefined, background: `color-mix(in srgb, ${config.iconColor} 15%, white)` }}
            >
              <span style={{ color: config.iconColor }}>{icon}</span>
            </div>
            <h3 className="text-base font-semibold text-stone-800 mb-1">{template.name}</h3>
            <p className="text-sm text-stone-500 mb-3 line-clamp-2">{template.description}</p>
            <div className="text-xs text-stone-400 space-y-1">
              <div>建议模型: {defaultModel}</div>
              <div>允许 Handoff: {allowHandoff ? '是' : '否'}</div>
            </div>
          </button>
        );
      })}

      <button
        onClick={onCustom}
        className="text-left bg-white border border-dashed border-stone-300 rounded-xl p-5 hover:border-stone-400 hover:bg-stone-50 transition-all duration-200"
      >
        <div className="w-10 h-10 rounded-lg bg-stone-100 flex items-center justify-center mb-3 text-stone-400">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 5v14M5 12h14" />
          </svg>
        </div>
        <h3 className="text-base font-semibold text-stone-700 mb-1">自定义</h3>
        <p className="text-sm text-stone-400">从零开始配置 Agent</p>
      </button>
    </div>
  );
}
