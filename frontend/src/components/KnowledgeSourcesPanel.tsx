import { useState } from 'react';
import type { FormEvent } from 'react';
import {
  useCreateKnowledgeSource, useDisableKnowledgeSource, useKnowledgeChunks,
  useKnowledgeDocuments, useKnowledgeSources, useSyncKnowledgeSource,
} from '../hooks/useKnowledge';
import type { KnowledgeDocument, KnowledgeSource, KnowledgeSourceInput } from '../types/knowledge';

const EMPTY_FORM: KnowledgeSourceInput = {
  name: '', type: 'workspace', uri: '', workspace_scope: '', sync_policy: 'manual',
};

function readableDate(value?: string | null) {
  return value ? new Date(value).toLocaleString() : 'Never';
}

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : 'Request failed';
}

export default function KnowledgeSourcesPanel() {
  const sources = useKnowledgeSources();
  const createSource = useCreateKnowledgeSource();
  const [form, setForm] = useState<KnowledgeSourceInput>(EMPTY_FORM);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    createSource.mutate(form, { onSuccess: () => setForm(EMPTY_FORM) });
  };

  return (
    <div className="space-y-4">
      <form onSubmit={submit} className="rounded-xl border border-stone-200 bg-white p-4">
        <div className="mb-3">
          <h2 className="text-sm font-semibold text-stone-900">Connect Workspace Knowledge</h2>
          <p className="mt-1 text-xs text-stone-500">Paths must stay inside the configured Workspace Root. Sync is checksum-based and incremental.</p>
        </div>
        <div className="grid gap-3 md:grid-cols-2">
          <label className="text-xs font-medium text-stone-600">Name
            <input aria-label="Knowledge source name" required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} className="mt-1 w-full rounded-lg border border-stone-200 px-3 py-2 text-sm" placeholder="Architecture docs" />
          </label>
          <label className="text-xs font-medium text-stone-600">Workspace path
            <input aria-label="Knowledge source path" required value={form.uri} onChange={(event) => setForm({ ...form, uri: event.target.value })} className="mt-1 w-full rounded-lg border border-stone-200 px-3 py-2 text-sm" placeholder="docs/architecture" />
          </label>
          <label className="text-xs font-medium text-stone-600">Permission scope
            <input aria-label="Knowledge source scope" value={form.workspace_scope || ''} onChange={(event) => setForm({ ...form, workspace_scope: event.target.value })} className="mt-1 w-full rounded-lg border border-stone-200 px-3 py-2 text-sm" placeholder="docs/architecture/**" />
          </label>
          <label className="text-xs font-medium text-stone-600">Source type
            <select aria-label="Knowledge source type" value={form.type} onChange={(event) => setForm({ ...form, type: event.target.value as KnowledgeSourceInput['type'] })} className="mt-1 w-full rounded-lg border border-stone-200 px-3 py-2 text-sm">
              <option value="workspace">Workspace folder</option>
              <option value="project_document">Project document</option>
            </select>
          </label>
        </div>
        <div className="mt-3 flex items-center justify-between gap-3">
          <span className="text-xs text-stone-400">Manual sync · supported text/code files · max 1 MB each</span>
          <button disabled={createSource.isPending} className="rounded-lg bg-stone-900 px-4 py-2 text-xs font-medium text-white disabled:opacity-40">{createSource.isPending ? 'Connecting…' : 'Connect source'}</button>
        </div>
        {createSource.isError && <p role="alert" className="mt-2 text-xs text-red-600">{errorMessage(createSource.error)}</p>}
      </form>

      {sources.isLoading && <div className="h-24 animate-pulse rounded-xl bg-stone-200" />}
      {sources.isError && <p role="alert" className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{errorMessage(sources.error)}</p>}
      {!sources.isLoading && !sources.isError && sources.data?.length === 0 && <div className="rounded-xl border border-dashed border-stone-300 p-10 text-center text-sm text-stone-400">No Knowledge Sources connected.</div>}
      {sources.data?.map((source) => <SourceCard key={source.id} source={source} />)}
    </div>
  );
}

function SourceCard({ source }: { source: KnowledgeSource }) {
  const [expanded, setExpanded] = useState(false);
  const documents = useKnowledgeDocuments(source.id, expanded);
  const syncSource = useSyncKnowledgeSource();
  const disableSource = useDisableKnowledgeSource();
  const busy = syncSource.isPending || disableSource.isPending;
  const actionError = syncSource.error || disableSource.error;
  const statusColor = source.status === 'active' ? 'bg-green-100 text-green-700' : source.status === 'error' ? 'bg-red-100 text-red-700' : 'bg-stone-100 text-stone-600';

  return (
    <article className="rounded-xl border border-stone-200 bg-white p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-sm font-semibold text-stone-900">{source.name}</h3>
            <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${statusColor}`}>{source.status}</span>
            <span className="rounded bg-stone-100 px-1.5 py-0.5 text-[10px] text-stone-500">{source.type}</span>
          </div>
          <p className="mt-1 break-all font-mono text-xs text-stone-600">{source.uri}</p>
          <p className="mt-1 text-xs text-stone-500">Scope: {source.workspace_scope || 'Workspace Root'} · Last sync: {readableDate(source.last_synced_at)}</p>
          {source.error_message && <p role="alert" className="mt-2 text-xs text-red-600">{source.error_message}</p>}
        </div>
        <div className="flex gap-2">
          <button onClick={() => setExpanded((value) => !value)} className="rounded-lg border border-stone-200 px-3 py-1.5 text-xs text-stone-700">{expanded ? 'Hide documents' : 'View documents'}</button>
          <button onClick={() => syncSource.mutate(source.id)} disabled={busy || source.status === 'disabled'} className="rounded-lg bg-stone-800 px-3 py-1.5 text-xs text-white disabled:opacity-40">Sync</button>
          {source.status !== 'disabled' && <button onClick={() => disableSource.mutate(source.id)} disabled={busy} className="rounded-lg border border-red-200 px-3 py-1.5 text-xs text-red-600 disabled:opacity-40">Disable</button>}
        </div>
      </div>
      {actionError && <p role="alert" className="mt-2 text-xs text-red-600">{errorMessage(actionError)}</p>}
      {syncSource.data && <p className="mt-2 text-xs text-green-700">Sync complete: {syncSource.data.added} added, {syncSource.data.updated} updated, {syncSource.data.deleted} deleted, {syncSource.data.unchanged} unchanged.</p>}
      {expanded && <DocumentList documents={documents.data || []} loading={documents.isLoading} error={documents.error} />}
    </article>
  );
}

function DocumentList({ documents, loading, error }: { documents: KnowledgeDocument[]; loading: boolean; error: unknown }) {
  if (loading) return <p className="mt-4 text-xs text-stone-400">Loading documents…</p>;
  if (error) return <p role="alert" className="mt-4 text-xs text-red-600">{errorMessage(error)}</p>;
  if (!documents.length) return <p className="mt-4 text-xs text-stone-400">No indexed documents. Run Sync first.</p>;
  return <div className="mt-4 divide-y divide-stone-100 border-t border-stone-100">{documents.map((document) => <DocumentRow key={document.id} document={document} />)}</div>;
}

function DocumentRow({ document }: { document: KnowledgeDocument }) {
  const [expanded, setExpanded] = useState(false);
  const chunks = useKnowledgeChunks(document.id, expanded);
  return (
    <div className="py-3">
      <button onClick={() => setExpanded((value) => !value)} className="flex w-full items-center justify-between gap-3 text-left">
        <span className="min-w-0"><span className="block truncate text-xs font-medium text-stone-700">{document.path}</span><span className="mt-0.5 block text-[10px] text-stone-400">{document.status} · indexed {readableDate(document.indexed_at)}</span></span>
        <span className="shrink-0 rounded bg-stone-100 px-2 py-1 text-[10px] text-stone-600">{document.chunk_count} chunks</span>
      </button>
      {expanded && <div className="mt-2 space-y-2 pl-3">
        {chunks.isLoading && <p className="text-xs text-stone-400">Loading chunks…</p>}
        {chunks.isError && <p role="alert" className="text-xs text-red-600">{errorMessage(chunks.error)}</p>}
        {chunks.data?.map((chunk) => <div key={chunk.id} className="rounded-lg bg-stone-50 p-3"><div className="mb-1 flex gap-2 text-[10px] text-stone-400"><span>Chunk {chunk.chunk_index}</span><span>{chunk.token_count} tokens</span><span>{chunk.status}</span>{chunk.symbol_path && <span>{chunk.symbol_path}</span>}</div><p className="whitespace-pre-wrap text-xs text-stone-600">{chunk.content}</p></div>)}
      </div>}
    </div>
  );
}
