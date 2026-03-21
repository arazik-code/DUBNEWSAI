"use client"

import { AlertCircle, CheckCircle2, RefreshCw, ShieldAlert } from "lucide-react"
import { useEffect, useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"

import { AuthGuard } from "@/components/auth/AuthGuard"
import { ActionStatus } from "@/components/shared/ActionStatus"
import { EmptyStatePanel } from "@/components/shared/EmptyStatePanel"
import { LoadingSpinner } from "@/components/shared/LoadingSpinner"
import { PremiumPageHero } from "@/components/ui/premium-page-hero"
import { apiClient } from "@/lib/api/client"
import { useAuth } from "@/lib/hooks/useAuth"
import { useAdminFeatureAccess, useAdminFeatureAccessUsers } from "@/lib/hooks/useEnterprise"
import { formatDateTime, titleCase } from "@/lib/utils/formatters"
import type { FeatureAccess } from "@/types"

interface ProviderSummary {
  total_providers: number
  healthy: number
  unhealthy: number
  by_type: Record<string, { total: number; enabled: number; healthy: number }>
  total_calls_today: number
  timestamp: string
}

interface ProviderRow {
  id: number
  name: string
  type: string
  priority: number
  is_enabled: boolean
  is_healthy: boolean
  reliability_score: number
  total_calls: number
  successful_calls: number
  failed_calls: number
  success_rate: number
  last_success_at: string | null
  last_failure_at: string | null
  circuit_state: string
  rate_limit_per_day: number | null
  cost_per_call: number
  base_url: string | null
  live_health_score: number
  live_circuit_state: string
}

export default function ProvidersAdminPage() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [providers, setProviders] = useState<ProviderRow[]>([])
  const [summary, setSummary] = useState<ProviderSummary | null>(null)
  const [selectedUserId, setSelectedUserId] = useState<number | undefined>(undefined)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const isAdmin = user?.role === "admin"
  const { data: accessUsers = [] } = useAdminFeatureAccessUsers()
  const { data: selectedUserFeatures = [] } = useAdminFeatureAccess(selectedUserId)

  const fetchData = async (silent = false) => {
    if (!silent) {
      setRefreshing(true)
    }
    try {
      const [providersResponse, summaryResponse] = await Promise.all([
        apiClient.get<ProviderRow[]>("/admin/providers/"),
        apiClient.get<ProviderSummary>("/admin/providers/dashboard-summary")
      ])
      setProviders(providersResponse.data)
      setSummary(summaryResponse.data)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    if (!isAdmin) {
      setLoading(false)
      return
    }

    void fetchData(true)
    const timer = window.setInterval(() => {
      if (!document.hidden) {
        void fetchData(true)
      }
    }, 60000)

    return () => window.clearInterval(timer)
  }, [isAdmin])

  const toggleProvider = async (providerId: number) => {
    await apiClient.patch(`/admin/providers/${providerId}/toggle`)
    await fetchData()
  }

  const resetCircuit = async (providerId: number) => {
    await apiClient.post(`/admin/providers/${providerId}/reset-circuit`)
    await fetchData()
  }

  useEffect(() => {
    if (!selectedUserId && accessUsers.length) {
      const firstNonAdmin = accessUsers.find((item) => item.role !== "admin") || accessUsers[0]
      setSelectedUserId(firstNonAdmin.id)
    }
  }, [accessUsers, selectedUserId])

  const updateUserFeatureAccess = useMutation({
    mutationFn: async ({ userId, featureKey, enabled }: { userId: number; featureKey: string; enabled: boolean }) => {
      const { data } = await apiClient.put<FeatureAccess[]>(`/admin/feature-access/users/${userId}/${featureKey}`, {
        enabled
      })
      return data
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin", "feature-access", selectedUserId] })
      await queryClient.invalidateQueries({ queryKey: ["feature-access"] })
    }
  })

  if (loading) {
    return (
      <AuthGuard>
        <div className="panel-deep p-8">
          <LoadingSpinner />
        </div>
      </AuthGuard>
    )
  }

  if (!isAdmin) {
    return (
      <AuthGuard>
        <div className="panel-premium flex items-start gap-4 p-6">
          <ShieldAlert className="mt-1 h-6 w-6 text-red-300" />
          <div>
            <p className="story-kicker">Restricted</p>
            <h1 className="mt-3 text-2xl font-semibold text-white">Admin access required</h1>
            <p className="mt-3 text-sm leading-7 text-white/56">
              This view exposes provider controls and operational health. It is available to admin accounts only.
            </p>
          </div>
        </div>
      </AuthGuard>
    )
  }

  return (
    <AuthGuard>
      <div className="space-y-8">
        <PremiumPageHero
          eyebrow="Provider operations"
          title="Operational health should feel like mission control, not a detached admin table."
          description="Monitor source health, circuit state, and failure patterns from one operations surface so provider reliability stays visible and actionable across the platform."
          chips={["Live health", "Circuit control", "Source quality", "Operational insight"]}
          stats={[
            {
              label: "Total providers",
              value: `${summary?.total_providers ?? 0}`,
              hint: "Configured across news, market, and macro layers"
            },
            {
              label: "Healthy",
              value: `${summary?.healthy ?? 0}`,
              hint: "Currently delivering within acceptable behavior"
            },
            {
              label: "Unhealthy",
              value: `${summary?.unhealthy ?? 0}`,
              hint: "Need attention or are being protected by circuit rules"
            },
            {
              label: "Calls today",
              value: `${summary?.total_calls_today ?? 0}`,
              hint: "Platform fetch attempts in the current day window"
            }
          ]}
          tone="rose"
          actions={[
            {
              label: refreshing ? "Refreshing..." : "Refresh providers",
              href: "#providers-table",
              variant: "ghost"
            }
          ]}
        />

        <div className="flex justify-end">
          <button
            type="button"
            onClick={() => void fetchData()}
            className="inline-flex items-center gap-2 rounded-full border border-white/10 px-4 py-2 text-sm text-white/78 transition hover:text-white disabled:opacity-60"
            disabled={refreshing}
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        {summary ? (
          <section className="grid gap-4 md:grid-cols-4">
            <SummaryCard title="Total providers" value={`${summary.total_providers}`} />
            <SummaryCard title="Healthy" value={`${summary.healthy}`} accent="text-emerald-300" icon={<CheckCircle2 className="h-7 w-7 text-emerald-300" />} />
            <SummaryCard title="Unhealthy" value={`${summary.unhealthy}`} accent="text-red-300" icon={<AlertCircle className="h-7 w-7 text-red-300" />} />
            <SummaryCard title="Calls today" value={`${summary.total_calls_today}`} />
          </section>
        ) : null}

        {summary ? (
          <section className="grid gap-4 lg:grid-cols-3">
            {Object.entries(summary.by_type).map(([type, stats]) => (
              <article key={type} className="panel-premium p-5">
                <div className="text-[10px] uppercase tracking-[0.28em] text-white/40">{titleCase(type)} sources</div>
                <div className="mt-4 grid grid-cols-3 gap-3 text-sm">
                  <Metric title="Total" value={`${stats.total}`} />
                  <Metric title="Enabled" value={`${stats.enabled}`} accent="text-emerald-300" />
                  <Metric title="Healthy" value={`${stats.healthy}`} accent="text-cyan-100" />
                </div>
              </article>
            ))}
          </section>
        ) : null}

        <section className="panel-premium p-6 sm:p-8">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="story-kicker">User feature access</p>
              <h2 className="mt-3 text-3xl font-semibold text-white">Grant premium workspaces user by user</h2>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-white/56">
                Public users keep News and Market. Signed-in users start with Analytics, Alerts, Settings, and their core workspace. Use this panel to unlock advanced modules like Investor Suite, Competitors, Executive, and Teams for specific accounts.
              </p>
            </div>
          </div>
          <div className="mt-6 grid gap-6 xl:grid-cols-[0.82fr_1.18fr]">
            <div className="space-y-3">
              {accessUsers.length ? (
                accessUsers.map((account) => (
                  <button
                    key={account.id}
                    type="button"
                    onClick={() => setSelectedUserId(account.id)}
                    className={`w-full rounded-[1.4rem] border p-4 text-left transition ${
                      selectedUserId === account.id ? "border-cyan-300/35 bg-cyan-300/[0.08]" : "border-white/10 bg-white/[0.03]"
                    }`}
                  >
                    <div className="text-sm font-semibold text-white">{account.full_name || account.email}</div>
                    <div className="mt-1 text-xs text-white/44">{account.email}</div>
                    <div className="mt-3 text-[10px] uppercase tracking-[0.22em] text-white/38">{titleCase(account.role)}</div>
                  </button>
                ))
              ) : (
                <EmptyStatePanel
                  title="No standard users are available yet."
                  description="Create or invite a non-admin user first, then grant premium workspace access from this panel."
                />
              )}
            </div>

            <div className="space-y-4">
              {selectedUserFeatures.filter((feature) => feature.grantable).map((feature) => (
                <article key={feature.feature_key} className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="text-sm font-semibold text-white">{feature.label}</div>
                      <div className="mt-1 text-[10px] uppercase tracking-[0.24em] text-white/38">{titleCase(feature.category)}</div>
                    </div>
                    <button
                      type="button"
                      onClick={() =>
                        selectedUserId &&
                        updateUserFeatureAccess.mutate({
                          userId: selectedUserId,
                          featureKey: feature.feature_key,
                          enabled: !feature.has_access
                        })
                      }
                      className={`rounded-full border px-3 py-2 text-xs transition ${
                        feature.has_access
                          ? "border-emerald-400/30 text-emerald-200 hover:border-emerald-300/50"
                          : "border-white/10 text-white/62 hover:text-white"
                      }`}
                      disabled={updateUserFeatureAccess.isPending || !selectedUserId}
                    >
                      {feature.has_access ? "Granted" : "Grant access"}
                    </button>
                  </div>
                  <p className="mt-4 text-sm leading-7 text-white/56">
                    {feature.description || "Feature access is managed here."}
                  </p>
                  <div className="mt-4 text-xs text-white/42">
                    {feature.granted_by_admin
                      ? "Enabled by admin grant for this user."
                      : "Not part of the default signed-in access bundle."}
                  </div>
                </article>
              ))}
              <ActionStatus
                isPending={updateUserFeatureAccess.isPending}
                isSuccess={updateUserFeatureAccess.isSuccess}
                error={updateUserFeatureAccess.error}
                successMessage="User access updated."
              />
            </div>
          </div>
        </section>

        <section id="providers-table" className="panel-premium overflow-hidden">
          {providers.length ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-white/10 text-sm">
                <thead className="bg-white/[0.03] text-left text-[10px] uppercase tracking-[0.28em] text-white/42">
                  <tr>
                    <th className="px-4 py-4">Provider</th>
                    <th className="px-4 py-4">Type</th>
                    <th className="px-4 py-4">Circuit</th>
                    <th className="px-4 py-4">Health</th>
                    <th className="px-4 py-4">Success</th>
                    <th className="px-4 py-4">Calls</th>
                    <th className="px-4 py-4">Last success</th>
                    <th className="px-4 py-4">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/6">
                  {providers.map((provider) => {
                    const liveHealth = Math.round(provider.live_health_score)
                    const circuitClass =
                      provider.live_circuit_state === "closed"
                        ? "text-emerald-300"
                        : provider.live_circuit_state === "half_open"
                          ? "text-amber-200"
                          : "text-red-300"

                    return (
                      <tr key={provider.id}>
                        <td className="px-4 py-4 align-top">
                          <div className="font-semibold text-white">{provider.name}</div>
                          <div className="mt-1 text-xs text-white/40">Priority {provider.priority}</div>
                          {provider.base_url ? <div className="mt-1 text-xs text-white/32">{provider.base_url}</div> : null}
                        </td>
                        <td className="px-4 py-4 align-top text-white/64">{titleCase(provider.type)}</td>
                        <td className={`px-4 py-4 align-top font-medium ${circuitClass}`}>{titleCase(provider.live_circuit_state.replace("_", " "))}</td>
                        <td className="px-4 py-4 align-top">
                          <div className="w-32 rounded-full bg-white/10">
                            <div
                              className={`h-2 rounded-full ${liveHealth >= 70 ? "bg-emerald-400" : liveHealth >= 40 ? "bg-amber-300" : "bg-red-400"}`}
                              style={{ width: `${Math.max(0, Math.min(100, liveHealth))}%` }}
                            />
                          </div>
                          <div className="mt-2 text-xs text-white/40">{liveHealth}%</div>
                        </td>
                        <td className="px-4 py-4 align-top text-white/64">{provider.success_rate.toFixed(1)}%</td>
                        <td className="px-4 py-4 align-top text-white/64">
                          <div>{provider.total_calls}</div>
                          <div className="mt-1 text-xs text-white/40">
                            {provider.successful_calls} ok / {provider.failed_calls} fail
                          </div>
                        </td>
                        <td className="px-4 py-4 align-top text-white/64">
                          {provider.last_success_at ? formatDateTime(provider.last_success_at) : "Never"}
                        </td>
                        <td className="px-4 py-4 align-top">
                          <div className="flex flex-wrap gap-2">
                            <button
                              type="button"
                              onClick={() => void toggleProvider(provider.id)}
                              className="rounded-full border border-white/10 px-3 py-2 text-xs text-white/78 transition hover:text-white"
                            >
                              {provider.is_enabled ? "Disable" : "Enable"}
                            </button>
                            {provider.live_circuit_state === "open" ? (
                              <button
                                type="button"
                                onClick={() => void resetCircuit(provider.id)}
                                className="rounded-full border border-red-500/30 px-3 py-2 text-xs text-red-300 transition hover:border-red-400/50 hover:text-red-200"
                              >
                                Reset Circuit
                              </button>
                            ) : null}
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-6">
              <EmptyStatePanel
                title="Provider controls will appear here."
                description="Once providers are configured, this table becomes the live operational control surface for circuit state, health, and throughput."
              />
            </div>
          )}
        </section>
      </div>
    </AuthGuard>
  )
}

function SummaryCard({
  title,
  value,
  accent,
  icon
}: {
  title: string
  value: string
  accent?: string
  icon?: React.ReactNode
}) {
  return (
    <article className="panel-premium p-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="text-[10px] uppercase tracking-[0.28em] text-white/40">{title}</div>
          <div className={`mt-4 text-3xl font-semibold ${accent || "text-white"}`}>{value}</div>
        </div>
        {icon}
      </div>
    </article>
  )
}

function Metric({ title, value, accent }: { title: string; value: string; accent?: string }) {
  return (
    <div>
      <div className="text-white/40">{title}</div>
      <div className={`mt-2 text-lg font-semibold ${accent || "text-white"}`}>{value}</div>
    </div>
  )
}
