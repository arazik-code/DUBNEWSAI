"use client"

import { AnimatePresence, motion } from "framer-motion"
import { LogOut, Menu, X } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useTheme } from "next-themes"
import { useState } from "react"
import type { ReactNode } from "react"

import { useAuth } from "@/lib/hooks/useAuth"
import { routes } from "@/lib/constants/routes"
import { cn } from "@/lib/utils/cn"

export function MobileNav() {
  const [isOpen, setIsOpen] = useState(false)
  const { logout } = useAuth()
  const { resolvedTheme } = useTheme()
  const isDark = resolvedTheme === "dark"

  return (
    <div className="lg:hidden">
      <button
        onClick={() => setIsOpen((value) => !value)}
        className={cn(
          "rounded-full border p-2.5",
          isDark ? "border-white/10 bg-white/[0.05] text-white/78" : "border-slate-200/70 bg-white/75 text-slate-700"
        )}
      >
        {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </button>

      <AnimatePresence>
        {isOpen ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xl"
          >
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 26, stiffness: 240 }}
              className="ml-auto flex h-full w-[86vw] max-w-sm flex-col border-l border-white/10 bg-[#07090d] p-6 shadow-[0_0_60px_rgba(0,0,0,0.5)]"
            >
              <div className="mb-10 flex items-center justify-between">
                <div>
                  <h2 className="font-display text-2xl font-bold text-white">DUBNEWSAI</h2>
                  <p className="mt-1 text-[10px] uppercase tracking-[0.32em] text-white/42">Navigation</p>
                </div>
                <button onClick={() => setIsOpen(false)} className="rounded-full border border-white/10 bg-white/[0.03] p-2 text-white/70">
                  <X className="h-5 w-5" />
                </button>
              </div>

              <nav className="space-y-3">
                {routes.map((route) => (
                  <MobileNavLink key={route.href} href={route.href} onClick={() => setIsOpen(false)}>
                    {route.label}
                  </MobileNavLink>
                ))}
              </nav>

              <button
                type="button"
                onClick={() => {
                  setIsOpen(false)
                  logout()
                }}
                className="mt-auto flex w-full items-center gap-2 rounded-[1.4rem] border border-red-500/25 px-4 py-4 text-left text-base font-medium text-red-300 transition hover:border-red-400/40 hover:text-red-200"
              >
                <LogOut className="h-5 w-5" />
                Sign out
              </button>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  )
}

function MobileNavLink({
  href,
  children,
  onClick
}: {
  href: string
  children: ReactNode
  onClick: () => void
}) {
  const pathname = usePathname()

  return (
    <Link
      href={href}
      onClick={onClick}
        className={cn(
          "block rounded-[1.4rem] border px-4 py-4 text-base font-medium transition-colors",
          pathname === href
            ? "border-white/12 bg-white/[0.12] text-white"
            : "border-white/10 bg-white/[0.03] text-white/74 hover:text-white"
        )}
    >
      {children}
    </Link>
  )
}
