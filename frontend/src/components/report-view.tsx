"use client";

import { motion } from "framer-motion";
import { AlertTriangle, CheckCircle2, Quote } from "lucide-react";
import type { TestReport } from "@/lib/api";
import { GlassCard } from "@/components/glass-card";
import { cn } from "@/lib/utils";

const SEVERITY_TONE: Record<string, string> = {
  high: "border-rose-500/40 text-rose-300",
  medium: "border-amber-500/40 text-amber-300",
  low: "border-sky-500/40 text-sky-300",
};

export function ReportView({ report }: { report: TestReport }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col gap-5"
    >
      <GlassCard>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-xl font-bold">{report.title}</h2>
          <span className="text-xs text-gray-500">
            {report.row_count} rows · {report.column_count} signals · {report.generated_by}
          </span>
        </div>
        <p className="mt-3 text-sm leading-relaxed text-gray-300">{report.executive_summary}</p>
      </GlassCard>

      {report.charts.length > 0 && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {report.charts.map((c, i) => (
            <GlassCard key={c.title} delay={i * 0.05}>
              <p className="mb-2 text-sm font-semibold text-gray-200">{c.title}</p>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={`data:image/png;base64,${c.image_base64}`}
                alt={c.title}
                className="w-full rounded-lg"
              />
            </GlassCard>
          ))}
        </div>
      )}

      {report.findings.length > 0 && (
        <GlassCard>
          <h3 className="mb-3 text-lg font-semibold">Key Findings</h3>
          <ul className="flex flex-col gap-2">
            {report.findings.map((f, i) => (
              <li key={i} className="flex items-start gap-3 text-sm text-gray-300">
                <Quote className="mt-0.5 h-4 w-4 shrink-0 text-cyan" />
                <span className="flex-1">
                  {f.statement}
                  <span className="ml-2 text-[11px] text-gray-500">
                    ({Math.round(f.confidence * 100)}% · {f.citation})
                  </span>
                </span>
              </li>
            ))}
          </ul>
        </GlassCard>
      )}

      {report.anomalies.length > 0 && (
        <GlassCard>
          <h3 className="mb-3 flex items-center gap-2 text-lg font-semibold">
            <AlertTriangle className="h-4 w-4 text-amber-400" /> Anomaly Detection
          </h3>
          <div className="flex flex-col gap-2">
            {report.anomalies.map((a, i) => (
              <div
                key={i}
                className={cn(
                  "rounded-xl border bg-white/[0.02] px-3 py-2 text-sm",
                  SEVERITY_TONE[a.severity] ?? "border-white/10 text-gray-300",
                )}
              >
                <span className="font-semibold">{a.column}</span>{" "}
                <span className="text-[11px] uppercase opacity-80">[{a.severity}]</span>
                <p className="mt-0.5 text-gray-400">{a.description}</p>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <GlassCard>
          <h3 className="mb-3 text-lg font-semibold">Conclusions</h3>
          <ul className="flex flex-col gap-2">
            {report.conclusions.map((c, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-cyan" />
                {c}
              </li>
            ))}
          </ul>
        </GlassCard>
        <GlassCard>
          <h3 className="mb-3 text-lg font-semibold">Recommendations</h3>
          <ul className="flex flex-col gap-2">
            {report.recommendations.map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                <ArrowIcon />
                {r}
              </li>
            ))}
          </ul>
        </GlassCard>
      </div>
    </motion.div>
  );
}

function ArrowIcon() {
  return <span className="mt-0.5 shrink-0 text-violet">▸</span>;
}
