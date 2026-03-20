"use client"

import { useEffect } from "react"
import { Bell, Building2, ShieldCheck, SlidersHorizontal, Waves, Workflow } from "lucide-react"

import { AuthGuard } from "@/components/auth/AuthGuard"
import { LoadingSpinner } from "@/components/shared/LoadingSpinner"
import { PremiumPageHero } from "@/components/ui/premium-page-hero"
import { useAuth } from "@/lib/hooks/useAuth"
import { useNotifications } from "@/lib/hooks/useNotifications"
import { useNotificationStore } from "@/lib/store/notificationStore"
import { formatDateTime, titleCase } from "@/lib/utils/formatters"

export default function SettingsPage() {
  const { user } = useAuth()
  const { data: notifications, isLoading, markRead, markAllRead, markingAllRead } = useNotifications()
  const realtimeNotifications = useNotificationStore((state) => state.items)
  const hydrateNotifications = useNotificationStore((state) => state.hydrate)

  useEffect(() => {
    if (notifications?.length) {
      hydrateNotifications(notifications)
    }
  }, [hydrateNotifications, notifications])

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
