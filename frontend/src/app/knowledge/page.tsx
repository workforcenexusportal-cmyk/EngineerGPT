"use client";

import { AnimatePresence, motion } from "framer-motion";
import {
  BookOpen,
  FileText,
  Loader2,
  Quote,
  Search,
  Sparkles,
  Trash2,
  Upload,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  ApiError,
  deleteDocument,
  listDocuments,
  searchKnowledge,
  uploadDocument,
  type AgentResult,
  type DocumentSummary,
} from "@/lib/api";
import { AuthGate } from "@/components/auth-gate";
import { GlassCard } from "@/components/glass-card";
import { useSession } from "@/lib/store";

export default function KnowledgePage() {
  return (
    <AuthGate>
      <KnowledgeHub />
    </AuthGate>
  );
}

function KnowledgeHub() {
  const token = useSession((s) => s.token);

  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [docsLoading, setDocsLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [result, setResult] = useState<AgentResult | null>(null);

  const refresh = useCallback(async () => {
    if (!token) return;
    setDocsLoading(true);
    try {
      setDocuments(await listDocuments(token));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load documents.");
    } finally {
      setDocsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const onUpload = async (file: File) => {
    if (!token) return;
    setUploading(true);
    setError(null);
    try {
      await uploadDocument(file, token);
      await refresh();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Upload failed.");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  };

  const onDelete = async (id: string) => {
    if (!token) return;
    try {
      await deleteDocument(id, token);
      setDocuments((docs) => docs.filter((d) => d.id !== id));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Delete failed.");
    }
  };

  const onSearch = async () => {
    if (!token || query.trim().length < 3) return;
    setSearching(true);
    setError(null);
    setResult(null);
    try {
      setResult(await searchKnowledge(query.trim(), 5, token));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Search failed.");
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6">
      <header>
        <h1 className="flex items-center gap-2 text-3xl font-extrabold tracking-tight">
          <BookOpen className="h-7 w-7 text-cyan" />
          Knowledge <span className="text-gradient">Hub</span>
        </h1>
        <p className="mt-1 text-sm text-gray-400">
          Grounded RAG search across your ingested documents. Answers cite only the
          retrieved corpus — no fabrication.
        </p>
      </header>

      {/* Search */}
      <GlassCard hover={false}>
        <div className="flex flex-col gap-3 sm:flex-row">
          <div className="flex flex-1 items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3">
            <Search className="h-4 w-4 shrink-0 text-gray-500" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && onSearch()}
              placeholder="Ask a question about your documents…"
              className="w-full bg-transparent py-2.5 text-sm text-gray-100 placeholder:text-gray-500 focus:outline-none"
            />
          </div>
          <button
            type="button"
            onClick={onSearch}
            disabled={searching || query.trim().length < 3}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan to-sky px-5 py-2.5 text-sm font-semibold text-black transition-transform enabled:hover:scale-[1.03] disabled:cursor-not-allowed disabled:opacity-40"
          >
            {searching ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4" />
            )}
            {searching ? "Searching…" : "Search"}
          </button>
        </div>
      </GlassCard>

      {error && (
        <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-300">
          {error}
        </p>
      )}

      <AnimatePresence mode="wait">
        {result && <ResultView key="result" result={result} />}
      </AnimatePresence>

      {/* Corpus */}
      <GlassCard hover={false}>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-200">
            Corpus{" "}
            <span className="text-gray-500">({documents.length} documents)</span>
          </h2>
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            disabled={uploading}
            className="inline-flex items-center gap-2 rounded-lg border border-white/15 bg-white/[0.04] px-3 py-1.5 text-xs font-semibold text-gray-200 transition-colors hover:border-cyan/40 disabled:opacity-40"
          >
            {uploading ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Upload className="h-3.5 w-3.5" />
            )}
            {uploading ? "Ingesting…" : "Upload document"}
          </button>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx,.pptx,.xlsx,.csv,.txt"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void onUpload(f);
            }}
          />
        </div>

        {docsLoading ? (
          <div className="flex items-center gap-2 py-6 text-sm text-gray-500">
            <Loader2 className="h-4 w-4 animate-spin" /> Loading corpus…
          </div>
        ) : documents.length === 0 ? (
          <p className="py-6 text-center text-sm text-gray-500">
            No documents yet. Upload a PDF, DOCX, PPTX, XLSX, CSV, or TXT to build the
            searchable corpus.
          </p>
        ) : (
          <ul className="flex flex-col divide-y divide-white/5">
            {documents.map((doc) => (
              <li key={doc.id} className="flex items-center gap-3 py-2.5 text-sm">
                <FileText className="h-4 w-4 shrink-0 text-cyan" />
                <span className="flex-1 truncate text-gray-200">{doc.filename}</span>
                <span className="shrink-0 text-xs text-gray-500">
                  {doc.chunk_count} chunks · {formatBytes(doc.size_bytes)}
                </span>
                <button
                  type="button"
                  onClick={() => onDelete(doc.id)}
                  aria-label={`Delete ${doc.filename}`}
                  className="shrink-0 rounded-lg p-1.5 text-gray-500 transition-colors hover:bg-rose-500/10 hover:text-rose-400"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </li>
            ))}
          </ul>
        )}
      </GlassCard>
    </div>
  );
}

function ResultView({ result }: { result: AgentResult }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
    >
      <GlassCard hover={false}>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-200">Answer</h3>
          <span className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] text-gray-400">
            {result.generated_by}
          </span>
        </div>
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-gray-100">
          {result.summary}
        </p>

        {result.insights.some((i) => i.citations.length > 0) && (
          <div className="mt-4 border-t border-white/5 pt-3">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-gray-500">
              Citations
            </p>
            <ul className="flex flex-col gap-1.5">
              {result.insights.flatMap((insight, idx) =>
                insight.citations.map((c, ci) => (
                  <li
                    key={`${idx}-${ci}`}
                    className="flex items-center gap-2 text-xs text-gray-400"
                  >
                    <Quote className="h-3 w-3 shrink-0 text-cyan" />
                    <span className="font-mono">{c.source}</span>
                    {c.locator && <span className="text-gray-600">· {c.locator}</span>}
                    <span className="ml-auto text-gray-600">
                      {(insight.confidence * 100).toFixed(0)}% conf.
                    </span>
                  </li>
                )),
              )}
            </ul>
          </div>
        )}
      </GlassCard>
    </motion.div>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
