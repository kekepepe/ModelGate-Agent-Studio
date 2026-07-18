import { useState, useEffect, useRef, useCallback } from 'react';
import { Check, Shuffle, AlertTriangle, X } from 'lucide-react';
import type { RoutingResult } from '../types/router';
import { MOCK_MODELS } from '../types/agent';
import ScoreBreakdownPanel from './ScoreBreakdownPanel';
import ModelOverrideModal from './ModelOverrideModal';

interface RoutingResultCardProps {
  result: RoutingResult;
  onAccept?: () => void;
  onOverride?: (modelId: string) => void;
  onDismiss?: () => void;
  autoDismiss?: boolean;
}

export default function RoutingResultCard({
  result,
  onAccept,
  onOverride,
  onDismiss,
  autoDismiss = true,
}: RoutingResultCardProps) {
  const [showOverride, setShowOverride] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [progress, setProgress] = useState(100);
  const containerRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<number | null>(null);

  const selectedModel = MOCK_MODELS.find((m) => m.id === result.selected_model_id);
  const confidencePct = Math.round((result.confidence || 0) * 100);

  const clearDismissTimer = useCallback(() => {
    if (timerRef.current !== null) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setProgress(100);
  }, []);

  const startDismissTimer = useCallback(() => {
    if (!autoDismiss) return;
    clearDismissTimer();
    const duration = 5000;
    const interval = 50;
    let elapsed = 0;

    const t = window.setInterval(() => {
      elapsed += interval;
      const remaining = Math.max(0, duration - elapsed);
      setProgress((remaining / duration) * 100);
      if (remaining <= 0) {
        window.clearInterval(t);
        timerRef.current = null;
        setDismissed(true);
        onDismiss?.();
      }
    }, interval);
    timerRef.current = t;
  }, [autoDismiss, clearDismissTimer, onDismiss]);

  useEffect(() => {
    startDismissTimer();
    return () => clearDismissTimer();
  }, [clearDismissTimer, startDismissTimer]);

  const handleMouseEnter = () => {
    clearDismissTimer();
    setProgress(100);
  };

  const handleMouseLeave = () => {
    startDismissTimer();
  };

  const handleAccept = () => {
    clearDismissTimer();
    onAccept?.();
  };

  const handleOverrideConfirm = (modelId: string) => {
    setShowOverride(false);
    clearDismissTimer();
    onOverride?.(modelId);
  };

  if (dismissed) return null;

  return (
    <>
      <div
        ref={containerRef}
        className="relative bg-white border border-stone-200 rounded-xl shadow-sm p-5 w-full max-w-lg"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        data-testid="routing-result-card"
      >
        {/* Auto-dismiss progress bar */}
        {autoDismiss && (
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-stone-100 rounded-t-xl overflow-hidden">
            <div
              className="h-full bg-lavender-400 transition-all duration-100"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}

        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <div className="w-6 h-6 rounded-full bg-lavender-100 flex items-center justify-center">
                <Shuffle size={14} className="text-lavender-700" />
              </div>
              <h3 className="text-sm font-semibold text-stone-800">模型路由决策</h3>
            </div>
            <div className="text-lg font-semibold text-stone-900">
              {selectedModel?.name || result.selected_model_id}
            </div>
          </div>
          <button
            onClick={() => { setDismissed(true); onDismiss?.(); }}
            className="text-stone-400 hover:text-stone-600 transition-colors"
            data-testid="card-dismiss"
          >
            <X size={16} />
          </button>
        </div>

        {/* Confidence bar */}
        <div className="mb-4">
          <div className="flex items-center justify-between text-xs text-stone-500 mb-1">
            <span>置信度</span>
            <span className="font-medium text-stone-700">{confidencePct}%</span>
          </div>
          <div className="h-2 bg-stone-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                confidencePct >= 80
                  ? 'bg-green-500'
                  : confidencePct >= 60
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
              }`}
              style={{ width: `${confidencePct}%` }}
            />
          </div>
        </div>

        {/* Routing reason */}
        <div className="mb-4 space-y-2">
          <p className="text-sm text-stone-700 font-medium">{result.routing_reason?.summary}</p>
          {result.routing_reason?.primary_factors?.length > 0 && (
            <ul className="space-y-1">
              {result.routing_reason.primary_factors.map((f, i) => (
                <li key={i} className="text-xs text-stone-600 flex items-start gap-1.5">
                  <span className="mt-0.5 w-1 h-1 rounded-full bg-lavender-400 shrink-0" />
                  {f}
                </li>
              ))}
            </ul>
          )}
          {result.routing_reason?.tradeoffs?.length > 0 && (
            <div className="text-xs text-stone-500 pt-1">
              {result.routing_reason.tradeoffs.map((t, i) => (
                <span key={i} className="inline-block mr-2">💡 {t}</span>
              ))}
            </div>
          )}
        </div>

        {/* Risk flags */}
        {result.risk_flags?.length > 0 && (
          <div className="mb-4 space-y-2">
            {result.risk_flags.map((flag, i) => (
              <div
                key={i}
                className={`flex items-start gap-2 p-2.5 rounded-lg text-xs ${
                  flag.severity === 'high'
                    ? 'bg-brick-50 text-brick-700'
                    : flag.severity === 'medium'
                    ? 'bg-amber-50 text-amber-700'
                    : 'bg-stone-50 text-stone-600'
                }`}
                data-testid="risk-flag"
              >
                <AlertTriangle size={14} className="shrink-0 mt-0.5" />
                <div>
                  <div className="font-medium">{flag.message}</div>
                  {flag.suggestion && (
                    <div className="mt-0.5 opacity-80">{flag.suggestion}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Backup models */}
        {result.backup_model_ids?.length > 0 && (
          <div className="mb-4">
            <p className="text-xs text-stone-500 mb-1.5">备用模型</p>
            <div className="flex flex-wrap gap-2">
              {result.backup_model_ids.map((id) => {
                const m = MOCK_MODELS.find((x) => x.id === id);
                return (
                  <span
                    key={id}
                    className="inline-flex items-center px-2 py-1 rounded-md bg-stone-100 text-xs text-stone-600"
                  >
                    {m?.name || id}
                  </span>
                );
              })}
            </div>
          </div>
        )}

        {/* Score breakdown */}
        <ScoreBreakdownPanel scoreBreakdown={result.score_breakdown} confidence={result.confidence} />

        {/* Actions */}
        <div className="mt-4 pt-3 border-t border-stone-100 flex gap-3">
          <button
            onClick={handleAccept}
            className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-lavender-600 hover:bg-lavender-700 rounded-lg transition-colors"
            data-testid="accept-model"
          >
            <Check size={14} />
            接受推荐
          </button>
          <button
            onClick={() => { clearDismissTimer(); setShowOverride(true); }}
            className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2 text-sm font-medium text-stone-700 bg-stone-100 hover:bg-stone-200 rounded-lg transition-colors"
            data-testid="switch-model"
          >
            <Shuffle size={14} />
            切换模型
          </button>
        </div>
      </div>

      {showOverride && (
        <ModelOverrideModal
          result={result}
          onConfirm={handleOverrideConfirm}
          onCancel={() => setShowOverride(false)}
        />
      )}
    </>
  );
}
