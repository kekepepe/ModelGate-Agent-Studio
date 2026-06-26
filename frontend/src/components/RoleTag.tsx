import { Compass, Code, Eye, Search, FileText, Shield, User } from 'lucide-react';
import { ROLE_CONFIG } from '../types/agent';
import type { AgentRole } from '../types/agent';

const ROLE_ICONS: Record<string, React.ReactNode> = {
  planner: <Compass size={14} />,
  coder: <Code size={14} />,
  reviewer: <Eye size={14} />,
  research: <Search size={14} />,
  summarizer: <FileText size={14} />,
  supervisor: <Shield size={14} />,
};

interface RoleTagProps {
  role: AgentRole;
}

export default function RoleTag({ role }: RoleTagProps) {
  const config = ROLE_CONFIG[role] || { label: role, bg: 'bg-stone-100', text: 'text-stone-600', iconColor: '#57534e' };
  const icon = ROLE_ICONS[role] || <User size={14} />;

  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.text}`}
    >
      <span style={{ color: config.iconColor }}>{icon}</span>
      {config.label}
    </span>
  );
}
