"use client";

import { CheckCircle2, CreditCard, Loader2, Sparkles } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  createCheckout,
  getContext,
  listPlans,
  openBillingPortal,
  type PlanCatalogItem,
} from "@/lib/api";
import { AuthGate } from "@/components/auth-gate";
import { GlassCard } from "@/components/glass-card";
import { useSession } from "@/lib/store";

export default function BillingPage() {
  return (
    <AuthGate>
      <Billing />
    </AuthGate>
  );
}

function formatLimit(value: number): string {
  return value < 0 ? "Unlimited" : value.toLocaleString();
}

function Billing() {
  const token = useSession((s) => s.token);
  const { context, setContext } = useSession();
  const [plans, setPlans] = useState<PlanCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  const currentPlan = context?.organization?.plan ?? context?.plan.key ?? "free";

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      setPlans(await listPlans());
      if (token) setContext(await getContext(token));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load plans.");
    } finally {
      setLoading(false);
    }
  }, [token, setContext]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const onUpgrade = async (plan: string) => {
    if (!token) return;
    setBusy(plan);
    setError(null);
    try {
      const url = await createCheckout(plan, token);
      window.location.href = url;
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not start checkout.");
      setBusy(null);
    }
  };

  const onManage = async () => {
    if (!token) return;
    setBusy("portal");
    setError(null);
    try {
      const url = await openBillingPortal(token);
      window.location.href = url;
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not open billing portal.");
      setBusy(null);
    }
  };

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6">
      <header className="flex flex-col gap-2 border-l-2 border-cyan pl-4">
        <p className="hud-kicker">BILLING // PLANS</p>
        <h1 className="display-font flex items-center gap-2 text-3xl font-bold tracking-tight">
          <CreditCard className="h-7 w-7 text-cyan" />
          Choose your <span className="text-gradient">plan</span>
        </h1>
        <p className="text-sm text-gray-400">
          Scale from a free workspace to unlimited engineering intelligence. Upgrade any time.
        </p>
      </header>

      {error && (
        <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-300">
          {error}
        </p>
      )}

      {context && (
        <GlassCard hover={false}>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="hud-kicker text-[10px]">CURRENT PLAN</p>
              <p className="mt-1 text-xl font-semibold text-white">
                {context.plan.label}
              </p>
              <p className="mt-1 text-xs text-gray-400">
                {context.usage.analyses_this_month} / {formatLimit(context.plan.monthly_analyses)}{" "}
                analyses this month · {context.usage.documents} /{" "}
                {formatLimit(context.plan.max_documents)} documents
              </p>
            </div>
            {currentPlan !== "free" && (
              <button
                type="button"
                onClick={onManage}
                disabled={busy === "portal"}
                className="cyber-button inline-flex items-center gap-2 border border-cyan/40 px-4 py-2 text-sm font-semibold text-cyan disabled:opacity-40"
              >
                {busy === "portal" ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <CreditCard className="h-4 w-4" />
                )}
                Manage billing
              </button>
            )}
          </div>
        </GlassCard>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-10 text-gray-400">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" /> Loading plans…
        </div>
      ) : (
        <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {plans.map((plan) => {
            const isCurrent = plan.key === currentPlan;
            const highlight = plan.key === "pro";
            return (
              <GlassCard key={plan.key} hover={false} className={highlight ? "border-cyan/50" : ""}>
                <div className="flex h-full flex-col">
                  <div className="flex items-center justify-between">
                    <h2 className="display-font text-2xl font-semibold">{plan.label}</h2>
                    {highlight && (
                      <span className="border border-cyan/40 px-2 py-0.5 text-[10px] font-semibold text-cyan">
                        POPULAR
                      </span>
                    )}
                  </div>
                  <p className="mt-3">
                    <span className="font-mono text-4xl font-bold text-white">
                      ${plan.price_usd_month}
                    </span>
                    <span className="text-sm text-gray-500"> / month</span>
                  </p>
                  <ul className="mt-5 flex flex-1 flex-col gap-2 text-sm text-gray-300">
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-cyan" />
                      {formatLimit(plan.monthly_analyses)} analyses / month
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-cyan" />
                      {formatLimit(plan.max_documents)} documents
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-cyan" />
                      {formatLimit(plan.max_members)} team members
                    </li>
                    {plan.features.map((f) => (
                      <li key={f} className="flex items-center gap-2">
                        <CheckCircle2 className="h-4 w-4 text-cyan" />
                        {f}
                      </li>
                    ))}
                  </ul>

                  <div className="mt-6">
                    {isCurrent ? (
                      <span className="block border border-white/10 px-4 py-2 text-center text-sm text-gray-400">
                        Current plan
                      </span>
                    ) : plan.purchasable ? (
                      <button
                        type="button"
                        onClick={() => onUpgrade(plan.key)}
                        disabled={busy === plan.key}
                        className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-cyan to-sky px-4 py-2.5 text-sm font-semibold text-black transition-transform enabled:hover:scale-[1.02] disabled:opacity-40"
                      >
                        {busy === plan.key ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Sparkles className="h-4 w-4" />
                        )}
                        Upgrade
                      </button>
                    ) : plan.key === "free" ? (
                      <span className="block border border-white/10 px-4 py-2 text-center text-sm text-gray-500">
                        Included
                      </span>
                    ) : (
                      <span className="block border border-white/10 px-4 py-2 text-center text-xs text-gray-500">
                        Contact us to enable
                      </span>
                    )}
                  </div>
                </div>
              </GlassCard>
            );
          })}
        </section>
      )}
    </div>
  );
}
