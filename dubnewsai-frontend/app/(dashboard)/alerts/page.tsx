"use client"

import { useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { BellRing, ShieldAlert, Siren, Zap } from "lucide-react"

import { AuthGuard } from "@/components/auth/AuthGuard"
import { LoadingSpinner } from "@/components/shared/LoadingSpinner"
import { PremiumPageHero } from "@/components/ui/premium-page-hero"
import { apiClient } from "@/lib/api/client"
import { useAlerts } from "@/lib/hooks/useAlerts"
import { formatDateTime, titleCase } from "@/lib/utils/formatters"

const alertTypes = [
  "price_above",
  "price_below",
  "price_change_percent",
  "keyword_match",
  "sentiment_threshold",
  "volume_spike",
  "new_article_category",
  "trend_detected"
]

interface AlertIntelligence {
  summary: {
    total: number
    active: number
    paused: number
    triggered: number
  }
  templates: {
    name: string
    alert_type: string
    frequency: string
    description: string
  }[]
  recent_triggers: {
    id: number
    alert_id: number
    alert_name: string
    message: string
    created_at: string
  }[]
}

export default function AlertsPage() {
  const { data: alerts, isLoading, createAlert, deleteAlert, toggleAlert, isCreating } = useAlerts()
  const { data: intelligence } = useQuery<AlertIntelligence>({
    queryKey: ["alerts", "intelligence"],
    queryFn: async () => {
      const response = await apiClient.get<AlertIntelligence>("/alerts/intelligence")
      return response.data
    }
  })

  const [name, setName] = useState("")
  const [alertType, setAlertType] = useState("keyword_match")
  const [symbol, setSymbol] = useState("")
  const [thresholdValue, setThresholdValue] = useState("")
  const [keywords, setKeywords] = useState("")
  const [category, setCategory] = useState("real_estate")
  const [frequency, setFrequency] = useState("instant")
  const [webhookUrl, setWebhookUrl] = useState("")
  const [emailEnabled, setEmailEnabled] = useState(false)

  const requiresSymbol = useMemo(
    () => ["price_above", "price_below", "price_change_percent", "volume_spike"].includes(alertType),
    [alertType]
  )
  const requiresThreshold = useMemo(
    () => ["price_above", "price_below", "price_change_percent", "sentiment_threshold", "volume_spike"].includes(alertType),
    [alertType]
  )
  const requiresKeywords = useMemo(
    () => ["keyword_match", "trend_detected"].includes(alertType),
    [alertType]
  )
  const requiresCategory = alertType === "new_article_category"

  return (
    <AuthGuard>
      <div className="space-y-8">
        <PremiumPageHero
          eyebrow="Alert engine"
          title="Alerts are now treated like an operator workflow, not a throwaway form."
          description="Build market, narrative, sentiment, and trend rules with enough structure to work as a real monitoring layer across the Dubai market and news stack."
          chips={["Price triggers", "Trend detection", "Sentiment thresholds", "Webhook ready"]}
          stats={[
            {
              label: "Configured rules",
              value: `${intelligence?.summary.total ?? alerts?.length ?? 0}`,
              hint: "All saved alert strategies"
            },
            {
              label: "Active rules",
              value: `${intelligence?.summary.active ?? alerts?.filter((alert) => alert.is_active).length ?? 0}`,
              hint: "Currently evaluating in the backend"
            },
            {
              label: "Triggered rules",
              value: `${intelligence?.summary.triggered ?? 0}`,
              hint: "Rules that have fired at least once"
            },
            {
              label: "Recent incidents",
              value: `${intelligence?.recent_triggers.length ?? 0}`,
              hint: "Most recent trigger log items"
            }
          ]}
          tone="rose"
        />

        <section className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
          <div className="space-y-6">
            <div className="panel-premium p-6 sm:p-8">
              <p className="story-kicker">Rule builder</p>
              <h2 className="mt-3 text-3xl font-semibold text-white">Compose an alert strategy</h2>
              <p className="mt-4 text-sm leading-7 text-white/56">
                Target symbols, news themes, trend acceleration, or sentiment thresholds and route them into notifications or webhooks.
              </p>
            </div>

            <form
              className="panel-premium grid gap-4 p-6 sm:p-8"
              onSubmit={async (event) => {
                event.preventDefault()
                await createAlert({
                  name,
                  alert_type: alertType,
                  symbol: requiresSymbol ? symbol || undefined : undefined,
                  threshold_value: requiresThreshold && thresholdValue ? Number(thresholdValue) : undefined,
                  keywords: requiresKeywords
                    ? keywords
                        .split(",")
                        .map((keyword) => keyword.trim())
                        .filter(Boolean)
                    : undefined,
                  category: requiresCategory ? category : undefined,
                  frequency,
                  notification_enabled: true,
                  email_enabled: emailEnabled,
                  webhook_url: webhookUrl || undefined
                })

                setName("")
                setSymbol("")
                setThresholdValue("")
                setKeywords("")
                setWebhookUrl("")
                setEmailEnabled(false)
              }}
            >
              <input
                required
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="Alert name"
                className="rounded-[1.4rem] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white outline-none transition placeholder:text-white/30 focus:border-cyan-300/30"
              />

              <div className="grid gap-4 md:grid-cols-2">
                <select
                  value={alertType}
                  onChange={(event) => setAlertType(event.target.value)}
                  className="rounded-[1.4rem] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-300/30"
                >
                  {alertTypes.map((type) => (
                    <option key={type} value={type} className="bg-slate-950">
                      {titleCase(type)}
                    </option>
                  ))}
                </select>

                <select
                  value={frequency}
                  onChange={(event) => setFrequency(event.target.value)}
                  className="rounded-[1.4rem] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white outline-none transition focus:border-cyan-300/30"
                >
                  {["instant", "hourly", "daily", "weekly"].map((item) => (
                    <option key={item} value={item} className="bg-slate-950">
                      {titleCase(item)}
                    </option>
                  ))}
                </select>
              </div>

              {requiresSymbol ? (
                <input
                  value={symbol}
                  onChange={(event) => setSymbol(event.target.value.toUpperCase())}
                  placeholder="Symbol (EMAAR)"
                  className="rounded-[1.4rem] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white outline-none transition placeholder:text-white/30 focus:border-emerald-300/30"
                />
              ) : null}

              {requiresThreshold ? (
                <input
                  value={thresholdValue}
                  onChange={(event) => setThresholdValue(event.target.value)}
                  placeholder="Threshold value"
                  className="rounded-[1.4rem] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white outline-none transition placeholder:text-white/30 focus:border-emerald-300/30"
                />
              ) : null}

              {requiresKeywords ? (
                <input
                  value={keywords}
                  onChange={(event) => setKeywords(event.target.value)}
                  placeholder="Keywords (comma separated)"
                  className="rounded-[1.4rem] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white outline-none transition placeholder:text-white/30 focus:border-amber-300/30"
                />
              ) : null}

              {requiresCategory ? (
                <input
                  value={category}
                  onChange={(event) => setCategory(event.target.value)}
                  placeholder="Category (real_estate)"
                  className="rounded-[1.4rem] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white outline-none transition placeholder:text-white/30 focus:border-cyan-300/30"
                />
              ) : null}

              <input
                value={webhookUrl}
                onChange={(event) => setWebhookUrl(event.target.value)}
                placeholder="Webhook URL (optional)"
                className="rounded-[1.4rem] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white outline-none transition placeholder:text-white/30 focus:border-violet-300/30"
              />

              <label className="flex items-center gap-3 rounded-[1.4rem] border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-white/74">
                <input type="checkbox" checked={emailEnabled} onChange={(event) => setEmailEnabled(event.target.checked)} className="h-4 w-4 rounded border-white/20 bg-transparent" />
                Enable email delivery for this alert
              </label>

              <button
                type="submit"
                disabled={isCreating}
                className="rounded-full bg-white px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-white/92 disabled:opacity-60"
              >
                {isCreating ? "Saving alert..." : "Create alert"}
              </button>
            </form>
          </div>

          <div className="space-y-6">
            <div className="panel-premium p-6 sm:p-8">
              <p className="story-kicker">Strategy templates</p>
              <h2 className="mt-3 text-3xl font-semibold text-white">Fast-start playbooks</h2>
              <div className="mt-6 space-y-3">
                {(intelligence?.templates || []).map((template) => (
                  <div key={template.name} className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-semibold text-white">{template.name}</div>
                      <span className="rounded-full border border-white/10 px-3 py-1 text-[10px] uppercase tracking-[0.22em] text-white/52">
                        {titleCase(template.frequency)}
                      </span>
                    </div>
                    <p className="mt-3 text-sm leading-7 text-white/56">{template.description}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="panel-premium p-6 sm:p-8">
              <p className="story-kicker">Recent trigger log</p>
              <h2 className="mt-3 text-3xl font-semibold text-white">What has fired lately</h2>
              <div className="mt-6 space-y-3">
                {(intelligence?.recent_triggers || []).length ? (
                  intelligence?.recent_triggers.map((trigger) => (
                    <div key={trigger.id} className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-4">
                      <div className="flex items-center justify-between gap-3">
                        <div className="text-sm font-semibold text-white">{trigger.alert_name}</div>
                        <div className="text-[10px] uppercase tracking-[0.22em] text-white/36">{formatDateTime(trigger.created_at)}</div>
                      </div>
                      <p className="mt-3 text-sm leading-7 text-white/56">{trigger.message}</p>
                    </div>
                  ))
                ) : (
                  <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-4 text-sm text-white/56">
                    No alert has triggered yet. As the rule set matures, this becomes the incident tape for your monitoring layer.
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        <section className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <CommandTile icon={BellRing} label="Rules total" value={`${intelligence?.summary.total ?? alerts?.length ?? 0}`} />
            <CommandTile icon={Zap} label="Active" value={`${intelligence?.summary.active ?? 0}`} />
            <CommandTile icon={Siren} label="Paused" value={`${intelligence?.summary.paused ?? 0}`} />
            <CommandTile icon={ShieldAlert} label="Triggered" value={`${intelligence?.summary.triggered ?? 0}`} />
          </div>

          <div>
            <p className="story-kicker">Current rules</p>
            <h2 className="mt-3 text-3xl font-semibold text-white">Your live automation layer</h2>
          </div>

          {isLoading ? (
            <div className="panel-deep p-6">
              <LoadingSpinner />
            </div>
          ) : (
            <div className="grid gap-4 lg:grid-cols-2">
              {alerts?.map((alert) => (
                <article key={alert.id} className="panel-premium space-y-4 p-5">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h3 className="text-lg font-semibold text-white">{alert.name}</h3>
                      <p className="mt-1 text-sm text-white/48">
                        {titleCase(alert.alert_type)} | {titleCase(alert.status)}
                      </p>
                    </div>
                    <span className={`rounded-full px-3 py-1 text-xs font-medium ${alert.is_active ? "bg-emerald-500/10 text-emerald-300" : "bg-white/10 text-white/62"}`}>
                      {alert.is_active ? "Active" : "Paused"}
                    </span>
                  </div>

                  <div className="grid gap-3 text-sm text-white/64 md:grid-cols-2">
                    <div>Symbol: {alert.symbol || "N/A"}</div>
                    <div>Threshold: {alert.threshold_value ?? "N/A"}</div>
                    <div>Frequency: {titleCase(alert.frequency)}</div>
                    <div>Triggers: {alert.trigger_count}</div>
                    <div>Last fired: {alert.last_triggered_at ? formatDateTime(alert.last_triggered_at) : "Never"}</div>
                    <div>Created: {formatDateTime(alert.created_at)}</div>
                  </div>

                  <div className="flex gap-3">
                    <button
                      type="button"
                      onClick={() => toggleAlert(alert.id)}
                      className="rounded-full border border-white/10 px-4 py-2 text-sm text-white/78 transition hover:text-white"
                    >
                      {alert.is_active ? "Pause" : "Activate"}
                    </button>
                    <button
                      type="button"
                      onClick={() => deleteAlert(alert.id)}
                      className="rounded-full border border-red-500/30 px-4 py-2 text-sm text-red-300 transition hover:border-red-400/50 hover:text-red-200"
                    >
                      Delete
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </AuthGuard>
  )
}

function CommandTile({
  icon: Icon,
  label,
  value
}: {
  icon: typeof BellRing
  label: string
  value: string
}) {
  return (
    <article className="panel-premium p-5">
      <div className="inline-flex items-center gap-2 text-[10px] uppercase tracking-[0.3em] text-white/40">
        <Icon className="h-3.5 w-3.5 text-cyan-200" />
        {label}
      </div>
      <div className="mt-4 text-3xl font-semibold text-white">{value}</div>
    </article>
  )
}
