export const MODEL_CONTEXT_OPTIONS = [
  { value: 128 * 1024, label: '128K' },
  { value: 256 * 1024, label: '256K' },
  { value: 512 * 1024, label: '512K' },
  { value: 1024 * 1024, label: '1M' },
] as const;

export const DEFAULT_MODEL_CONTEXT_TOKENS = MODEL_CONTEXT_OPTIONS[0].value;

export function formatTokenCount(tokens: number): string {
  const option = MODEL_CONTEXT_OPTIONS.find((item) => item.value === tokens);
  return option?.label ?? `${Math.round(tokens / 1024)}K`;
}
