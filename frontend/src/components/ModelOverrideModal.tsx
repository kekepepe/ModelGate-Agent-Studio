import { useState } from 'react';
import { X } from 'lucide-react';
import type { RoutingResult } from '../types/router';
import { MOCK_MODELS } from '../types/agent';

interface ModelOverrideModalProps {
  result: RoutingResult;
  onConfirm: (modelId: string, reason?: string) => void;
  onCancel: () => void;
}

export default function ModelOverrideModal({ result, onConfirm, onCancel }: ModelOverrideModalProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const backupModels = result.backup_model_ids
    .map((id) => MOCK_MODELS.find((m) => m.id === id))
    .filter(Boolean);

  const selectedModel = selectedId ? MOCK_MODELS.find((m) => m.id === selectedId) : null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-stone-900/40 backdrop-blur-sm">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-stone-800">切换模型</h3>
          <button
            onClick={onCancel}
            className="text-stone-400 hover:text-stone-600 transition-colors"
            data-testid="override-cancel"
          >
            <X size={18} />
          </button>
        </div>

        <div className="mb-4">
          <p className="text-sm text-stone-500 mb-1">当前推荐模型</p>
          <div className="text-sm font-medium text-stone-800">
            {MOCK_MODELS.find((m) => m.id === result.selected_model_id)?.name || result.selected_model_id}
          </div>
        </div>

        <div className="mb-4">
          <p className="text-sm text-stone-500 mb-2">备用模型</p>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {backupModels.length === 0 && (
              <p className="text-sm text-stone-400">无备用模型</p>
            )}
            {backupModels.map((model) => {
              if (!model) return null;
              const isSelected = selectedId === model.id;
              return (
                <button
                  key={model.id}
                  onClick={() => setSelectedId(model.id)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg border text-left transition-all ${
                    isSelected
                      ? 'border-lavender-400 bg-lavender-50'
                      : 'border-stone-200 hover:border-stone-300 bg-white'
                  }`}
                  data-testid={`backup-model-${model.id}`}
                >
                  <div>
                    <div className={`text-sm font-medium ${isSelected ? 'text-lavender-800' : 'text-stone-800'}`}>
                      {model.name}
                    </div>
                    <div className="text-xs text-stone-500">{model.provider}</div>
                  </div>
                  {isSelected && (
                    <div className="w-4 h-4 rounded-full bg-lavender-500 flex items-center justify-center">
                      <div className="w-1.5 h-1.5 rounded-full bg-white" />
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {selectedModel && (
          <div className="mb-4 p-3 bg-stone-50 rounded-lg text-sm text-stone-600">
            将切换至 <span className="font-medium text-stone-800">{selectedModel.name}</span>，
            原推荐模型为{' '}
            <span className="font-medium text-stone-800">
              {MOCK_MODELS.find((m) => m.id === result.selected_model_id)?.name || result.selected_model_id}
            </span>
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 text-sm font-medium text-stone-600 bg-stone-100 hover:bg-stone-200 rounded-lg transition-colors"
          >
            取消
          </button>
          <button
            onClick={() => selectedId && onConfirm(selectedId)}
            disabled={!selectedId}
            className="flex-1 px-4 py-2 text-sm font-medium text-white bg-lavender-600 hover:bg-lavender-700 disabled:bg-stone-300 disabled:cursor-not-allowed rounded-lg transition-colors"
            data-testid="override-confirm"
          >
            确认切换
          </button>
        </div>
      </div>
    </div>
  );
}
