"use client"

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import type { ReactNode } from "react"
import { ThemeProvider } from "next-themes"
import { useEffect, useState } from "react"

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 3 * 60 * 1000,
            gcTime: 15 * 60 * 1000,
            retry: 1,
            refetchOnWindowFocus: false,
            refetchOnReconnect: false
          }
        }
      })
  )

  useEffect(() => {
    if (typeof window === "undefined") {
      return
    }

    const payload = window.localStorage.getItem("dubnewsai-brand-preview")
    if (!payload) {
      return
    }

    try {
      const parsed = JSON.parse(payload) as { primary_color?: string; secondary_color?: string }
      if (parsed.primary_color) {
        document.documentElement.style.setProperty("--brand-primary", parsed.primary_color)
        document.documentElement.style.setProperty("--brand-primary-rgb", toRgbChannels(parsed.primary_color))
      }
      if (parsed.secondary_color) {
        document.documentElement.style.setProperty("--brand-secondary", parsed.secondary_color)
        document.documentElement.style.setProperty("--brand-secondary-rgb", toRgbChannels(parsed.secondary_color))
      }
    } catch {
      window.localStorage.removeItem("dubnewsai-brand-preview")
    }
  }, [])

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
        {children}
      </ThemeProvider>
    </QueryClientProvider>
  )
}

function toRgbChannels(hex: string) {
  const sanitized = hex.replace("#", "")
  const normalized = sanitized.length === 3 ? sanitized.split("").map((char) => char + char).join("") : sanitized
  const numeric = Number.parseInt(normalized, 16)
  const red = (numeric >> 16) & 255
  const green = (numeric >> 8) & 255
  const blue = numeric & 255
  return `${red} ${green} ${blue}`
}
