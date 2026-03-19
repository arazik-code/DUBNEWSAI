"use client"

import { AlertCircle, CheckCircle2, RefreshCw, ShieldAlert } from "lucide-react"
import { useEffect, useState } from "react"

import { AuthGuard } from "@/components/auth/AuthGuard"
import { LoadingSpinner } from "@/components/shared/LoadingSpinner"
import { apiClient } from "@/lib/api/client"
import { useAuth } from "@/lib/hooks/useAuth"
import { formatDateTime, titleCase } from "@/lib/utils/formatters"

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
  const [providers, setProviders] = useState<ProviderRow[]>([])
  const [summary, setSummary] = useState<ProviderSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const isAdmin = user?.role === "admin"

  const fetchData = async (silent = false) => {
    if (!silent) {
      setRefreshing(true)
    }
    try {
      const [providersResponse, summaryResponse] = await Promise.all([
        apiClient.get<ProviderRow[]>("/admin/providers/"),
        apiClient.get<ProviderSummary>("/admin/providers/dashboard-summary"),
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
      void fetchData(true)
    }, 30000)

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

  if (loading) {
    return (
      <AuthGuard>
        <div className="panel p-8">
          <LoadingSpinner />
        </div>
      </AuthGuard>
    )
  }

  if (!isAdmin) {
    return (
      <AuthGuard>
        <div className="panel flex items-start gap-4 p-6">
          <ShieldAlert className="mt-1 h-6 w-6 text-red-400" />
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-red-400">Restricted</p>
            <h1 className="mt-2 text-2xl font-display font-semibold text-slate-950 dark:text-white">Admin access required</h1>
            <p className="mt-3 text-sm text-slate-600 dark:text-slate-400">
              This view exposes provider controls and operational health. It is available to admin accounts only.
            </p>
          </div>
        </div>
      </AuthGuard>
    )
  }

  return (
    <AuthGuard>
      <div className="space-y-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] text-cyber-500">Admin</p>
            <h1 className="text-3xl font-display font-semibold text-slate-950 dark:text-white">Provider Management</h1>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
              Monitor provider health, rate-limit posture, and live ingestion reliability.
            </p>
          </div>
          <button
            type="button"
            onClick={() => void fetchData()}
            className="inline-flex items-center gap-2 rounded-2xl border border-white/10 px-4 py-2 text-sm text-slate-700 transition hover:border-gold-400 hover:text-gold-500 disabled:opacity-60 dark:text-slate-200"
            disabled={refreshing}
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        {summary && (
          <section className="grid gap-4 md:grid-cols-4">
            <article className="panel p-5">
              <div className="text-xs uppercase tracking-[0.2em] text-slate-500">Total Providers</div>
              <div className="mt-3 text-3xl font-semibold text-slate-950 dark:text-white">{summary.total_providers}</div>
            </article>
            <article className="panel p-5">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs uppercase tracking-[0.2em] text-slate-500">Healthy</div>
                  <div className="mt-3 text-3xl font-semibold text-emerald-500">{summary.healthy}</div>
                </div>
                <CheckCircle2 className="h-8 w-8 text-emerald-400" />
              </div>
            </article>
            <article className="panel p-5">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs uppercase tracking-[0.2em] text-slate-500">Unhealthy</div>
                  <div className="mt-3 text-3xl font-semibold text-red-500">{summary.unhealthy}</div>
                </div>
                <AlertCircle className="h-8 w-8 text-red-400" />
              </div>
            </article>
            <article className="panel p-5">
              <div className="text-xs uppercase tracking-[0.2em] text-slate-500">Calls Today</div>
              <div className="mt-3 text-3xl font-semibold text-slate-950 dark:text-white">{summary.total_calls_today}</div>
            </article>
          </section>
        )}

        {summary && (
          <section className="grid gap-4 lg:grid-cols-3">
            {Object.entries(summary.by_type).map(([type, stats]) => (
              <article key={type} className="panel p-5">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-500">{titleCase(type)} Sources</div>
                <div className="mt-4 grid grid-cols-3 gap-3 text-sm">
                  <div>
                    <div className="text-slate-500">Total</div>
                    <div className="mt-1 text-lg font-semibold text-slate-950 dark:text-white">{stats.total}</div>
                  </div>
                  <div>
                    <div className="text-slate-500">Enabled</div>
                    <div className="mt-1 text-lg font-semibold text-emerald-500">{stats.enabled}</div>
                  </div>
                  <div>
                    <div className="text-slate-500">Healthy</div>
                    <div className="mt-1 text-lg font-semibold text-cyber-500">{stats.healthy}</div>
                  </div>
                </div>
              </article>
            ))}
          </section>
        )}

        <section className="panel overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-white/10 text-sm">
              <thead className="bg-slate-950/50 text-left text-xs uppercase tracking-[0.2em] text-slate-400">
                <tr>
                  <th className="px-4 py-3">Provider</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Circuit</th>
                  <th className="px-4 py-3">Health</th>
                  <th className="px-4 py-3">Success</th>
                  <th className="px-4 py-3">Calls</th>
                  <th className="px-4 py-3">Last Success</th>
                  <th className="px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {providers.map((provider) => {
                  const liveHealth = Math.round(provider.live_health_score)
                  const circuitClass =
                    provider.live_circuit_state === "closed"
                      ? "text-emerald-400"
                      : provider.live_circuit_state === "half_open"
                        ? "text-amber-400"
                        : "text-red-400"

                  return (
                    <tr key={provider.id} className="bg-transparent">
                      <td className="px-4 py-4 align-top">
                        <div className="font-semibold text-slate-950 dark:text-white">{provider.name}</div>
                        <div className="mt-1 text-xs text-slate-500">Priority {provider.priority}</div>
                        {provider.base_url && <div className="mt-1 text-xs text-slate-500">{provider.base_url}</div>}
                      </td>
                      <td className="px-4 py-4 align-top text-slate-600 dark:text-slate-300">{titleCase(provider.type)}</td>
                      <td className={`px-4 py-4 align-top font-medium ${circuitClass}`}>
                        {titleCase(provider.live_circuit_state.replace("_", " "))}
                      </td>
                      <td className="px-4 py-4 align-top">
                        <div className="w-32 rounded-full bg-slate-800/60">
                          <div
                            className={`h-2 rounded-full ${liveHealth >= 70 ? "bg-emerald-500" : liveHealth >= 40 ? "bg-amber-500" : "bg-red-500"}`}
                            style={{ width: `${Math.max(0, Math.min(100, liveHealth))}%` }}
                          />
                        </div>
                        <div className="mt-2 text-xs text-slate-500">{liveHealth}%</div>
                      </td>
                      <td className="px-4 py-4 align-top text-slate-600 dark:text-slate-300">{provider.success_rate.toFixed(1)}%</td>
                      <td className="px-4 py-4 align-top text-slate-600 dark:text-slate-300">
                        <div>{provider.total_calls}</div>
                        <div className="mt-1 text-xs text-slate-500">
                          {provider.successful_calls} ok / {provider.failed_calls} fail
                        </div>
                      </td>
                      <td className="px-4 py-4 align-top text-slate-600 dark:text-slate-300">
                        {provider.last_success_at ? formatDateTime(provider.last_success_at) : "Never"}
                      </td>
                      <td className="px-4 py-4 align-top">
                        <div className="flex flex-wrap gap-2">
                          <button
                            type="button"
                            onClick={() => void toggleProvider(provider.id)}
                            className="rounded-2xl border border-white/10 px-3 py-2 text-xs text-slate-700 transition hover:border-gold-400 hover:text-gold-500 dark:text-slate-200"
                          >
                            {provider.is_enabled ? "Disable" : "Enable"}
                          </button>
                          {provider.live_circuit_state === "open" && (
                            <button
                              type="button"
                              onClick={() => void resetCircuit(provider.id)}
                              className="rounded-2xl border border-red-500/30 px-3 py-2 text-xs text-red-400 transition hover:border-red-400 hover:text-red-300"
                            >
                              Reset Circuit
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </AuthGuard>
  )
}
