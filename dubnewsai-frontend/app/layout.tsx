import type { Metadata } from "next"
import { Inter, JetBrains_Mono, Merriweather, Space_Grotesk } from "next/font/google"
import type { ReactNode } from "react"

import "./globals.css"
import { getDefaultAppUrl } from "@/lib/config/api"
import { Providers } from "./providers"
import { Toaster } from "react-hot-toast"

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap"
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap"
})

const clashDisplay = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-clash",
  display: "swap"
})

const editorial = Merriweather({
  subsets: ["latin"],
  variable: "--font-editorial",
  display: "swap",
  weight: ["300", "400", "700"]
})

export const metadata: Metadata = {
  metadataBase: new URL(getDefaultAppUrl(process.env.NEXT_PUBLIC_APP_URL)),
  title: {
    default: "DUBNEWSAI | Dubai Intelligence Platform",
    template: "%s | DUBNEWSAI"
  },
  description: "Premium Dubai market intelligence across news, listed developers, property, macro, predictions, alerts, and executive workflows.",
  keywords: ["Dubai", "Market Intelligence", "Real Estate", "Analytics", "Investing", "UAE", "Property"],
  alternates: {
    canonical: "/"
  },
  openGraph: {
    title: "DUBNEWSAI | Dubai Intelligence Platform",
    description: "A premium command surface for Dubai news, market signals, property intelligence, investor workflows, and executive monitoring.",
    url: "/",
    siteName: "DUBNEWSAI",
    locale: "en_US",
    type: "website"
  },
  twitter: {
    card: "summary_large_image",
    title: "DUBNEWSAI | Dubai Intelligence Platform",
    description: "Dubai news, market signals, property intelligence, alerts, and executive workflows in one premium platform."
  }
}

export default function RootLayout({
  children
}: {
  children: ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} ${clashDisplay.variable} ${editorial.variable} font-sans antialiased`}
      >
        <Providers>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              className: "glass-effect text-sm text-slate-900 dark:text-slate-100",
              duration: 3000
            }}
          />
        </Providers>
      </body>
    </html>
  )
}
