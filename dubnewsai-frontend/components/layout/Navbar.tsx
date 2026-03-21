"use client"

import { Bell, LogOut, Sparkles, Wifi, WifiOff } from "lucide-react"
import Link from "next/link"
import { useTheme } from "next-themes"

import { MobileNav } from "@/components/layout/MobileNav"
import { ThemeToggle } from "@/components/shared/ThemeToggle"
import { useAuth } from "@/lib/hooks/useAuth"
import { useWebSocket } from "@/lib/hooks/useWebSocket"
import { cn } from "@/lib/utils/cn"

export function Navbar() {
  const { isConnected } = useWebSocket()
  const { isAuthenticated, logout, user } = useAuth()
  const { resolvedTheme } = useTheme()
  const isDark = resolvedTheme === "dark"

  return (
    <header
      className={cn(
        "sticky top-0 z-40 border-b backdrop-blur-2xl",
        isDark ? "border-white/8 bg-[#050506]/84" : "border-slate-200/70 bg-white/80"
      )}
    >
      <div className="mx-auto flex h-20 max-w-[1600px] items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-4">
          <MobileNav />
          <Link href={isAuthenticated ? "/dashboard" : "/"} className="flex items-center gap-3">
            <div
              className={cn(
                "flex h-11 w-11 items-center justify-center rounded-2xl border text-sm font-black",
                isDark
                  ? "border-white/10 bg-white/[0.08] text-white shadow-[0_12px_40px_-18px_rgba(0,0,0,0.75)]"
                  : "border-slate-200/70 bg-white text-slate-950 shadow-[0_12px_40px_-18px_rgba(15,23,42,0.18)]"
              )}
            >
              DN
            </div>
            <div>
              <div className={cn("font-display text-lg font-bold tracking-[0.14em]", isDark ? "text-white" : "text-slate-900")}>DUBNEWSAI</div>
              <div className={cn("text-[10px] uppercase tracking-[0.32em]", isDark ? "text-white/42" : "text-slate-500")}>Dubai market intelligence</div>
            </div>
          </Link>
          <div
            className={cn(
              "hidden items-center gap-2 rounded-full border px-3 py-2 text-[11px] uppercase tracking-[0.24em] xl:inline-flex",
              isDark ? "border-white/10 bg-white/[0.04] text-white/52" : "border-slate-200/70 bg-white/75 text-slate-500"
            )}
          >
            <Sparkles className="h-3.5 w-3.5 text-cyan-200" />
            Multi-source signal engine
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div
            className={cn(
              "hidden items-center gap-2 rounded-full border px-3 py-2 text-xs md:flex",
              isDark ? "border-white/10 bg-white/[0.04] text-white/72" : "border-slate-200/70 bg-white/75 text-slate-600"
            )}
          >
            {isConnected ? (
              <Wifi className="h-3.5 w-3.5 text-emerald-400" />
            ) : (
              <WifiOff className="h-3.5 w-3.5 text-red-400" />
            )}
            <span>{isConnected ? "Realtime connected" : "Realtime offline"}</span>
          </div>

          {isAuthenticated ? (
            <>
              <Link
                href="/settings"
                className={cn(
                  "inline-flex h-11 w-11 items-center justify-center rounded-full border transition",
                  isDark
                    ? "border-white/10 bg-white/[0.04] text-white/72 hover:text-white"
                    : "border-slate-200/70 bg-white/75 text-slate-600 hover:border-cyan-300/30 hover:text-slate-900"
                )}
              >
                <Bell className="h-4 w-4" />
              </Link>
              <div
                className={cn(
                  "hidden rounded-full border px-4 py-2 text-sm lg:block",
                  isDark ? "border-white/10 bg-white/[0.04] text-white/78" : "border-slate-200/70 bg-white/75 text-slate-700"
                )}
              >
                {user?.full_name || user?.email || "Operator"}
              </div>
              <button
                type="button"
                onClick={logout}
                className={cn(
                  "inline-flex h-11 w-11 items-center justify-center rounded-full border transition",
                  isDark
                    ? "border-white/10 bg-white/[0.04] text-white/72 hover:text-white"
                    : "border-slate-200/70 bg-white/75 text-slate-600 hover:border-amber-300/30 hover:text-slate-900"
                )}
                aria-label="Sign out"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="hidden rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm font-medium text-white/72 transition hover:text-white md:inline-flex"
              >
                Sign in
              </Link>
              <Link
                href="/register"
                className="inline-flex rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-white/92"
              >
                Get premium
              </Link>
            </>
          )}
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
