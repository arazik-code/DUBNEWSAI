"use client"

import { useEffect, useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Bell, Building2, KeyRound, Palette, ShieldCheck, SlidersHorizontal, Waves, Workflow } from "lucide-react"

import { AuthGuard } from "@/components/auth/AuthGuard"
import { LoadingSpinner } from "@/components/shared/LoadingSpinner"
import { PremiumPageHero } from "@/components/ui/premium-page-hero"
import { apiClient } from "@/lib/api/client"
import { useAuth } from "@/lib/hooks/useAuth"
import { useApiKeys, useWhiteLabelConfig } from "@/lib/hooks/useEnterprise"
import { useNotifications } from "@/lib/hooks/useNotifications"
import { useNotificationStore } from "@/lib/store/notificationStore"
import { formatDateTime, titleCase } from "@/lib/utils/formatters"

export default function SettingsPage() {
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const { data: notifications, isLoading, markRead, markAllRead, markingAllRead } = useNotifications()
  const { data: apiKeys = [] } = useApiKeys()
  const { data: whiteLabel } = useWhiteLabelConfig()
  const realtimeNotifications = useNotificationStore((state) => state.items)
  const hydrateNotifications = useNotificationStore((state) => state.hydrate)
  const [apiKeyForm, setApiKeyForm] = useState({ name: "Enterprise feed key", rate_limit_per_hour: 250 })
  const [whiteLabelForm, setWhiteLabelForm] = useState({
    company_name: whiteLabel?.company_name || "DUBNEWSAI Intelligence",
    logo_url: whiteLabel?.logo_url || "",
    primary_color: whiteLabel?.primary_color || "#22d3ee",
    secondary_color: whiteLabel?.secondary_color || "#f59e0b",
    custom_domain: whiteLabel?.custom_domain || "",
    subdomain: whiteLabel?.subdomain || "",
    enabled_features: (whiteLabel?.enabled_features || ["portfolio", "analytics", "news"]).join(", "),
    api_enabled: whiteLabel?.api_enabled ?? true,
    api_rate_limit: whiteLabel?.api_rate_limit || 250,
    is_active: whiteLabel?.is_active ?? true
  })
  const [plaintextKey, setPlaintextKey] = useState<string | null>(null)

  useEffect(() => {
    if (notifications?.length) {
      hydrateNotifications(notifications)
    }
  }, [hydrateNotifications, notifications])

  useEffect(() => {
    if (whiteLabel) {
      setWhiteLabelForm({
        company_name: whiteLabel.company_name,
        logo_url: whiteLabel.logo_url || "",
        primary_color: whiteLabel.primary_color || "#22d3ee",
        secondary_color: whiteLabel.secondary_color || "#f59e0b",
        custom_domain: whiteLabel.custom_domain || "",
        subdomain: whiteLabel.subdomain || "",
        enabled_features: (whiteLabel.enabled_features || ["portfolio", "analytics", "news"]).join(", "),
        api_enabled: whiteLabel.api_enabled,
        api_rate_limit: whiteLabel.api_rate_limit,
        is_active: whiteLabel.is_active
      })
    }
  }, [whiteLabel])

  const createApiKey = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post("/settings/api-keys", apiKeyForm)
      return data as { plaintext_key: string }
    },
    onSuccess: async (data) => {
      setPlaintextKey(data.plaintext_key)
      await queryClient.invalidateQueries({ queryKey: ["settings", "api-keys"] })
    }
  })

  const saveWhiteLabel = useMutation({
    mutationFn: async () => {
      await apiClient.put("/settings/white-label", {
        ...whiteLabelForm,
        enabled_features: whiteLabelForm.enabled_features
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean)
      })
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["settings", "white-label"] })
    }
  })

  const unreadCount = realtimeNotifications.filter((notification) => !notification.is_read).length

  return (
    <AuthGuard>
      <div className="space-y-8">
        <PremiumPageHero
          eyebrow="Workspace settings"
          title="Settings should feel like command infrastructure, not a demo page."
          description="DUBNEWSAI settings now frame identity, notification posture, workspace behavior, and operating preferences as part of a real enterprise workspace."
          chips={["Operator identity", "Inbox posture", "Workspace policy", "Delivery controls"]}
          stats={[
            {
              label: "Unread inbox",
              value: `${unreadCount}`,
              hint: "Live items still waiting for review"
            },
            {
              label: "Workspace role",
              value: titleCase(user?.role || "user"),
              hint: "Current permission posture"
            },
            {
              label: "Notification stream",
              value: `${realtimeNotifications.length}`,
              hint: "Hydrated across API and realtime events"
            },
            {
              label: "Workspace mode",
              value: "Live monitoring",
              hint: "Signals continue updating in the background"
            }
          ]}
          tone="violet"
        />

        <section className="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
          <div className="space-y-6">
            <article className="panel-premium p-6 sm:p-8">
              <p className="story-kicker">Operator identity</p>
              <h2 className="mt-4 text-3xl font-semibold text-white">Workspace profile</h2>
              <div className="mt-6 grid gap-4 rounded-[1.8rem] border border-white/10 bg-white/[0.03] p-5">
                <ProfileRow label="Name" value={user?.full_name || "Not set"} />
                <ProfileRow label="Email" value={user?.email || "Unknown"} />
                <ProfileRow label="Role" value={titleCase(user?.role || "user")} />
              </div>
            </article>

            <article className="panel-premium p-6 sm:p-8">
              <p className="story-kicker">Workspace posture</p>
              <h2 className="mt-4 text-3xl font-semibold text-white">Operational defaults</h2>
              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <SettingTile icon={Workflow} label="Alert delivery" value="Realtime + webhook ready" text="Designed for immediate operator response and automation handoff." />
                <SettingTile icon={Waves} label="Data cadence" value="Continuous refresh" text="News and market layers keep refreshing in the background." />
                <SettingTile icon={ShieldCheck} label="Security posture" value="Authenticated workspace" text="Role-aware access and operator identity are surfaced as first-class context." />
                <SettingTile icon={Building2} label="Deployment mode" value="Production linked" text="Frontend and backend are attached to active deployment infrastructure." />
              </div>
            </article>

            <article className="panel-premium p-6 sm:p-8">
              <p className="story-kicker">API access</p>
              <h2 className="mt-4 text-3xl font-semibold text-white">Issue and manage public API keys</h2>
              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <label className="block">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">Key name</div>
                  <input className="input-premium" value={apiKeyForm.name} onChange={(event) => setApiKeyForm((current) => ({ ...current, name: event.target.value }))} />
                </label>
                <label className="block">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">Hourly limit</div>
                  <input type="number" className="input-premium" value={apiKeyForm.rate_limit_per_hour} onChange={(event) => setApiKeyForm((current) => ({ ...current, rate_limit_per_hour: Number(event.target.value) }))} />
                </label>
              </div>
              <button type="button" onClick={() => createApiKey.mutate()} className="action-premium mt-5">
                <KeyRound className="h-4 w-4" />
                Create API key
              </button>
              {plaintextKey ? (
                <div className="mt-5 rounded-[1.4rem] border border-cyan-300/20 bg-cyan-300/[0.06] p-4">
                  <div className="text-[10px] uppercase tracking-[0.28em] text-cyan-100/70">New key</div>
                  <div className="mt-3 break-all text-sm text-white">{plaintextKey}</div>
                </div>
              ) : null}
              <div className="mt-6 space-y-3">
                {apiKeys.map((item) => (
                  <div key={item.id} className="rounded-[1.4rem] border border-white/10 bg-white/[0.03] p-4">
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <div className="text-sm font-semibold text-white">{item.name}</div>
                        <div className="mt-1 text-xs text-white/42">{item.rate_limit_per_hour} req/hr · {item.total_requests} total requests</div>
                      </div>
                      <div className="text-xs text-white/46">{item.last_used_at ? formatDateTime(item.last_used_at) : "Never used"}</div>
                    </div>
                  </div>
                ))}
              </div>
            </article>
          </div>

          <div className="space-y-6">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="story-kicker">Inbox controls</p>
                <h2 className="mt-3 text-3xl font-semibold text-white">Notification command surface</h2>
              </div>
              <button
                type="button"
                onClick={() => markAllRead()}
                disabled={markingAllRead}
                className="rounded-full border border-white/10 px-4 py-2 text-sm text-white/76 transition hover:text-white disabled:opacity-60"
              >
                Mark all read
              </button>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <ControlPill icon={Bell} label="Unread" value={`${unreadCount}`} />
              <ControlPill icon={SlidersHorizontal} label="Priority aware" value="Enabled" />
              <ControlPill icon={Workflow} label="Realtime sync" value="Active" />
            </div>

            {isLoading ? (
              <div className="panel-deep p-6">
                <LoadingSpinner />
              </div>
            ) : (
              <div className="space-y-3">
                {realtimeNotifications.map((notification) => (
                  <article key={notification.id} className="panel-premium flex items-start justify-between gap-4 p-4">
                    <div>
                      <div className="text-sm font-semibold text-white">{notification.title}</div>
                      <p className="mt-2 text-sm leading-7 text-white/56">{notification.message}</p>
                      <p className="mt-3 text-[10px] uppercase tracking-[0.22em] text-white/36">
                        {titleCase(notification.priority)} | {formatDateTime(notification.created_at)}
                      </p>
                    </div>
                    {!notification.is_read ? (
                      <button
                        type="button"
                        onClick={() => markRead(notification.id)}
                        className="rounded-full border border-cyan-300/20 px-3 py-2 text-xs font-medium text-cyan-100 transition hover:border-cyan-300/35"
                      >
                        Mark read
                      </button>
                    ) : null}
                  </article>
                ))}
              </div>
            )}

            <article className="panel-premium p-6 sm:p-8">
              <p className="story-kicker">White-label</p>
              <h2 className="mt-4 text-3xl font-semibold text-white">Enterprise branding and delivery controls</h2>
              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <label className="block">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">Company name</div>
                  <input className="input-premium" value={whiteLabelForm.company_name} onChange={(event) => setWhiteLabelForm((current) => ({ ...current, company_name: event.target.value }))} />
                </label>
                <label className="block">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">Logo URL</div>
                  <input className="input-premium" value={whiteLabelForm.logo_url} onChange={(event) => setWhiteLabelForm((current) => ({ ...current, logo_url: event.target.value }))} />
                </label>
                <label className="block">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">Primary color</div>
                  <input className="input-premium" value={whiteLabelForm.primary_color} onChange={(event) => setWhiteLabelForm((current) => ({ ...current, primary_color: event.target.value }))} />
                </label>
                <label className="block">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">Secondary color</div>
                  <input className="input-premium" value={whiteLabelForm.secondary_color} onChange={(event) => setWhiteLabelForm((current) => ({ ...current, secondary_color: event.target.value }))} />
                </label>
                <label className="block">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">Custom domain</div>
                  <input className="input-premium" value={whiteLabelForm.custom_domain} onChange={(event) => setWhiteLabelForm((current) => ({ ...current, custom_domain: event.target.value }))} />
                </label>
                <label className="block">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">Subdomain</div>
                  <input className="input-premium" value={whiteLabelForm.subdomain} onChange={(event) => setWhiteLabelForm((current) => ({ ...current, subdomain: event.target.value }))} />
                </label>
                <label className="block md:col-span-2">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">Enabled features</div>
                  <input className="input-premium" value={whiteLabelForm.enabled_features} onChange={(event) => setWhiteLabelForm((current) => ({ ...current, enabled_features: event.target.value }))} />
                </label>
              </div>
              <div className="mt-6 grid gap-4 md:grid-cols-3">
                <ControlPill icon={Palette} label="Brand mode" value={whiteLabelForm.is_active ? "Active" : "Paused"} />
                <ControlPill icon={KeyRound} label="API layer" value={whiteLabelForm.api_enabled ? "Enabled" : "Disabled"} />
                <ControlPill icon={Workflow} label="Rate limit" value={`${whiteLabelForm.api_rate_limit}/hr`} />
              </div>
              <button type="button" onClick={() => saveWhiteLabel.mutate()} className="action-premium mt-6">
                <Palette className="h-4 w-4" />
                Save white-label config
              </button>
            </article>
          </div>
        </section>
      </div>
    </AuthGuard>
  )
}

function ProfileRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-[0.26em] text-white/38">{label}</div>
      <div className="mt-2 text-lg font-semibold text-white">{value}</div>
    </div>
  )
}

function SettingTile({
  icon: Icon,
  label,
  value,
  text
}: {
  icon: typeof Workflow
  label: string
  value: string
  text: string
}) {
  return (
    <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-4">
      <div className="inline-flex items-center gap-2 text-[10px] uppercase tracking-[0.28em] text-white/38">
        <Icon className="h-3.5 w-3.5 text-cyan-200" />
        {label}
      </div>
      <div className="mt-3 text-lg font-semibold text-white">{value}</div>
      <p className="mt-3 text-sm leading-7 text-white/56">{text}</p>
    </div>
  )
}

function ControlPill({
  icon: Icon,
  label,
  value
}: {
  icon: typeof Bell
  label: string
  value: string
}) {
  return (
    <div className="panel-premium p-5">
      <div className="inline-flex items-center gap-2 text-[10px] uppercase tracking-[0.28em] text-white/40">
        <Icon className="h-3.5 w-3.5 text-violet-200" />
        {label}
      </div>
      <div className="mt-4 text-2xl font-semibold text-white">{value}</div>
    </div>
  )
}
