"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Download, FileUp, Loader2, Sparkles } from "lucide-react";
import { useRef, useState } from "react";
import {
  analyzeTestReport,
  ApiError,
  exportTestReportPdf,
  type TestReport,
} from "@/lib/api";
import { GlassCard } from "@/components/glass-card";
import { ReportView } from "@/components/report-view";
import { useSession } from "@/lib/store";

export default function TestReportPage() {
  const token = useSession((s) => s.token) ?? undefined;
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [report, setReport] = useState<TestReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    setReport(null);
    try {
      const result = await analyzeTestReport(file, title || file.name, token);
      setReport(result);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Analysis failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const onExport = async () => {
    if (!file) return;
    setExporting(true);
    try {
      const blob = await exportTestReportPdf(file, title || file.name, token);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${title || "test-report"}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Export failed.");
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6">
      <header>
        <h1 className="text-3xl font-extrabold tracking-tight">
          Test Report <span className="text-gradient">Agent</span>
        </h1>
        <p className="mt-1 text-sm text-gray-400">
          Upload CSV or XLSX measurement data to generate a professional engineering report.
        </p>
      </header>

      <GlassCard hover={false}>
        <div className="flex flex-col gap-4">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Report title (e.g. Battery Bench Run 42)"
            className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm text-gray-100 placeholder:text-gray-500 focus:border-cyan/40 focus:outline-none"
          />

          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="flex items-center justify-center gap-3 rounded-xl border border-dashed border-white/15 bg-white/[0.02] px-4 py-8 text-sm text-gray-400 transition-colors hover:border-cyan/40 hover:text-gray-200"
          >
            <FileUp className="h-5 w-5 text-cyan" />
            {file ? (
              <span className="text-gray-200">{file.name}</span>
            ) : (
              <span>Click to select a .csv or .xlsx file</span>
            )}
          </button>
          <input
            ref={inputRef}
            type="file"
            accept=".csv,.xlsx"
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={onAnalyze}
              disabled={!file || loading}
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan to-sky px-5 py-2.5 text-sm font-semibold text-black transition-transform enabled:hover:scale-[1.03] disabled:cursor-not-allowed disabled:opacity-40"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              {loading ? "Analyzing…" : "Generate Report"}
            </button>

            {report && (
              <button
                type="button"
                onClick={onExport}
                disabled={exporting}
                className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/[0.04] px-5 py-2.5 text-sm font-semibold text-gray-200 transition-colors hover:border-cyan/40"
              >
                {exporting ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
                Export PDF
              </button>
            )}
          </div>

          {error && (
            <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-300">
              {error}
            </p>
          )}
        </div>
      </GlassCard>

      <AnimatePresence mode="wait">
        {loading && <LoadingSkeleton />}
        {report && !loading && <ReportView report={report} />}
      </AnimatePresence>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex flex-col gap-4"
    >
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="glass h-28 animate-pulse rounded-2xl bg-white/[0.03]"
          style={{ animationDelay: `${i * 120}ms` }}
        />
      ))}
    </motion.div>
  );
}
