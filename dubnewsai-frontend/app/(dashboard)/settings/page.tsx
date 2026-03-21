"use client"

import { useEffect, useMemo, useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { Bell, Building2, KeyRound, Palette, ShieldCheck, SunMedium, Waves, Workflow } from "lucide-react"
import { useTheme } from "next-themes"

import { AuthGuard } from "@/components/auth/AuthGuard"
import { ActionStatus } from "@/components/shared/ActionStatus"
import { LoadingSpinner } from "@/components/shared/LoadingSpinner"
import { PremiumPageHero } from "@/components/ui/premium-page-hero"
import { apiClient } from "@/lib/api/client"
import { useAuth } from "@/lib/hooks/useAuth"
import { useApiKeys, useWhiteLabelConfig } from "@/lib/hooks/useEnterprise"
import { useNotifications } from "@/lib/hooks/useNotifications"
import { useNotificationStore } from "@/lib/store/notificationStore"
import { formatDateTime, titleCase } from "@/lib/utils/formatters"

const BRAND_PRESETS = [
  { name: "Gulf Signal", primary: "#22D3EE", secondary: "#F59E0B" },
  { name: "Capital Mint", primary: "#10B981", secondary: "#0EA5E9" },
  { name: "Executive Slate", primary: "#334155", secondary: "#F97316" }
]

const THEME_OPTIONS = ["dark", "light", "system"] as const

export default function SettingsPage() {
  const queryClient = useQueryClient()
  const { theme, setTheme } = useTheme()
  const { user } = useAuth()
  const { data: notifications, isLoading, markRead, markAllRead, markingAllRead } = useNotifications()
  const { data: apiKeys = [] } = useApiKeys()
  const { data: whiteLabel } = useWhiteLabelConfig()
  const realtimeNotifications = useNotificationStore((state) => state.items)
  const hydrateNotifications = useNotificationStore((state) => state.hydrate)
  const [apiKeyForm, setApiKeyForm] = useState({ name: "Enterprise feed key", rate_limit_per_hour: 250 })
  const [whiteLabelForm, setWhiteLabelForm] = useState({
    company_name: "DUBNEWSAI Intelligence",
    logo_url: "",
    primary_color: "#22D3EE",
    secondary_color: "#F59E0B",
    custom_domain: "",
    subdomain: "",
    api_enabled: true,
    api_rate_limit: 250,
    is_active: true
  })
  const [plaintextKey, setPlaintextKey] = useState<string | null>(null)
  const [themeMode, setThemeMode] = useState("system")

  useEffect(() => {
    if (notifications?.length) {
      hydrateNotifications(notifications)
    }
  }, [hydrateNotifications, notifications])

  useEffect(() => {
    if (theme) {
      setThemeMode(theme)
    }
  }, [theme])

  useEffect(() => {
    if (whiteLabel) {
      setWhiteLabelForm({
        company_name: whiteLabel.company_name,
        logo_url: whiteLabel.logo_url || "",
        primary_color: whiteLabel.primary_color || "#22D3EE",
        secondary_color: whiteLabel.secondary_color || "#F59E0B",
        custom_domain: whiteLabel.custom_domain || "",
        subdomain: whiteLabel.subdomain || "",
        api_enabled: whiteLabel.api_enabled,
        api_rate_limit: whiteLabel.api_rate_limit,
        is_active: whiteLabel.is_active
      })
    }
  }, [whiteLabel])

  useEffect(() => {
    applyBrandPreview(whiteLabelForm.primary_color, whiteLabelForm.secondary_color)
    if (typeof window !== "undefined") {
      window.localStorage.setItem(
        "dubnewsai-brand-preview",
        JSON.stringify({
          primary_color: whiteLabelForm.primary_color,
          secondary_color: whiteLabelForm.secondary_color
        })
      )
    }
  }, [whiteLabelForm.primary_color, whiteLabelForm.secondary_color])

  const whiteLabelValidation = useMemo(() => {
    const companyName = whiteLabelForm.company_name.trim()
    const colorPattern = /^#[0-9A-Fa-f]{6}$/
    const primaryValid = colorPattern.test(whiteLabelForm.primary_color)
    const secondaryValid = colorPattern.test(whiteLabelForm.secondary_color)

    return {
      companyName,
      primaryValid,
      secondaryValid,
      canSave: Boolean(companyName) && primaryValid && secondaryValid
    }
  }, [whiteLabelForm.company_name, whiteLabelForm.primary_color, whiteLabelForm.secondary_color])

  const createApiKey = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post("/settings/api-keys", {
        ...apiKeyForm,
        name: apiKeyForm.name.trim()
      })
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
        company_name: whiteLabelValidation.companyName
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
          title="Settings should stay calm while the platform stays live."
          description="Identity, inbox controls, API keys, theme, and white-label setup from one cleaner operations surface."
          chips={["Identity", "Inbox", "API access", "White-label"]}
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
              label: "Theme mode",
              value: titleCase(themeMode),
              hint: "Applied across the live workspace"
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
                <SettingTile icon={Workflow} label="Alert delivery" value="Realtime + inbox" text="Built for fast follow-up." />
                <SettingTile icon={Waves} label="Data cadence" value="Always-on refresh" text="Signals stay current in the background." />
                <SettingTile icon={ShieldCheck} label="Security posture" value="Role-aware access" text="Access is controlled per user." />
                <SettingTile icon={Building2} label="Deployment mode" value="Production linked" text="Connected to live infrastructure." />
              </div>
            </article>

            <article className="panel-premium p-6 sm:p-8">
              <p className="story-kicker">API access</p>
              <h2 className="mt-4 text-3xl font-semibold text-white">Issue and manage public API keys</h2>
              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <label className="block">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">Key name</div>
                  <input
                    className="input-premium"
                    value={apiKeyForm.name}
                    onChange={(event) => setApiKeyForm((current) => ({ ...current, name: event.target.value }))}
                  />
                </label>
                <label className="block">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">Hourly limit</div>
                  <input
                    type="number"
                    className="input-premium"
                    value={apiKeyForm.rate_limit_per_hour}
                    onChange={(event) => setApiKeyForm((current) => ({ ...current, rate_limit_per_hour: Number(event.target.value) }))}
                  />
                </label>
              </div>
              <button
                type="button"
                onClick={() => createApiKey.mutate()}
                className="action-premium mt-5"
                disabled={createApiKey.isPending || !apiKeyForm.name.trim()}
              >
                <KeyRound className="h-4 w-4" />
                {createApiKey.isPending ? "Creating..." : "Create API key"}
              </button>
              <ActionStatus
                isPending={createApiKey.isPending}
                isSuccess={createApiKey.isSuccess}
                error={createApiKey.error}
                successMessage="API key created."
              />
              {plaintextKey ? (
                <div className="mt-5 rounded-[1.4rem] border border-cyan-300/20 bg-cyan-300/[0.06] p-4">
                  <div className="text-[10px] uppercase tracking-[0.28em] text-cyan-100/70">New key</div>
                  <div className="mt-3 break-all text-sm text-white">{plaintextKey}</div>
                </div>
              ) : null}
              <div className="mt-6 space-y-3">
                {apiKeys.length ? (
                  apiKeys.map((item) => (
                    <div key={item.id} className="rounded-[1.4rem] border border-white/10 bg-white/[0.03] p-4">
                      <div className="flex items-center justify-between gap-4">
                        <div>
                          <div className="text-sm font-semibold text-white">{item.name}</div>
                          <div className="mt-1 text-xs text-white/42">
                            {item.rate_limit_per_hour} req/hr | {item.total_requests} total requests
                          </div>
                        </div>
                        <div className="text-xs text-white/46">{item.last_used_at ? formatDateTime(item.last_used_at) : "Never used"}</div>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="rounded-[1.4rem] border border-dashed border-white/12 bg-white/[0.02] p-4 text-sm text-white/50">
                    No API keys yet. Create one when you are ready to expose market, news, or analytics data externally.
                  </div>
                )}
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
              <ControlPill icon={Workflow} label="Realtime sync" value="Active" />
              <ControlPill icon={SunMedium} label="Theme" value={titleCase(themeMode)} />
            </div>

            {isLoading ? (
              <div className="panel-deep p-6">
                <LoadingSpinner />
              </div>
            ) : (
              <div className="space-y-3">
                {realtimeNotifications.length ? (
                  realtimeNotifications.map((notification) => (
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
                  ))
                ) : (
                  <div className="panel-premium p-5 text-sm text-white/54">
                    Your inbox is clear. New alerts, summaries, and workflow prompts will appear here as the workspace updates.
                  </div>
                )}
              </div>
            )}

            <article className="panel-premium p-6 sm:p-8">
              <p className="story-kicker">White-label</p>
              <h2 className="mt-4 text-3xl font-semibold text-white">Branding and delivery controls</h2>
              <p className="mt-4 max-w-2xl text-sm leading-7 text-white/56">
                Save a stable workspace identity here. Domain conflicts and invalid color values are checked before they become database errors.
              </p>

              <div className="mt-6 grid gap-3 md:grid-cols-3">
                {BRAND_PRESETS.map((preset) => (
                  <button
                    key={preset.name}
                    type="button"
                    onClick={() =>
                      setWhiteLabelForm((current) => ({
                        ...current,
                        primary_color: preset.primary,
                        secondary_color: preset.secondary
                      }))
                    }
                    className="rounded-[1.35rem] border border-white/10 bg-white/[0.03] p-4 text-left transition hover:border-cyan-300/30"
                  >
                    <div className="text-sm font-semibold text-white">{preset.name}</div>
                    <div className="mt-3 flex gap-2">
                      <span className="h-8 w-8 rounded-full border border-white/10" style={{ backgroundColor: preset.primary }} />
                      <span className="h-8 w-8 rounded-full border border-white/10" style={{ backgroundColor: preset.secondary }} />
                    </div>
                  </button>
                ))}
              </div>

              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <label className="block">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">Company name</div>
                  <input
                    className="input-premium"
                    value={whiteLabelForm.company_name}
                    onChange={(event) => setWhiteLabelForm((current) => ({ ...current, company_name: event.target.value }))}
                  />
                </label>
                <label className="block">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">Logo URL</div>
                  <input
                    className="input-premium"
                    value={whiteLabelForm.logo_url}
                    onChange={(event) => setWhiteLabelForm((current) => ({ ...current, logo_url: event.target.value }))}
                  />
                </label>
                <label className="block">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">Primary color</div>
                  <div className="flex items-center gap-3">
                    <input
                      type="color"
                      className="h-12 w-16 rounded-xl border border-white/10 bg-transparent"
                      value={whiteLabelForm.primary_color}
                      onChange={(event) => setWhiteLabelForm((current) => ({ ...current, primary_color: event.target.value.toUpperCase() }))}
                    />
                    <input
                      className="input-premium"
                      value={whiteLabelForm.primary_color}
                      onChange={(event) => setWhiteLabelForm((current) => ({ ...current, primary_color: event.target.value.toUpperCase() }))}
                    />
                  </div>
                </label>
                <label className="block">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">Secondary color</div>
                  <div className="flex items-center gap-3">
                    <input
                      type="color"
                      className="h-12 w-16 rounded-xl border border-white/10 bg-transparent"
                      value={whiteLabelForm.secondary_color}
                      onChange={(event) => setWhiteLabelForm((current) => ({ ...current, secondary_color: event.target.value.toUpperCase() }))}
                    />
                    <input
                      className="input-premium"
                      value={whiteLabelForm.secondary_color}
                      onChange={(event) => setWhiteLabelForm((current) => ({ ...current, secondary_color: event.target.value.toUpperCase() }))}
                    />
                  </div>
                </label>
                <label className="block">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">Custom domain</div>
                  <input
                    className="input-premium"
                    value={whiteLabelForm.custom_domain}
                    onChange={(event) => setWhiteLabelForm((current) => ({ ...current, custom_domain: event.target.value }))}
                  />
                </label>
                <label className="block">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">Subdomain</div>
                  <input
                    className="input-premium"
                    value={whiteLabelForm.subdomain}
                    onChange={(event) => setWhiteLabelForm((current) => ({ ...current, subdomain: event.target.value }))}
                  />
                </label>
                <div className="block">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">Theme mode</div>
                  <div className="grid grid-cols-3 gap-2">
                    {THEME_OPTIONS.map((mode) => (
                      <button
                        key={mode}
                        type="button"
                        onClick={() => {
                          setThemeMode(mode)
                          setTheme(mode)
                        }}
                        className={`rounded-[1rem] border px-3 py-3 text-sm transition ${
                          themeMode === mode ? "border-cyan-300/35 bg-cyan-300/[0.08] text-white" : "border-white/10 bg-white/[0.03] text-white/64"
                        }`}
                      >
                        {titleCase(mode)}
                      </button>
                    ))}
                  </div>
                </div>
                <label className="block">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">API rate limit</div>
                  <input
                    type="number"
                    className="input-premium"
                    value={whiteLabelForm.api_rate_limit}
                    onChange={(event) => setWhiteLabelForm((current) => ({ ...current, api_rate_limit: Number(event.target.value) }))}
                  />
                </label>
                <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.03] p-4">
                  <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Delivery controls</div>
                  <div className="mt-4 space-y-3 text-sm text-white/70">
                    <label className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={whiteLabelForm.api_enabled}
                        onChange={(event) => setWhiteLabelForm((current) => ({ ...current, api_enabled: event.target.checked }))}
                      />
                      Enable public API access
                    </label>
                    <label className="flex items-center gap-3">
                      <input
                        type="checkbox"
                        checked={whiteLabelForm.is_active}
                        onChange={(event) => setWhiteLabelForm((current) => ({ ...current, is_active: event.target.checked }))}
                      />
                      Keep white-label profile active
                    </label>
                  </div>
                </div>
                <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.03] p-4 md:col-span-2">
                  <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Access model</div>
                  <p className="mt-4 text-sm leading-7 text-white/58">
                    Branding does not control feature access anymore. Admins grant premium workspaces per user, while public visitors keep News and Market and signed-in users start with Analytics, Alerts, and Settings.
                  </p>
                </div>
              </div>

              {!whiteLabelValidation.canSave ? (
                <div className="mt-5 rounded-[1.4rem] border border-amber-300/20 bg-amber-300/[0.08] p-4 text-sm text-amber-50">
                  Use a company name and full 6-digit hex colors like <span className="font-semibold">#22D3EE</span> before saving.
                </div>
              ) : null}

              <div className="mt-6 grid gap-4 md:grid-cols-3">
                <ControlPill icon={Palette} label="Brand mode" value={whiteLabelForm.is_active ? "Active" : "Paused"} />
                <ControlPill icon={KeyRound} label="API layer" value={whiteLabelForm.api_enabled ? "Enabled" : "Disabled"} />
                <ControlPill icon={SunMedium} label="Theme" value={titleCase(themeMode)} />
              </div>

              <div
                className="mt-6 rounded-[1.5rem] border border-white/10 p-5"
                style={{ backgroundImage: `linear-gradient(135deg, ${whiteLabelForm.primary_color}22, ${whiteLabelForm.secondary_color}22)` }}
              >
                <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Live preview</div>
                <div className="mt-3 text-lg font-semibold text-white">{whiteLabelValidation.companyName || "Workspace brand"}</div>
                <p className="mt-2 text-sm text-white/58">Theme and brand colors preview immediately in the workspace before you save.</p>
              </div>

              <button
                type="button"
                onClick={() => saveWhiteLabel.mutate()}
                className="action-premium mt-6"
                disabled={saveWhiteLabel.isPending || !whiteLabelValidation.canSave}
              >
                <Palette className="h-4 w-4" />
                {saveWhiteLabel.isPending ? "Saving..." : "Save white-label config"}
              </button>
              <ActionStatus
                isPending={saveWhiteLabel.isPending}
                isSuccess={saveWhiteLabel.isSuccess}
                error={saveWhiteLabel.error}
                successMessage="White-label settings saved."
              />
            </article>
          </div>
        </section>
      </div>
    </AuthGuard>
  )
}

function hexToRgbChannels(hex: string) {
  const sanitized = hex.replace("#", "")
  const normalized = sanitized.length === 3 ? sanitized.split("").map((char) => char + char).join("") : sanitized
  const numeric = Number.parseInt(normalized, 16)
  const red = (numeric >> 16) & 255
  const green = (numeric >> 8) & 255
  const blue = numeric & 255
  return `${red} ${green} ${blue}`
}

function applyBrandPreview(primary: string, secondary: string) {
  if (typeof document === "undefined") {
    return
  }

  const root = document.documentElement
  root.style.setProperty("--brand-primary", primary)
  root.style.setProperty("--brand-secondary", secondary)
  root.style.setProperty("--brand-primary-rgb", hexToRgbChannels(primary))
  root.style.setProperty("--brand-secondary-rgb", hexToRgbChannels(secondary))
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
