"use client";

import { motion } from "framer-motion";
import { Search, Sparkles } from "lucide-react";
import { FormEvent, useState } from "react";

/** Dynamic dashboard command surface; this remains local until a query endpoint is wired. */
export function CommandBar() {
  const [value, setValue] = useState("");
  const [status, setStatus] = useState<"ready" | "queued">("ready");

  const onSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    if (!value.trim() || status === "queued") return;
    setStatus("queued");
    window.setTimeout(() => setStatus("ready"), 900);
  };

  return (
    <motion.form
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      onSubmit={onSubmit}
      className="glass flex flex-col gap-3 p-3 sm:flex-row sm:items-center"
      aria-label="EngineerGPT command bar"
    >
      <div className="flex min-w-0 flex-1 items-center gap-3 px-2">
        <Search className="h-5 w-5 shrink-0 text-cyan" aria-hidden="true" />
        <label htmlFor="command-query" className="sr-only">Ask EngineerGPT</label>
        <input
          id="command-query"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder="Ask the engineering network…"
          className="w-full bg-transparent text-sm text-gray-100 placeholder:text-gray-500 focus:outline-none"
          autoComplete="off"
        />
      </div>
      <button
        type="submit"
        disabled={!value.trim() || status === "queued"}
        className="cyber-button inline-flex items-center justify-center gap-2 bg-cyan px-4 py-2 text-xs font-bold text-[#071014] disabled:cursor-not-allowed disabled:opacity-40"
      >
        <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
        {status === "queued" ? "Queued" : "Execute"}
      </button>
      <span className="hud-kicker px-2 text-[10px]" aria-live="polite">
        {status === "queued" ? "PROCESSING" : "READY"}
      </span>
    </motion.form>
  );
}
