"use client"

import { motion, useReducedMotion } from "framer-motion"
import {
  ArrowRight,
  BellRing,
  Blocks,
  BrainCircuit,
  Building2,
  CandlestickChart,
  ChevronRight,
  Globe2,
  Radar,
  ShieldCheck,
  Sparkles,
  Waves
} from "lucide-react"
import Link from "next/link"
import type { ReactNode } from "react"

import { SparklesCore } from "@/components/ui/sparkles"

const heroMetrics = [
  { label: "Coverage", value: "Dubai, UAE, GCC" },
  { label: "Signal layers", value: "News, market, macro, alerts" },
  { label: "Decision tempo", value: "Minutes, not hours" }
] as const

const platformPillars = [
  {
    eyebrow: "Signal clarity",
    title: "See the story, the symbol, and the market backdrop in one view.",
    copy:
      "DUBNEWSAI is designed to stop context fragmentation. News, property pressure, listed developers, FX, and macro signals connect inside one operating surface.",
    icon: Radar,
    accent: "from-cyan-300/30 to-transparent"
  },
  {
    eyebrow: "Operator workflow",
    title: "Move from discovery to action without changing mental gears.",
    copy:
      "Watchlists, alerts, analytics, investor intelligence, and executive views are arranged as a coherent decision system instead of separate product islands.",
    icon: BrainCircuit,
    accent: "from-amber-300/30 to-transparent"
  },
  {
    eyebrow: "Trust posture",
    title: "Provider-aware, quality-aware, and built for real production use.",
    copy:
      "The platform surfaces source health, confidence, and structured fallback behavior so users can trust what they are seeing under real market pressure.",
    icon: ShieldCheck,
    accent: "from-emerald-300/30 to-transparent"
  }
] as const

const workflowSteps = [
  {
    step: "01",
    title: "Absorb the market quickly",
    text: "Open a command surface built to communicate pressure, movement, and concentration without throwing noise at the user."
  },
  {
    step: "02",
    title: "Validate the signal",
    text: "Cross-check headlines with listed names, location-level property context, technical pressure, and market-wide momentum."
  },
  {
    step: "03",
    title: "Act from one workspace",
    text: "Shift into alerts, investor tools, competitive intelligence, or executive views without losing the original context."
  }
] as const

const audienceCards = [
  { title: "Investors", copy: "Track portfolios, watchlists, and price setups with local market context.", icon: CandlestickChart },
  { title: "Brokerage teams", copy: "Run a cleaner workflow for discovery, monitoring, and client-facing market interpretation.", icon: Building2 },
  { title: "Operators", copy: "Turn scattered sources into one monitored intelligence system that actually feels operational.", icon: Blocks },
  { title: "Advisory leaders", copy: "Move from broad Dubai market awareness into strategic and executive-level action.", icon: Waves }
] as const

const systemHighlights = [
  "Fast-loading dashboard architecture",
  "Role-aware feature access",
  "Per-user admin grants",
  "Curated prediction and property universes",
  "Investor and competitor intelligence layers",
  "Premium light and dark mode support"
] as const

export default function LandingPage() {
  const reducedMotion = useReducedMotion()

  return (
    <div className="min-h-screen overflow-x-hidden bg-[#050506] text-white">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.1),transparent_24%),radial-gradient(circle_at_top_right,rgba(245,158,11,0.08),transparent_26%),radial-gradient(circle_at_bottom_left,rgba(16,185,129,0.06),transparent_22%),linear-gradient(180deg,rgba(255,255,255,0.03),transparent_18%)]" />
      <div className="pointer-events-none fixed inset-0 opacity-20 [background-image:linear-gradient(rgba(255,255,255,0.045)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.045)_1px,transparent_1px)] [background-size:84px_84px]" />
      <SparklesCore
        className="pointer-events-none fixed inset-0 h-full w-full opacity-40"
        background="transparent"
        minSize={0.4}
        maxSize={1.2}
        particleDensity={70}
        particleColor="#dbeafe"
        speed={0.55}
      />

      <LandingNav />

      <main className="relative">
        <section className="relative overflow-hidden px-4 pb-20 pt-28 sm:px-6 lg:px-8 lg:pb-28 lg:pt-32">
          <div className="mx-auto grid max-w-[1440px] gap-12 lg:grid-cols-[1.03fr_0.97fr] lg:items-end">
            <motion.div
              initial={reducedMotion ? false : { opacity: 0, y: 22 }}
              animate={reducedMotion ? undefined : { opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              className="relative"
            >
              <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.05] px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.28em] text-white/68 shadow-[0_18px_60px_-38px_rgba(0,0,0,0.5)] backdrop-blur-xl">
                <Sparkles className="h-3.5 w-3.5 text-amber-400" />
                Dubai market intelligence system
              </div>

              <div className="mt-8 max-w-4xl">
                <p className="font-editorial text-[1.02rem] italic tracking-[0.05em] text-white/42">
                  Built for investors, operators, and leaders who need to understand Dubai before they commit.
                </p>
                <h1 className="mt-5 font-display text-[3.7rem] font-bold leading-[0.94] tracking-[-0.07em] text-white sm:text-[4.8rem] lg:text-[6.7rem]">
                  A sharper way
                  <span className="block bg-[linear-gradient(135deg,#ffffff,#67e8f9,#fde68a)] bg-clip-text text-transparent">
                    to read Dubai.
                  </span>
                </h1>
                <p className="mt-7 max-w-2xl text-base leading-8 text-white/58 sm:text-lg">
                  DUBNEWSAI brings together market-moving headlines, listed developers, property intelligence, macro context, predictions, alerts, and executive workflow into one premium operating surface.
                </p>
              </div>

              <div className="mt-10 flex flex-col gap-4 sm:flex-row">
                <Link
                  href="/news"
                  className="inline-flex items-center justify-center gap-2 rounded-full bg-white px-6 py-3.5 text-sm font-semibold text-slate-950 transition hover:bg-slate-100"
                >
                  Open intelligence feed
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  href="/market"
                  className="inline-flex items-center justify-center rounded-full border border-white/10 bg-white/[0.04] px-6 py-3.5 text-sm font-semibold text-white/76 transition hover:border-cyan-300/40 hover:bg-white/[0.08] hover:text-white"
                >
                  Explore market stack
                </Link>
              </div>

              <div className="mt-10 grid gap-3 sm:grid-cols-3">
                {heroMetrics.map((metric, index) => (
                  <motion.div
                    key={metric.label}
                    initial={reducedMotion ? false : { opacity: 0, y: 18 }}
                    animate={reducedMotion ? undefined : { opacity: 1, y: 0 }}
                    transition={{ duration: 0.65, delay: 0.08 * index }}
                    className="rounded-[1.8rem] border border-white/10 bg-white/[0.04] px-5 py-5 shadow-[0_24px_80px_-44px_rgba(0,0,0,0.82)] backdrop-blur-xl"
                  >
                    <div className="text-[10px] uppercase tracking-[0.32em] text-white/42">{metric.label}</div>
                    <div className="mt-3 text-sm font-semibold text-white">{metric.value}</div>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            <motion.div
              initial={reducedMotion ? false : { opacity: 0, y: 26 }}
              animate={reducedMotion ? undefined : { opacity: 1, y: 0 }}
              transition={{ duration: 0.9, delay: 0.1 }}
              className="relative"
            >
              <div className="absolute inset-0 rounded-[2.8rem] bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.22),transparent_34%),radial-gradient(circle_at_bottom_right,rgba(245,158,11,0.18),transparent_36%)] blur-3xl" />
              <div className="relative overflow-hidden rounded-[2.8rem] border border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.06),rgba(255,255,255,0.02))] p-4 shadow-[0_44px_120px_-58px_rgba(0,0,0,0.9)] backdrop-blur-2xl">
                <HeroCommandPanel reducedMotion={Boolean(reducedMotion)} />
              </div>
            </motion.div>
          </div>
        </section>

        <section className="border-t border-white/10 px-4 py-20 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-[1440px]">
            <div className="grid gap-6 lg:grid-cols-3">
              {platformPillars.map((pillar, index) => {
                const Icon = pillar.icon

                return (
                  <motion.article
                    key={pillar.title}
                    initial={reducedMotion ? false : { opacity: 0, y: 24 }}
                    whileInView={reducedMotion ? undefined : { opacity: 1, y: 0 }}
                    viewport={{ once: true, amount: 0.2 }}
                    transition={{ duration: 0.7, delay: index * 0.06 }}
                    className="group relative overflow-hidden rounded-[2.2rem] border border-white/10 bg-white/[0.04] p-7 shadow-[0_32px_90px_-54px_rgba(0,0,0,0.82)] backdrop-blur-xl"
                  >
                    <div className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${pillar.accent} opacity-70`} />
                    <div className="relative">
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-[10px] uppercase tracking-[0.32em] text-white/40">{pillar.eyebrow}</span>
                        <div className="rounded-2xl border border-white/10 bg-white/[0.05] p-3 text-cyan-100">
                          <Icon className="h-5 w-5" />
                        </div>
                      </div>
                      <h2 className="mt-8 text-[1.85rem] font-semibold leading-tight tracking-[-0.04em] text-white">
                        {pillar.title}
                      </h2>
                      <p className="mt-4 text-sm leading-7 text-white/56">{pillar.copy}</p>
                    </div>
                  </motion.article>
                )
              })}
            </div>
          </div>
        </section>

        <section className="px-4 py-20 sm:px-6 lg:px-8">
          <div className="mx-auto grid max-w-[1440px] gap-8 lg:grid-cols-[0.88fr_1.12fr]">
            <motion.div
              initial={reducedMotion ? false : { opacity: 0, y: 24 }}
              whileInView={reducedMotion ? undefined : { opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.25 }}
              transition={{ duration: 0.8 }}
            className="rounded-[2.4rem] border border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.05),rgba(255,255,255,0.02))] p-8 shadow-[0_34px_90px_-56px_rgba(0,0,0,0.84)]"
          >
              <div className="text-[10px] uppercase tracking-[0.34em] text-white/42">Operating rhythm</div>
              <h2 className="mt-5 font-display text-4xl font-semibold leading-tight tracking-[-0.05em] text-white">
                Designed to help people think clearly under market pressure.
              </h2>
              <p className="mt-5 max-w-xl text-base leading-8 text-white/58">
                The system is being shaped around one standard: less friction between information, interpretation, and action.
              </p>

              <div className="mt-10 space-y-4">
                {workflowSteps.map((item, index) => (
                  <motion.div
                    key={item.step}
                    initial={reducedMotion ? false : { opacity: 0, x: -18 }}
                    whileInView={reducedMotion ? undefined : { opacity: 1, x: 0 }}
                    viewport={{ once: true, amount: 0.2 }}
                    transition={{ duration: 0.65, delay: index * 0.08 }}
                    className="rounded-[1.6rem] border border-white/10 bg-white/[0.03] p-5"
                  >
                    <div className="flex items-start gap-4">
                      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full border border-white/10 bg-white/[0.05] text-sm font-semibold text-white">
                        {item.step}
                      </div>
                      <div>
                        <h3 className="text-xl font-semibold tracking-[-0.03em] text-white">{item.title}</h3>
                        <p className="mt-3 text-sm leading-7 text-white/56">{item.text}</p>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            <div className="grid gap-6 md:grid-cols-2">
              {audienceCards.map((item, index) => {
                const Icon = item.icon
                return (
                  <motion.article
                    key={item.title}
                    initial={reducedMotion ? false : { opacity: 0, y: 24 }}
                    whileInView={reducedMotion ? undefined : { opacity: 1, y: 0 }}
                    viewport={{ once: true, amount: 0.2 }}
                    transition={{ duration: 0.7, delay: index * 0.05 }}
                    className="rounded-[2rem] border border-white/10 bg-white/[0.03] p-6 shadow-[0_24px_70px_-46px_rgba(0,0,0,0.82)]"
                  >
                    <div className="inline-flex rounded-2xl border border-white/10 bg-white/[0.05] p-3 text-amber-100">
                      <Icon className="h-5 w-5" />
                    </div>
                    <h3 className="mt-8 text-2xl font-semibold tracking-[-0.03em] text-white">{item.title}</h3>
                    <p className="mt-4 text-sm leading-7 text-white/56">{item.copy}</p>
                  </motion.article>
                )
              })}
            </div>
          </div>
        </section>

        <section className="border-y border-white/10 px-4 py-20 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-[1440px]">
            <motion.div
              initial={reducedMotion ? false : { opacity: 0, y: 18 }}
              whileInView={reducedMotion ? undefined : { opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.25 }}
              transition={{ duration: 0.75 }}
              className="overflow-hidden rounded-[2.6rem] border border-white/10 bg-[linear-gradient(135deg,rgba(255,255,255,0.06),rgba(255,255,255,0.02))] p-8 shadow-[0_44px_120px_-58px_rgba(0,0,0,0.9)] sm:p-10"
            >
              <div className="grid gap-10 lg:grid-cols-[0.98fr_1.02fr]">
                <div>
                  <div className="text-[10px] uppercase tracking-[0.34em] text-white/42">Quality standard</div>
                  <h2 className="mt-5 font-display text-4xl font-semibold leading-tight tracking-[-0.05em] text-white sm:text-5xl">
                    Every layer should feel like part of one system.
                  </h2>
                  <p className="mt-5 max-w-2xl text-base leading-8 text-white/58">
                    That includes performance, access control, predictive workflows, investor tools, competitor intelligence, and the visual polish that tells users they are working inside something serious.
                  </p>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  {systemHighlights.map((item, index) => (
                    <motion.div
                      key={item}
                      initial={reducedMotion ? false : { opacity: 0, scale: 0.98 }}
                      whileInView={reducedMotion ? undefined : { opacity: 1, scale: 1 }}
                      viewport={{ once: true, amount: 0.2 }}
                      transition={{ duration: 0.55, delay: index * 0.04 }}
                      className="flex items-center gap-3 rounded-[1.5rem] border border-white/10 bg-white/[0.04] px-4 py-4 text-sm text-white/74"
                    >
                      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-white/10 bg-white/[0.05]">
                        <ChevronRight className="h-4 w-4" />
                      </span>
                      <span>{item}</span>
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        <section className="px-4 py-20 sm:px-6 lg:px-8 lg:py-24">
          <div className="mx-auto max-w-[1440px]">
            <motion.div
              initial={reducedMotion ? false : { opacity: 0, y: 18 }}
              whileInView={reducedMotion ? undefined : { opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.25 }}
              transition={{ duration: 0.8 }}
              className="relative overflow-hidden rounded-[2.8rem] border border-slate-300/70 bg-[linear-gradient(135deg,rgba(15,23,42,0.96),rgba(15,23,42,0.78))] px-8 py-10 text-white shadow-[0_46px_130px_-62px_rgba(15,23,42,0.42)] dark:border-white/10"
            >
              <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.16),transparent_26%),radial-gradient(circle_at_bottom_right,rgba(245,158,11,0.16),transparent_28%)]" />
              <div className="relative grid gap-8 lg:grid-cols-[1fr_auto] lg:items-end">
                <div>
                  <div className="text-[10px] uppercase tracking-[0.36em] text-white/44">Enter the platform</div>
                  <h2 className="mt-5 font-display text-4xl font-semibold leading-tight tracking-[-0.05em] sm:text-5xl">
                    Start with the public market and news surface, then unlock the full operating stack.
                  </h2>
                  <p className="mt-5 max-w-2xl text-base leading-8 text-white/60">
                    DUBNEWSAI is being shaped as a premium intelligence environment for Dubai. The public face should feel polished. The product underneath should feel fast, sharp, and trustworthy.
                  </p>
                </div>

                <div className="flex flex-col gap-3 sm:flex-row">
                  <Link
                    href="/market"
                    className="inline-flex items-center justify-center rounded-full bg-white px-6 py-3.5 text-sm font-semibold text-slate-950 transition hover:bg-slate-100"
                  >
                    Explore market
                  </Link>
                  <Link
                    href="/register"
                    className="inline-flex items-center justify-center gap-2 rounded-full border border-white/12 bg-white/[0.06] px-6 py-3.5 text-sm font-semibold text-white transition hover:bg-white/[0.1]"
                  >
                    Request access
                    <ArrowRight className="h-4 w-4" />
                  </Link>
                </div>
              </div>
            </motion.div>
          </div>
        </section>
      </main>
    </div>
  )
}

function LandingNav() {
  return (
    <div className="sticky top-0 z-50 px-4 pt-4 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-[1440px] items-center justify-between rounded-full border border-white/10 bg-[#050506]/76 px-4 py-3 shadow-[0_24px_80px_-48px_rgba(0,0,0,0.88)] backdrop-blur-2xl">
        <Link href="/" className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white text-sm font-black text-slate-950">
            DN
          </div>
          <div>
            <div className="font-display text-sm font-bold tracking-[0.28em] text-white">DUBNEWSAI</div>
            <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Dubai intelligence platform</div>
          </div>
        </Link>

        <div className="hidden items-center gap-2 md:flex">
          <LandingNavLink href="/news">News</LandingNavLink>
          <LandingNavLink href="/market">Market</LandingNavLink>
          <LandingNavLink href="/login">Login</LandingNavLink>
          <Link
            href="/register"
            className="inline-flex items-center justify-center rounded-full bg-white px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-slate-100"
          >
            Get access
          </Link>
        </div>
      </div>
    </div>
  )
}

function LandingNavLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link
      href={href}
      className="inline-flex items-center rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm font-medium text-white/66 transition hover:text-white"
    >
      {children}
    </Link>
  )
}

function HeroCommandPanel({ reducedMotion }: { reducedMotion: boolean }) {
  return (
    <div className="relative overflow-hidden rounded-[2.2rem] border border-white/10 bg-[linear-gradient(180deg,rgba(12,16,24,0.98),rgba(8,10,14,0.96))] p-5">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.12),transparent_26%),radial-gradient(circle_at_bottom_right,rgba(245,158,11,0.14),transparent_30%)]" />
      <SparklesCore
        className="pointer-events-none absolute inset-0 h-full w-full opacity-35"
        background="transparent"
        minSize={0.4}
        maxSize={1}
        particleDensity={45}
        particleColor="#ffffff"
        speed={0.5}
      />

      <div className="relative space-y-4">
        <div className="flex items-center justify-between rounded-[1.35rem] border border-white/10 bg-white/[0.04] px-4 py-3">
          <div>
            <div className="text-[10px] uppercase tracking-[0.28em] text-white/40">Live operating surface</div>
            <div className="mt-2 text-sm font-semibold text-white">DUBNEWSAI command brief</div>
          </div>
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-300/30 bg-emerald-300/12 px-3 py-1 text-[10px] uppercase tracking-[0.24em] text-emerald-100/82">
            <BellRing className="h-3.5 w-3.5" />
            Live
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="rounded-[1.7rem] border border-white/10 bg-white/[0.04] p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-[10px] uppercase tracking-[0.28em] text-white/40">Signal blend</div>
                <h3 className="mt-4 font-display text-3xl font-semibold leading-tight tracking-[-0.04em] text-white">
                  From headline to board pressure without losing the thread.
                </h3>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/[0.05] p-3 text-cyan-100">
                <Globe2 className="h-5 w-5" />
              </div>
            </div>

            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              {[
                ["News flow", "Dubai, UAE, GCC"],
                ["Markets", "DFM, ADX, FX"],
                ["Context", "Macro, sentiment, property"]
              ].map(([label, value]) => (
                <div key={label} className="rounded-[1.1rem] border border-white/10 bg-white/[0.03] px-3 py-3">
                  <div className="text-[10px] uppercase tracking-[0.24em] text-white/38">{label}</div>
                  <div className="mt-2 text-sm font-medium text-white/82">{value}</div>
                </div>
              ))}
            </div>

            <div className="mt-6 rounded-[1.4rem] border border-white/10 bg-[linear-gradient(135deg,rgba(34,211,238,0.1),rgba(255,255,255,0.03))] p-4">
              <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Today&apos;s market read</div>
              <div className="mt-3 flex items-start gap-3">
                <Radar className="mt-1 h-4 w-4 text-amber-400" />
                <p className="text-sm leading-7 text-white/60">
                  Dubai intelligence now feels like one connected decision system instead of separate feeds, dashboards, and tabs.
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <FloatingPanel reducedMotion={reducedMotion} delay={0} title="Watched names" kicker="DFM focus">
              {[ 
                ["EMAAR", "+1.84%", "text-emerald-600 dark:text-emerald-300"],
                ["ALDAR", "+0.92%", "text-emerald-600 dark:text-emerald-300"],
                ["DAMAC", "Alert", "text-amber-600 dark:text-amber-200"]
              ].map(([symbol, move, tone]) => (
                <div key={symbol} className="flex items-center justify-between rounded-[1rem] border border-white/10 bg-white/[0.03] px-3 py-3">
                  <span className="text-sm font-semibold text-white">{symbol}</span>
                  <span className={`text-xs font-medium ${tone}`}>{move}</span>
                </div>
              ))}
            </FloatingPanel>

            <FloatingPanel reducedMotion={reducedMotion} delay={0.08} title="Platform posture" kicker="System quality">
              {[
                "Provider-aware confidence",
                "Per-user access control",
                "Investor and competitor intelligence"
              ].map((item) => (
                <div key={item} className="flex items-center gap-3 rounded-[1rem] border border-white/10 bg-white/[0.03] px-3 py-3 text-sm text-white/66">
                  <span className="h-2 w-2 rounded-full bg-cyan-400" />
                  <span>{item}</span>
                </div>
              ))}
            </FloatingPanel>
          </div>
        </div>
      </div>
    </div>
  )
}

function FloatingPanel({
  reducedMotion,
  delay,
  title,
  kicker,
  children
}: {
  reducedMotion: boolean
  delay: number
  title: string
  kicker: string
  children: ReactNode
}) {
  return (
    <motion.div
      initial={reducedMotion ? false : { opacity: 0, y: 18 }}
      animate={reducedMotion ? undefined : { opacity: 1, y: 0 }}
      transition={{ duration: 0.65, delay }}
      className="rounded-[1.7rem] border border-white/10 bg-white/[0.04] p-5 shadow-[0_20px_60px_-42px_rgba(0,0,0,0.82)]"
    >
      <div className="text-[10px] uppercase tracking-[0.28em] text-white/40">{kicker}</div>
      <div className="mt-3 text-lg font-semibold text-white">{title}</div>
      <div className="mt-4 space-y-3">{children}</div>
    </motion.div>
  )
}
