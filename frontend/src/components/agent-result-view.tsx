"use client";

import { motion } from "framer-motion";
import { Quote } from "lucide-react";
import type { AgentResult } from "@/lib/api";
import { GlassCard } from "@/components/glass-card";

/** Uniform renderer for the evidence-backed AgentResult envelope. */
export function AgentResultView({ result }: { result: AgentResult }) {
  const hasCitations = result.insights.some((i) => i.citations.length > 0);
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="flex flex-col gap-4"
    >
      <GlassCard hover={false}>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-200">Summary</h3>
          <span className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] text-gray-400">
            {result.generated_by}
          </span>
        </div>
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-gray-100">
          {result.summary || "No summary returned."}
        </p>
      </GlassCard>

      {result.insights.length > 0 && (
        <GlassCard hover={false}>
          <h3 className="mb-3 text-sm font-semibold text-gray-200">Insights</h3>
          <ul className="flex flex-col gap-3">
            {result.insights.map((insight, i) => (
              <li
                key={i}
                className="rounded-xl border border-white/5 bg-white/[0.02] p-3"
              >
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm text-gray-100">{insight.statement}</p>
                  <span className="shrink-0 rounded-full bg-cyan/10 px-2 py-0.5 text-[10px] font-semibold text-cyan">
                    {(insight.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                {insight.citations.length > 0 && (
                  <ul className="mt-2 flex flex-wrap gap-2">
                    {insight.citations.map((c, ci) => (
                      <li
                        key={ci}
                        className="inline-flex items-center gap-1 rounded-lg border border-white/10 bg-black/30 px-2 py-1 text-[11px] text-gray-400"
                      >
                        <Quote className="h-3 w-3 text-cyan" />
                        <span className="font-mono">{c.source}</span>
                        {c.locator && <span className="text-gray-600">· {c.locator}</span>}
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        </GlassCard>
      )}

      {!hasCitations && result.insights.length === 0 && result.summary && (
        <p className="text-center text-xs text-gray-500">
          No structured insights were returned for this input.
        </p>
      )}
    </motion.div>
  );
}
