"use client"

import { BarChart3, BellRing, Building2, LayoutDashboard, LineChart, Newspaper, Settings, Shield } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"

import { cn } from "@/lib/utils/cn"
import { useAuthStore } from "@/lib/store/authStore"

const baseItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/news", label: "News Feed", icon: Newspaper },
  { href: "/market", label: "Market", icon: LineChart },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/alerts", label: "Alerts", icon: BellRing },
  { href: "/settings", label: "Settings", icon: Settings }
]

export function Sidebar() {
  const pathname = usePathname()
  const user = useAuthStore((state) => state.user)
  const items = user?.role === "admin"
    ? [...baseItems, { href: "/admin/providers", label: "Providers", icon: Shield }]
    : baseItems

  return (
    <aside className="fixed left-0 top-20 hidden h-[calc(100vh-5rem)] w-64 border-r border-white/10 bg-transparent lg:block">
      <div className="m-4 rounded-3xl border border-white/10 bg-slate-950/70 p-4 shadow-2xl shadow-slate-950/25 backdrop-blur-xl">
        <div className="mb-6 rounded-2xl border border-gold-400/20 bg-gradient-to-br from-gold-500/10 to-cyber-500/10 p-4">
          <div className="mb-1 flex items-center gap-2 text-sm font-semibold text-gold-300">
            <Building2 className="h-4 w-4" />
            Dubai Intelligence
          </div>
          <p className="text-sm text-slate-300">
            Monitor news, pricing momentum, and AI signals across the market.
          </p>
        </div>

        <nav className="space-y-1">
          {items.map((item) => {
            const Icon = item.icon
            const active = pathname === item.href

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-all",
                  active
                    ? "bg-gradient-to-r from-gold-500/20 to-cyber-500/15 text-white shadow-lg shadow-gold-500/10"
                    : "text-slate-400 hover:bg-white/5 hover:text-slate-100"
                )}
              >
                <Icon className={cn("h-4 w-4", active ? "text-gold-300" : "text-slate-500")} />
                {item.label}
              </Link>
            )
          })}
        </nav>
      </div>
    </aside>
  )
}
