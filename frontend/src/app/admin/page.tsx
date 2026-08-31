"use client";

import { Loader2, ShieldCheck } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  getPlatformStats,
  listOrganizations,
  listUsers,
  setOrgPlan,
  type OrgRow,
  type PlatformStats,
  type UserRow,
} from "@/lib/api";
import { AuthGate } from "@/components/auth-gate";
import { GlassCard } from "@/components/glass-card";
import { useSession } from "@/lib/store";

const PLAN_OPTIONS = ["free", "pro", "team"];

export default function AdminPage() {
  return (
    <AuthGate>
      <AdminGuard />
    </AuthGate>
  );
}

function AdminGuard() {
  const user = useSession((s) => s.user);
  if (user && !user.is_superuser) {
    return (
      <div className="mx-auto mt-16 max-w-md text-center">
        <GlassCard hover={false}>
          <ShieldCheck className="mx-auto h-8 w-8 text-magenta" />
          <h1 className="mt-3 text-lg font-bold">Restricted area</h1>
          <p className="mt-1 text-sm text-gray-400">
            The platform admin panel is available to superusers only.
          </p>
        </GlassCard>
      </div>
    );
  }
  return <Admin />;
}

function StatTile({ label, value }: { label: string; value: number }) {
  return (
    <GlassCard hover={false}>
      <p className="hud-kicker text-[10px]">{label}</p>
      <p className="mt-2 font-mono text-3xl font-semibold text-white">
        {value.toLocaleString()}
      </p>
    </GlassCard>
  );
}

function Admin() {
  const token = useSession((s) => s.token);
  const [stats, setStats] = useState<PlatformStats | null>(null);
  const [orgs, setOrgs] = useState<OrgRow[]>([]);
  const [users, setUsers] = useState<UserRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const [s, o, u] = await Promise.all([
        getPlatformStats(token),
        listOrganizations(token),
        listUsers(token),
      ]);
      setStats(s);
      setOrgs(o);
      setUsers(u);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load admin data.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const onPlanChange = async (orgId: string, plan: string) => {
    if (!token) return;
    try {
      const updated = await setOrgPlan(orgId, plan, token);
      setOrgs((current) => current.map((o) => (o.id === orgId ? updated : o)));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to update plan.");
    }
  };

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-6">
      <header className="flex flex-col gap-2 border-l-2 border-magenta pl-4">
        <p className="hud-kicker">PLATFORM // CONTROL</p>
        <h1 className="display-font flex items-center gap-2 text-3xl font-bold tracking-tight">
          <ShieldCheck className="h-7 w-7 text-magenta" />
          Admin <span className="text-gradient">Console</span>
        </h1>
        <p className="text-sm text-gray-400">
          Platform-wide tenants, users, and usage. Superuser access only.
        </p>
      </header>

      {error && (
        <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-300">
          {error}
        </p>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-10 text-gray-400">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" /> Loading console…
        </div>
      ) : (
        <>
          {stats && (
            <section className="grid grid-cols-2 gap-3 lg:grid-cols-5">
              <StatTile label="Organizations" value={stats.organizations} />
              <StatTile label="Users" value={stats.users} />
              <StatTile label="Documents" value={stats.documents} />
              <StatTile label="Analyses (total)" value={stats.analyses_total} />
              <StatTile label="Analyses (month)" value={stats.analyses_this_month} />
            </section>
          )}

          <GlassCard hover={false}>
            <h2 className="display-font mb-3 text-xl font-semibold">Organizations</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-white/10 text-[11px] uppercase tracking-wide text-gray-500">
                    <th className="py-2 pr-4">Name</th>
                    <th className="py-2 pr-4">Members</th>
                    <th className="py-2 pr-4">Docs</th>
                    <th className="py-2 pr-4">Status</th>
                    <th className="py-2 pr-4">Plan</th>
                  </tr>
                </thead>
                <tbody>
                  {orgs.map((org) => (
                    <tr key={org.id} className="border-b border-white/5">
                      <td className="py-2 pr-4 text-gray-100">
                        {org.name}
                        <span className="block text-[10px] text-gray-500">{org.slug}</span>
                      </td>
                      <td className="py-2 pr-4 text-gray-300">{org.members}</td>
                      <td className="py-2 pr-4 text-gray-300">{org.documents}</td>
                      <td className="py-2 pr-4 text-gray-400">
                        {org.subscription_status ?? "—"}
                      </td>
                      <td className="py-2 pr-4">
                        <select
                          value={org.plan}
                          onChange={(e) => onPlanChange(org.id, e.target.value)}
                          className="border border-white/10 bg-white/[0.03] px-2 py-1 text-xs text-gray-100 focus:border-cyan/40 focus:outline-none"
                        >
                          {PLAN_OPTIONS.map((p) => (
                            <option key={p} value={p} className="bg-[#0a0a0f]">
                              {p}
                            </option>
                          ))}
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassCard>

          <GlassCard hover={false}>
            <h2 className="display-font mb-3 text-xl font-semibold">Users</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-white/10 text-[11px] uppercase tracking-wide text-gray-500">
                    <th className="py-2 pr-4">Email</th>
                    <th className="py-2 pr-4">Name</th>
                    <th className="py-2 pr-4">Role</th>
                    <th className="py-2 pr-4">Superuser</th>
                    <th className="py-2 pr-4">Joined</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-b border-white/5">
                      <td className="py-2 pr-4 text-gray-100">{u.email}</td>
                      <td className="py-2 pr-4 text-gray-300">{u.full_name || "—"}</td>
                      <td className="py-2 pr-4 text-gray-300">{u.role}</td>
                      <td className="py-2 pr-4 text-gray-400">{u.is_superuser ? "yes" : "—"}</td>
                      <td className="py-2 pr-4 text-gray-500">
                        {new Date(u.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </GlassCard>
        </>
      )}
    </div>
  );
}
