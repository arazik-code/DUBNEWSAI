"use client"

import { BarChart3, BellRing, Briefcase, Building2, LayoutDashboard, LineChart, Newspaper, Settings, Shield, Sparkles, Swords, Users2, Waves } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useTheme } from "next-themes"

import { useFeatureAccess } from "@/lib/hooks/useEnterprise"
import { useAuthStore } from "@/lib/store/authStore"
import { cn } from "@/lib/utils/cn"

const baseItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, featureKey: "dashboard" },
  { href: "/news", label: "News Feed", icon: Newspaper, featureKey: "news" },
  { href: "/market", label: "Market", icon: LineChart, featureKey: "market" },
  { href: "/portfolios", label: "Investor Suite", icon: Briefcase, featureKey: "portfolios" },
  { href: "/competitors", label: "Competitors", icon: Swords, featureKey: "competitors" },
  { href: "/analytics", label: "Analytics", icon: BarChart3, featureKey: "analytics" },
  { href: "/executive", label: "Executive", icon: Waves, featureKey: "executive" },
  { href: "/teams", label: "Teams", icon: Users2, featureKey: "teams" },
  { href: "/alerts", label: "Alerts", icon: BellRing, featureKey: "alerts" },
  { href: "/settings", label: "Settings", icon: Settings, featureKey: "settings" }
]

export function Sidebar() {
  const pathname = usePathname()
  const { resolvedTheme } = useTheme()
  const { accessToken, user } = useAuthStore()
  const { data: featureAccess = [] } = useFeatureAccess()
  const isDark = resolvedTheme === "dark"
  const accessMap = new Map(featureAccess.map((feature) => [feature.feature_key, feature.has_access]))
  const items = (user?.role === "admin"
    ? [...baseItems, { href: "/admin/providers", label: "Providers", icon: Shield, featureKey: "admin_providers" }]
    : baseItems
  ).filter((item) => {
    if (!accessToken) {
      return item.featureKey === "news" || item.featureKey === "market"
    }
    return accessMap.get(item.featureKey) ?? false
  })

  return (
    <aside className="fixed left-0 top-20 hidden h-[calc(100vh-5rem)] w-[18.5rem] overflow-x-hidden lg:block">
      <div
        className={cn(
          "m-4 flex h-[calc(100%-2rem)] min-h-0 flex-col rounded-[2rem] border p-4 backdrop-blur-2xl",
          isDark
            ? "border-white/8 bg-[#07090d]/94 shadow-[0_32px_120px_-60px_rgba(0,0,0,0.98)]"
            : "border-slate-200/70 bg-white/80 shadow-[0_32px_120px_-60px_rgba(15,23,42,0.18)]"
        )}
      >
        <div
          className={cn(
            "rounded-[1.6rem] border p-4",
            isDark
              ? "border-white/8 bg-[linear-gradient(135deg,rgba(255,255,255,0.07),rgba(255,255,255,0.02))]"
              : "border-slate-200/70 bg-[linear-gradient(135deg,rgba(255,255,255,0.9),rgba(241,245,249,0.78))]"
          )}
        >
          <div className={cn("flex items-center gap-2 text-sm font-semibold", isDark ? "text-white" : "text-slate-900")}>
            <Building2 className="h-4 w-4 text-amber-300" />
            Dubai Intelligence Desk
          </div>
          <p className={cn("mt-2 text-sm leading-6", isDark ? "text-white/58" : "text-slate-600")}>
            One workspace for Dubai news, listed developers, market signals, and context that actually helps you act.
          </p>
        </div>

        <nav className="mt-5 flex-1 space-y-1.5 overflow-y-auto overflow-x-hidden pr-1">
          {items.map((item) => {
            const Icon = item.icon
            const active = pathname === item.href

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "group flex items-center gap-3 rounded-[1.2rem] px-4 py-3 text-sm font-medium transition-all duration-300",
                  active
                    ? isDark
                      ? "bg-white/[0.08] text-white shadow-[0_22px_40px_-24px_rgba(0,0,0,0.72)]"
                      : "bg-white text-slate-950 shadow-[0_18px_40px_-24px_rgba(255,255,255,0.85)]"
                    : isDark
                      ? "text-white/62 hover:bg-white/[0.05] hover:text-white"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-950"
                )}
              >
                <span
                  className={cn(
                    "flex h-9 w-9 items-center justify-center rounded-full border transition-all",
                    active
                      ? isDark
                        ? "border-white/10 bg-white/[0.08]"
                        : "border-slate-200 bg-slate-100"
                      : isDark
                        ? "border-white/10 bg-white/[0.03]"
                        : "border-slate-200/70 bg-white"
                  )}
                >
                  <Icon
                    className={cn(
                      "h-4 w-4",
                      active
                        ? isDark
                          ? "text-white"
                          : "text-slate-950"
                        : isDark
                          ? "text-white/60 group-hover:text-white"
                          : "text-slate-500 group-hover:text-slate-950"
                    )}
                  />
                </span>
                <span className="flex-1">{item.label}</span>
              </Link>
            )
          })}
        </nav>

        <div
          className={cn(
            "mt-auto rounded-[1.6rem] border p-4",
            isDark ? "border-cyan-300/18 bg-cyan-300/[0.06]" : "border-cyan-300/18 bg-cyan-300/[0.08]"
          )}
        >
          <div className={cn("flex items-center gap-2 text-xs uppercase tracking-[0.28em]", isDark ? "text-cyan-100/60" : "text-cyan-700")}>
            <Sparkles className="h-3.5 w-3.5" />
            Live stack
          </div>
          <div className={cn("mt-4 space-y-3 text-sm", isDark ? "text-white/72" : "text-slate-700")}>
            <div className="flex items-center justify-between">
              <span>News coverage</span>
              <span className={cn("rounded-full border px-2 py-1 text-[11px] uppercase tracking-[0.18em]", isDark ? "border-white/10 text-white/58" : "border-slate-200/70 text-slate-500")}>active</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Market signals</span>
              <span className={cn("rounded-full border px-2 py-1 text-[11px] uppercase tracking-[0.18em]", isDark ? "border-white/10 text-white/58" : "border-slate-200/70 text-slate-500")}>streaming</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  )
}
