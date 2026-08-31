"use client";

import { AnimatePresence, motion } from "framer-motion";
import { History, Loader2, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  deleteHistory,
  getHistory,
  listHistory,
  type HistoryDetail,
  type HistoryItem,
} from "@/lib/api";
import { AgentResultView } from "@/components/agent-result-view";
import { AuthGate } from "@/components/auth-gate";
import { GlassCard } from "@/components/glass-card";
import { useSession } from "@/lib/store";

const MODULE_LABELS: Record<string, string> = {
  failure_analysis: "Failure Analysis",
  requirements_intel: "Requirements",
  meeting_prep: "Meeting Prep",
  design_review: "Design Review",
  knowledge_hub: "Knowledge Hub",
};

export default function HistoryPage() {
  return (
    <AuthGate>
      <HistoryView />
    </AuthGate>
  );
}

function HistoryView() {
  const token = useSession((s) => s.token);
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<HistoryDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const refresh = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      setItems(await listHistory(token, { limit: 100 }));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load history.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const onOpen = async (id: string) => {
    if (!token) return;
    setDetailLoading(true);
    try {
      setSelected(await getHistory(id, token));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load record.");
    } finally {
      setDetailLoading(false);
    }
  };

  const onDelete = async (id: string) => {
    if (!token) return;
    try {
      await deleteHistory(id, token);
      setItems((current) => current.filter((i) => i.id !== id));
      if (selected?.id === id) setSelected(null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to delete record.");
    }
  };

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-6">
      <header className="flex flex-col gap-2 border-l-2 border-cyan pl-4">
        <p className="hud-kicker">ARCHIVE // ANALYSIS LOG</p>
        <h1 className="display-font flex items-center gap-2 text-3xl font-bold tracking-tight">
          <History className="h-7 w-7 text-cyan" />
          Analysis <span className="text-gradient">History</span>
        </h1>
        <p className="text-sm text-gray-400">
          Every analysis your workspace runs is saved here — searchable, reviewable, and shareable.
        </p>
      </header>

      {error && (
        <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-300">
          {error}
        </p>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <GlassCard hover={false}>
            {loading ? (
              <div className="flex items-center justify-center py-10 text-gray-400">
                <Loader2 className="mr-2 h-5 w-5 animate-spin" /> Loading…
              </div>
            ) : items.length === 0 ? (
              <p className="py-10 text-center text-sm text-gray-500">
                No analyses yet. Run a module to populate your history.
              </p>
            ) : (
              <ul className="flex flex-col gap-2">
                {items.map((item) => (
                  <li key={item.id} className="flex items-stretch gap-2">
                    <button
                      type="button"
                      onClick={() => onOpen(item.id)}
                      className={`flex-1 border-l-2 px-3 py-2 text-left transition-colors ${
                        selected?.id === item.id
                          ? "border-cyan bg-cyan/10"
                          : "border-white/10 hover:border-cyan/50 hover:bg-white/[0.03]"
                      }`}
                    >
                      <p className="truncate text-sm text-gray-100">{item.title || "Untitled"}</p>
                      <p className="mt-0.5 text-[11px] uppercase tracking-wide text-gray-500">
                        {MODULE_LABELS[item.module] ?? item.module} ·{" "}
                        {new Date(item.created_at).toLocaleString()}
                      </p>
                    </button>
                    <button
                      type="button"
                      onClick={() => onDelete(item.id)}
                      aria-label="Delete record"
                      className="px-2 text-gray-500 transition-colors hover:bg-magenta/10 hover:text-magenta"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </GlassCard>
        </div>

        <div className="lg:col-span-3">
          {detailLoading ? (
            <GlassCard hover={false}>
              <div className="flex items-center justify-center py-10 text-gray-400">
                <Loader2 className="mr-2 h-5 w-5 animate-spin" /> Loading record…
              </div>
            </GlassCard>
          ) : (
            <AnimatePresence mode="wait">
              {selected ? (
                <motion.div
                  key={selected.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                >
                  <AgentResultView result={selected.result} />
                </motion.div>
              ) : (
                <GlassCard hover={false}>
                  <p className="py-10 text-center text-sm text-gray-500">
                    Select a record to view its full analysis.
                  </p>
                </GlassCard>
              )}
            </AnimatePresence>
          )}
        </div>
      </div>
    </div>
  );
}
