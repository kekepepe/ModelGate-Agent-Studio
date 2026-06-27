import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import type { ScoreBreakdown } from '../types/router';
import { DIMENSION_LABELS, DIMENSION_COLORS } from '../types/router';

interface ScoreBreakdownPanelProps {
  scoreBreakdown: ScoreBreakdown[];
  confidence: number;
}

export default function ScoreBreakdownPanel({ scoreBreakdown, confidence }: ScoreBreakdownPanelProps) {
  const [expanded, setExpanded] = useState(false);

  if (!scoreBreakdown || scoreBreakdown.length === 0) return null;

  const topModel = scoreBreakdown[0];
  const dimensions = topModel.dimension_scores || [];

  const totalWeighted = dimensions.reduce((sum, d) => sum + (d.weighted_score || 0), 0);

  return (
    <div className="mt-3 border-t border-stone-200 pt-3">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-sm text-stone-600 hover:text-stone-900 transition-colors"
        data-testid="score-breakdown-toggle"
      >
        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        <span>{expanded ? '收起评分详情' : '查看评分详情'}</span>
      </button>

      {expanded && (
        <div className="mt-3 space-y-3" data-testid="score-breakdown-content">
          <div className="text-sm font-medium text-stone-700">
            {topModel.model_name} — 总分: {(topModel.total_score * 100).toFixed(1)}
          </div>
          {dimensions.map((dim) => {
            const pct = Math.round((dim.score || 0) * 100);
            const colorClass = DIMENSION_COLORS[dim.dimension] || 'bg-stone-400';
            return (
              <div key={dim.dimension} className="space-y-1">
                <div className="flex items-center justify-between text-xs text-stone-600">
                  <span>{DIMENSION_LABELS[dim.dimension] || dim.dimension}</span>
                  <span className="text-stone-500">
                    {dim.score.toFixed(2)} × {dim.weight.toFixed(2)} = {dim.weighted_score.toFixed(4)}
                  </span>
                </div>
                <div className="h-2 bg-stone-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${colorClass} rounded-full transition-all duration-500`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <div className="text-xs text-stone-400">{dim.reason}</div>
              </div>
            );
          })}
          <div className="pt-2 border-t border-stone-100 flex items-center justify-between text-sm">
            <span className="text-stone-500">加权得分总和</span>
            <span className="font-medium text-stone-800">{totalWeighted.toFixed(4)}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-stone-500">置信度</span>
            <span className="font-medium text-stone-800">{(confidence * 100).toFixed(1)}%</span>
          </div>
        </div>
      )}
    </div>
  );
}
