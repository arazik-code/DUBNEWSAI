"use client"

import { useQuery } from "@tanstack/react-query"
import { motion } from "framer-motion"
import { Activity, BarChart3, BrainCircuit, Radar, Sparkles, Waves } from "lucide-react"

import { AuthGuard } from "@/components/auth/AuthGuard"
import { PremiumPageHero } from "@/components/ui/premium-page-hero"
import { apiClient } from "@/lib/api/client"
import { titleCase } from "@/lib/utils/formatters"

interface AnalyticsOverview {
  mood: {
    score: number
    label: string
    summary: string
    drivers: {
      positive_percent: number
      negative_percent: number
      neutral_percent: number
      leading_categories: { category: string; count: number; share_percent: number }[]
      leading_keywords: { keyword: string; count: number; trend_score: number }[]
    }
  }
  sentiment_distribution: {
    positive: number
    neutral: number
    negative: number
    total: number
    positive_percent: number
    neutral_percent: number
    negative_percent: number
  }
  trends: { keyword: string; count: number; trend_score: number }[]
  category_distribution: { category: string; count: number; share_percent: number }[]
  sentiment_timeline: { date: string; positive: number; neutral: number; negative: number; total: number }[]
  provider_distribution: { provider: string; count: number; share_percent: number }[]
}

export default function AnalyticsPage() {
  const { data } = useQuery<AnalyticsOverview>({
    queryKey: ["analytics", "overview"],
    queryFn: async () => {
      const response = await apiClient.get<AnalyticsOverview>("/analytics/overview", { params: { days: 7 } })
      return response.data
    }
  })

  const mood = data?.mood
  const sentiment = data?.sentiment_distribution
  const maxTimeline = Math.max(...(data?.sentiment_timeline.map((item) => item.total) || [1]))
  const maxCategory = Math.max(...(data?.category_distribution.map((item) => item.share_percent) || [1]))

  return (
    <AuthGuard>
      <div className="space-y-8">
        <PremiumPageHero
          eyebrow="Analytics command"
          title="Market intelligence should explain pressure, direction, and narrative concentration in one place."
          description={
            mood?.summary ||
            "Analytics now ties sentiment, topical concentration, provider mix, and story momentum into a single market brief instead of presenting isolated percentages."
          }
          chips={[
            mood?.label || "Balanced",
            "Topic momentum",
            "Provider mix",
            "Seven-day narrative"
          ]}
          stats={[
            {
              label: "Mood score",
              value: mood ? `${mood.score}` : "0",
              hint: mood?.label || "No narrative summary yet"
            },
            {
              label: "Positive share",
              value: `${sentiment?.positive_percent ?? 0}%`,
              hint: "Constructive coverage across the active article pool"
            },
            {
              label: "Negative share",
              value: `${sentiment?.negative_percent ?? 0}%`,
              hint: "Stress coverage and downside pressure"
            },
            {
              label: "Analyzed pool",
              value: `${sentiment?.total ?? 0}`,
              hint: "Stories feeding the intelligence layer"
            }
          ]}
          tone="emerald"
        />

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <StatTile icon={BrainCircuit} label="Narrative mood" value={mood?.label || "Balanced"} hint="Derived from sentiment spread and dominant themes" />
          <StatTile icon={Sparkles} label="Trend themes" value={`${data?.trends.length ?? 0}`} hint="Cleaned keyword set without stopword noise" />
          <StatTile icon={Radar} label="Providers active" value={`${data?.provider_distribution.length ?? 0}`} hint="News mix contributing to the intelligence graph" />
          <StatTile icon={Activity} label="Timeline points" value={`${data?.sentiment_timeline.length ?? 0}`} hint="Daily sentiment checkpoints across the last week" />
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <article className="panel-premium p-6 sm:p-8">
            <p className="story-kicker">Mood engine</p>
            <h2 className="mt-4 text-3xl font-semibold text-white">How the market is reading right now</h2>
            <p className="mt-5 max-w-3xl text-base leading-8 text-white/58">
              {mood?.summary ||
                "As the article pool refreshes, DUBNEWSAI will translate sentiment distribution and topic concentration into a clearer market brief."}
            </p>
            <div className="mt-6 overflow-hidden rounded-full border border-white/10 bg-white/[0.04]">
              <div className="flex h-6 w-full">
                <div className="bg-emerald-400" style={{ width: `${sentiment?.positive_percent ?? 0}%` }} />
                <div className="bg-cyan-400" style={{ width: `${sentiment?.neutral_percent ?? 0}%` }} />
                <div className="bg-rose-400" style={{ width: `${sentiment?.negative_percent ?? 0}%` }} />
              </div>
            </div>
            <div className="mt-6 grid gap-4 md:grid-cols-3">
              <InsightTile label="Positive" value={`${sentiment?.positive_percent ?? 0}%`} description="Coverage aligned with growth, demand, and constructive flow." />
              <InsightTile label="Neutral" value={`${sentiment?.neutral_percent ?? 0}%`} description="Information-heavy updates without a sharp directional bias." />
              <InsightTile label="Negative" value={`${sentiment?.negative_percent ?? 0}%`} description="Pressure stories, risks, or downside framing in the cycle." />
            </div>
          </article>

          <article className="panel-premium p-6 sm:p-8">
            <p className="story-kicker">Leading themes</p>
            <h2 className="mt-4 text-3xl font-semibold text-white">What is driving the graph</h2>
            <div className="mt-6 space-y-3">
              {(mood?.drivers.leading_keywords || data?.trends || []).slice(0, 6).map((trend, index) => (
                <motion.div
                  key={trend.keyword}
                  initial={{ opacity: 0, x: -12 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true, amount: 0.2 }}
                  transition={{ duration: 0.4, delay: index * 0.06 }}
                  className="flex items-center justify-between rounded-[1.5rem] border border-white/10 bg-white/[0.03] px-4 py-4"
                >
                  <div>
                    <div className="text-sm font-medium text-white">{trend.keyword}</div>
                    <div className="mt-1 text-xs uppercase tracking-[0.2em] text-white/38">Trend score {trend.trend_score}</div>
                  </div>
                  <div className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/62">{trend.count}x</div>
                </motion.div>
              ))}
            </div>
          </article>
        </section>

        <section className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
          <article className="panel-premium p-6 sm:p-8">
            <p className="story-kicker">Category flow</p>
            <h2 className="mt-4 text-3xl font-semibold text-white">Which parts of the story graph are dominating</h2>
            <div className="mt-6 space-y-4">
              {(data?.category_distribution || []).map((item) => (
                <div key={item.category}>
                  <div className="mb-2 flex items-center justify-between gap-3 text-sm">
                    <span className="font-medium text-white">{titleCase(item.category)}</span>
                    <span className="text-white/52">{item.share_percent}%</span>
                  </div>
                  <div className="h-3 overflow-hidden rounded-full bg-white/[0.05]">
                    <div className="h-full rounded-full bg-gradient-to-r from-cyan-300 via-emerald-300 to-amber-200" style={{ width: `${(item.share_percent / maxCategory) * 100}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </article>

          <article className="panel-premium p-6 sm:p-8">
            <p className="story-kicker">Sentiment timeline</p>
            <h2 className="mt-4 text-3xl font-semibold text-white">How the weekly narrative has been moving</h2>
            <div className="mt-6 grid grid-cols-[repeat(auto-fit,minmax(72px,1fr))] gap-3">
              {(data?.sentiment_timeline || []).map((point) => (
                <div key={point.date} className="rounded-[1.4rem] border border-white/10 bg-white/[0.03] p-3">
                  <div className="text-[10px] uppercase tracking-[0.24em] text-white/38">{point.date.slice(5)}</div>
                  <div className="mt-4 flex h-32 items-end gap-1">
                    <TimelineBar color="bg-emerald-400" value={point.positive} max={maxTimeline} />
                    <TimelineBar color="bg-cyan-400" value={point.neutral} max={maxTimeline} />
                    <TimelineBar color="bg-rose-400" value={point.negative} max={maxTimeline} />
                  </div>
                  <div className="mt-3 text-xs text-white/52">{point.total} stories</div>
                </div>
              ))}
            </div>
          </article>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          <article className="panel-premium p-6 sm:p-8">
            <p className="story-kicker">Provider mix</p>
            <h2 className="mt-4 text-3xl font-semibold text-white">Which feeds are shaping the current picture</h2>
            <div className="mt-6 space-y-3">
              {(data?.provider_distribution || []).slice(0, 8).map((item) => (
                <div key={item.provider} className="flex items-center justify-between rounded-[1.4rem] border border-white/10 bg-white/[0.03] px-4 py-4">
                  <div>
                    <div className="text-sm font-medium text-white">{titleCase(item.provider)}</div>
                    <div className="mt-1 text-xs uppercase tracking-[0.2em] text-white/38">{item.count} stories</div>
                  </div>
                  <div className="text-sm text-white/62">{item.share_percent}%</div>
                </div>
              ))}
            </div>
          </article>

          <article className="panel-premium p-6 sm:p-8">
            <p className="story-kicker">Operator read</p>
            <h2 className="mt-4 text-3xl font-semibold text-white">What to do with this</h2>
            <div className="mt-6 space-y-4">
              <OperatorCard
                icon={BarChart3}
                title="Use mood and category flow together"
                text="A positive score matters more when real-estate or market categories are also dominating the story mix."
              />
              <OperatorCard
                icon={Waves}
                title="Watch the timeline for sudden pivots"
                text="A swing from neutral-heavy to negative-heavy days often signals a narrative shift before the dashboard feels it."
              />
              <OperatorCard
                icon={Radar}
                title="Read provider concentration carefully"
                text="If one source family dominates the graph, treat the narrative as concentrated rather than fully diversified."
              />
            </div>
          </article>
        </section>
      </div>
    </AuthGuard>
  )
}

function StatTile({
  icon: Icon,
  label,
  value,
  hint
}: {
  icon: typeof BrainCircuit
  label: string
  value: string
  hint: string
}) {
  return (
    <article className="panel-premium p-5">
      <div className="inline-flex items-center gap-2 text-[10px] uppercase tracking-[0.3em] text-white/40">
        <Icon className="h-3.5 w-3.5 text-cyan-200" />
        {label}
      </div>
      <div className="mt-4 text-3xl font-semibold text-white">{value}</div>
      <div className="mt-2 text-sm text-white/48">{hint}</div>
    </article>
  )
}

function InsightTile({ label, value, description }: { label: string; value: string; description: string }) {
  return (
    <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.03] p-4">
      <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">{label}</div>
      <div className="mt-3 text-2xl font-semibold text-white">{value}</div>
      <p className="mt-3 text-sm leading-7 text-white/56">{description}</p>
    </div>
  )
}

function TimelineBar({ color, value, max }: { color: string; value: number; max: number }) {
  const height = Math.max(10, (value / max) * 100)
  return <div className={`w-full rounded-full ${color}`} style={{ height: `${height}%` }} />
}

function OperatorCard({
  icon: Icon,
  title,
  text
}: {
  icon: typeof BarChart3
  title: string
  text: string
}) {
  return (
    <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-4">
      <div className="inline-flex items-center gap-2 text-[10px] uppercase tracking-[0.28em] text-white/38">
        <Icon className="h-3.5 w-3.5 text-amber-200" />
        {title}
      </div>
      <p className="mt-3 text-sm leading-7 text-white/58">{text}</p>
    </div>
  )
}
