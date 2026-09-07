import { Badge } from "./badge"
import { cn } from "@/lib/utils"

/**
 * Agent / Task / Worker status badge.
 *
 * V1.0-5: Maps the 6 Star-Office-UI agent states (idle / writing /
 * researching / executing / syncing / error) plus the ModelGate
 * task + worker status enums onto a single, design-system-aware
 * color palette defined in index.css.
 *
 * Use this everywhere a status pill is needed (TaskCard, AgentStationCard,
 * WorkerBadge, Workspace TopBar, Logs timeline). It is intentionally
 * thin so it can wrap any existing local mapping.
 */

export type AgentVisualState =
  | "idle"
  | "writing"
  | "researching"
  | "executing"
  | "syncing"
  | "error"
  // ModelGate task + worker status enums (from types/workspace.ts)
  | "pending"
  | "running"
  | "paused"
  | "blocked"
  | "completed"
  | "completed_verified"
  | "completed_unverified"
  | "revision_required"
  | "cancelled"
  | "failed"
  | "handoff"
  | "handoff_required"
  | "queued"
  | "reviewing"
  | "skipped"
  | "stopped"
  | "draft"
  | "planning"
  | "ready"
  | "started"
  | "finishing"
  | "done";

const STATE_TO_TOKEN: Record<AgentVisualState, string> = {
  // Star-Office-UI inspired (6 states × 3 zones)
  idle: "var(--state-idle)",
  writing: "var(--state-writing)",
  researching: "var(--state-researching)",
  executing: "var(--state-executing)",
  syncing: "var(--state-syncing)",
  error: "var(--state-error)",
  // ModelGate task states
  pending: "var(--state-idle)",
  running: "var(--state-running)",
  paused: "var(--state-paused)",
  blocked: "var(--state-error)",
  completed: "var(--state-completed)",
  completed_verified: "var(--state-completed)",
  completed_unverified: "var(--state-paused)",
  revision_required: "var(--state-paused)",
  cancelled: "var(--state-idle)",
  failed: "var(--state-failed)",
  handoff: "var(--state-researching)",
  handoff_required: "var(--state-researching)",
  queued: "var(--state-idle)",
  reviewing: "var(--state-researching)",
  skipped: "var(--state-idle)",
  stopped: "var(--state-paused)",
  // ModelGate goal states
  draft: "var(--state-idle)",
  planning: "var(--state-researching)",
  ready: "var(--state-writing)",
  started: "var(--state-running)",
  finishing: "var(--state-syncing)",
  done: "var(--state-completed)",
};

const STATE_LABEL: Record<AgentVisualState, string> = {
  idle: "Idle",
  writing: "Writing",
  researching: "Researching",
  executing: "Executing",
  syncing: "Syncing",
  error: "Error",
  pending: "Pending",
  running: "Running",
  paused: "Paused",
  blocked: "Blocked",
  completed: "Done",
  completed_verified: "Verified",
  completed_unverified: "Unverified",
  revision_required: "Needs revision",
  cancelled: "Cancelled",
  failed: "Failed",
  handoff: "Handoff",
  handoff_required: "Handoff needed",
  queued: "Queued",
  reviewing: "Reviewing",
  skipped: "Skipped",
  stopped: "Stopped",
  draft: "Draft",
  planning: "Planning",
  ready: "Ready",
  started: "Running",
  finishing: "Finishing",
  done: "Done",
};

export interface AgentStatusBadgeProps {
  state: AgentVisualState | string;
  label?: string;
  /** Show a coloured dot to the left of the label. Default true. */
  dot?: boolean;
  className?: string;
}

export function AgentStatusBadge({
  state,
  label,
  dot = true,
  className,
}: AgentStatusBadgeProps) {
  const key = (state in STATE_TO_TOKEN ? state : "idle") as AgentVisualState;
  const color = STATE_TO_TOKEN[key];
  const text = label ?? STATE_LABEL[key] ?? state;

  return (
    <Badge
      variant="secondary"
      className={cn("gap-1.5 font-medium", className)}
      style={{ borderLeft: `3px solid ${color}` }}
    >
      {dot && (
        <span
          aria-hidden
          className="inline-block size-1.5 rounded-full"
          style={{ backgroundColor: color }}
        />
      )}
      {text}
    </Badge>
  );
}
