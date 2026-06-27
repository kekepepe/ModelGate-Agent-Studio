import { useState } from 'react';
import { Route, Shuffle, AlertTriangle, Loader2 } from 'lucide-react';
import { useSelectModel, useOverrideModel } from '../hooks/useModelRouter';
import type { RoutingResult } from '../types/router';
import { TASK_TYPE_LABELS } from '../types/router';
import RoutingResultCard from '../components/RoutingResultCard';

const TASK_TYPES = [
  'planning', 'coding', 'review', 'research',
  'summarization', 'supervision', 'debugging',
  'documentation', 'testing', 'general',
];

const COMPLEXITY_OPTIONS = [
  { value: 'simple', label: '简单' },
  { value: 'moderate', label: '中等' },
  { value: 'complex', label: '复杂' },
  { value: 'very_complex', label: '非常复杂' },
];

const BUDGET_OPTIONS = [
  { value: 'low', label: '低成本优先' },
  { value: 'medium', label: '均衡' },
  { value: 'high', label: '高质量优先' },
  { value: 'unlimited', label: '不限' },
];

const SPEED_OPTIONS = [
  { value: 'fast', label: '快速响应' },
  { value: 'balanced', label: '均衡' },
  { value: 'quality', label: '质量优先' },
];

export default function ModelRouterPage() {
  const [taskType, setTaskType] = useState('coding');
  const [complexity, setComplexity] = useState('moderate');
  const [contextLength, setContextLength] = useState(8000);
  const [budget, setBudget] = useState('medium');
  const [speed, setSpeed] = useState('balanced');
  const [hasVision, setHasVision] = useState(false);
  const [needsTools, setNeedsTools] = useState(false);
  const [result, setResult] = useState<RoutingResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selectModel = useSelectModel();
  const overrideModel = useOverrideModel();

  const handleSubmit = async () => {
    setError(null);
    setResult(null);
    try {
      const res = await selectModel.mutateAsync({
        task_id: `task-${Date.now()}`,
        task_type: taskType,
        task_complexity: complexity,
        context_length_estimate: contextLength,
        budget_preference: budget,
        speed_preference: speed,
        has_vision_input: hasVision,
        requires_tool_calling: needsTools,
      });
      setResult(res);
    } catch (e: any) {
      setError(e?.message || '路由请求失败');
    }
  };

  const handleAccept = () => {
    // In a real workspace, this would proceed with task execution
    setResult(null);
  };

  const handleOverride = async (modelId: string) => {
    if (!result) return;
    try {
      await overrideModel.mutateAsync({
        task_id: result.selected_model_id,
        selected_model_id: modelId,
        original_model_id: result.selected_model_id,
        reason: '用户手动切换模型',
      });
      // Update displayed result
      setResult({
        ...result,
        selected_model_id: modelId,
        is_user_override: true,
        override_note: '用户手动切换模型',
      });
    } catch (e: any) {
      setError(e?.message || '覆盖失败');
    }
  };

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-stone-900 flex items-center gap-2">
          <Route size={24} className="text-lavender-600" />
          Model Router
        </h1>
        <p className="text-stone-500 mt-1">
          测试模型路由决策 — 根据任务特征自动选择最合适的模型
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Form */}
        <div className="bg-white border border-stone-200 rounded-xl p-6">
          <h2 className="text-base font-semibold text-stone-800 mb-4 flex items-center gap-2">
            <Shuffle size={16} className="text-lavender-600" />
            路由参数
          </h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-stone-700 mb-1.5">任务类型</label>
              <select
                value={taskType}
                onChange={(e) => setTaskType(e.target.value)}
                className="w-full px-3 py-2 border border-stone-200 rounded-lg text-sm text-stone-800 bg-white focus:outline-none focus:ring-2 focus:ring-lavender-300 focus:border-lavender-400"
              >
                {TASK_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {TASK_TYPE_LABELS[t] || t}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-stone-700 mb-1.5">任务复杂度</label>
              <div className="grid grid-cols-2 gap-2">
                {COMPLEXITY_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setComplexity(opt.value)}
                    className={`px-3 py-2 text-sm rounded-lg border transition-all ${
                      complexity === opt.value
                        ? 'border-lavender-400 bg-lavender-50 text-lavender-800'
                        : 'border-stone-200 text-stone-600 hover:border-stone-300'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-stone-700 mb-1.5">
                预估上下文长度: {contextLength.toLocaleString()} tokens
              </label>
              <input
                type="range"
                min={1000}
                max={200000}
                step={1000}
                value={contextLength}
                onChange={(e) => setContextLength(Number(e.target.value))}
                className="w-full accent-lavender-600"
              />
              <div className="flex justify-between text-xs text-stone-400 mt-1">
                <span>1K</span>
                <span>200K</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-stone-700 mb-1.5">预算偏好</label>
              <div className="flex gap-2">
                {BUDGET_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setBudget(opt.value)}
                    className={`flex-1 px-3 py-2 text-sm rounded-lg border transition-all ${
                      budget === opt.value
                        ? 'border-lavender-400 bg-lavender-50 text-lavender-800'
                        : 'border-stone-200 text-stone-600 hover:border-stone-300'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-stone-700 mb-1.5">速度偏好</label>
              <div className="flex gap-2">
                {SPEED_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setSpeed(opt.value)}
                    className={`flex-1 px-3 py-2 text-sm rounded-lg border transition-all ${
                      speed === opt.value
                        ? 'border-lavender-400 bg-lavender-50 text-lavender-800'
                        : 'border-stone-200 text-stone-600 hover:border-stone-300'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex gap-4">
              <label className="flex items-center gap-2 text-sm text-stone-600 cursor-pointer">
                <input
                  type="checkbox"
                  checked={hasVision}
                  onChange={(e) => setHasVision(e.target.checked)}
                  className="rounded border-stone-300 text-lavender-600 focus:ring-lavender-400"
                />
                包含视觉输入
              </label>
              <label className="flex items-center gap-2 text-sm text-stone-600 cursor-pointer">
                <input
                  type="checkbox"
                  checked={needsTools}
                  onChange={(e) => setNeedsTools(e.target.checked)}
                  className="rounded border-stone-300 text-lavender-600 focus:ring-lavender-400"
                />
                需要工具调用
              </label>
            </div>
          </div>

          <button
            onClick={handleSubmit}
            disabled={selectModel.isPending}
            className="mt-6 w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-lavender-600 hover:bg-lavender-700 disabled:bg-stone-300 disabled:cursor-not-allowed rounded-lg transition-colors"
          >
            {selectModel.isPending ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                路由中...
              </>
            ) : (
              <>
                <Shuffle size={16} />
                执行路由
              </>
            )}
          </button>
        </div>

        {/* Result area */}
        <div className="space-y-4">
          {error && (
            <div className="bg-brick-50 border border-brick-200 rounded-xl p-4 flex items-start gap-3">
              <AlertTriangle size={18} className="text-brick-600 shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-medium text-brick-800">路由失败</div>
                <div className="text-sm text-brick-600 mt-0.5">{error}</div>
              </div>
            </div>
          )}

          {!result && !error && !selectModel.isPending && (
            <div className="bg-stone-50 border border-dashed border-stone-200 rounded-xl p-8 text-center">
              <Shuffle size={32} className="text-stone-300 mx-auto mb-3" />
              <p className="text-stone-500 text-sm">设置路由参数并点击「执行路由」查看结果</p>
            </div>
          )}

          {result && (
            <RoutingResultCard
              result={result}
              onAccept={handleAccept}
              onOverride={handleOverride}
              onDismiss={() => setResult(null)}
              autoDismiss={false}
            />
          )}
        </div>
      </div>
    </div>
  );
}
