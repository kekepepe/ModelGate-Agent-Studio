import { beforeEach, describe, expect, it, vi } from 'vitest';
import { fireEvent, render, screen } from '@testing-library/react';
import KnowledgeSourcesPanel from '../KnowledgeSourcesPanel';
import {
  useCreateKnowledgeSource, useDisableKnowledgeSource, useKnowledgeChunks,
  useKnowledgeDocuments, useKnowledgeSources, useSyncKnowledgeSource,
} from '../../hooks/useKnowledge';

vi.mock('../../hooks/useKnowledge', () => ({
  useKnowledgeSources: vi.fn(),
  useCreateKnowledgeSource: vi.fn(),
  useSyncKnowledgeSource: vi.fn(),
  useDisableKnowledgeSource: vi.fn(),
  useKnowledgeDocuments: vi.fn(),
  useKnowledgeChunks: vi.fn(),
}));

const createMutate = vi.fn();
const syncMutate = vi.fn();
const disableMutate = vi.fn();

describe('KnowledgeSourcesPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useKnowledgeSources).mockReturnValue({
      data: [{
        id: 's-1', name: 'Architecture Docs', type: 'workspace', uri: 'docs/architecture',
        workspace_scope: 'docs/architecture/**', status: 'active', sync_policy: 'manual',
        metadata: {}, last_synced_at: '2026-07-18T09:00:00Z',
      }],
      isLoading: false, isError: false,
    } as ReturnType<typeof useKnowledgeSources>);
    vi.mocked(useCreateKnowledgeSource).mockReturnValue({ mutate: createMutate, isPending: false, isError: false } as unknown as ReturnType<typeof useCreateKnowledgeSource>);
    vi.mocked(useSyncKnowledgeSource).mockReturnValue({ mutate: syncMutate, isPending: false } as unknown as ReturnType<typeof useSyncKnowledgeSource>);
    vi.mocked(useDisableKnowledgeSource).mockReturnValue({ mutate: disableMutate, isPending: false } as unknown as ReturnType<typeof useDisableKnowledgeSource>);
    vi.mocked(useKnowledgeDocuments).mockReturnValue({
      data: [{ id: 'd-1', source_id: 's-1', path: 'docs/architecture/runtime.md', title: 'runtime.md', checksum: 'abc', status: 'indexed', metadata: {}, chunk_count: 1, indexed_at: '2026-07-18T09:00:00Z' }],
      isLoading: false,
    } as unknown as ReturnType<typeof useKnowledgeDocuments>);
    vi.mocked(useKnowledgeChunks).mockReturnValue({
      data: [{ id: 'c-1', document_id: 'd-1', chunk_index: 0, content: 'Plan versions are immutable.', token_count: 8, status: 'active', metadata: {} }],
      isLoading: false, isError: false,
    } as unknown as ReturnType<typeof useKnowledgeChunks>);
  });

  it('shows source scope, sync state, documents and chunks', () => {
    render(<KnowledgeSourcesPanel />);
    expect(screen.getByText('Architecture Docs')).toBeInTheDocument();
    expect(screen.getByText(/Scope: docs\/architecture\/\*\*/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'View documents' }));
    expect(screen.getByText('docs/architecture/runtime.md')).toBeInTheDocument();
    expect(screen.getByText('1 chunks')).toBeInTheDocument();
    fireEvent.click(screen.getByText('docs/architecture/runtime.md'));
    expect(screen.getByText('Plan versions are immutable.')).toBeInTheDocument();
    expect(screen.getByText('8 tokens')).toBeInTheDocument();
  });

  it('connects, syncs and disables a source', () => {
    render(<KnowledgeSourcesPanel />);
    fireEvent.change(screen.getByLabelText('Knowledge source name'), { target: { value: 'Runtime docs' } });
    fireEvent.change(screen.getByLabelText('Knowledge source path'), { target: { value: 'docs/runtime' } });
    fireEvent.change(screen.getByLabelText('Knowledge source scope'), { target: { value: 'docs/runtime/**' } });
    fireEvent.click(screen.getByRole('button', { name: 'Connect source' }));
    expect(createMutate).toHaveBeenCalledWith(expect.objectContaining({ name: 'Runtime docs', uri: 'docs/runtime', workspace_scope: 'docs/runtime/**' }), expect.any(Object));
    fireEvent.click(screen.getByRole('button', { name: 'Sync' }));
    expect(syncMutate).toHaveBeenCalledWith('s-1');
    fireEvent.click(screen.getByRole('button', { name: 'Disable' }));
    expect(disableMutate).toHaveBeenCalledWith('s-1');
  });
});
