"use client"

import { type ReactNode, useMemo, useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { AlertTriangle, Building2, Crosshair, Newspaper, Plus, ShieldAlert, Swords, TrendingUp } from "lucide-react"

import { AuthGuard } from "@/components/auth/AuthGuard"
import { PremiumPageHero } from "@/components/ui/premium-page-hero"
import { apiClient } from "@/lib/api/client"
import { useCompetitorAnalysis, useCompetitors } from "@/lib/hooks/useEnterprise"
import { formatCompactCurrency, formatDateTime, titleCase } from "@/lib/utils/formatters"

export default function CompetitorsPage() {
  const queryClient = useQueryClient()
  const { data: competitors = [] } = useCompetitors()
  const [selectedId, setSelectedId] = useState<number | undefined>(undefined)
  const [form, setForm] = useState({
    name: "Sobha Realty",
    sector: "Real Estate",
    industry: "Real Estate",
    ticker_symbol: "",
    headquarters: "Dubai",
    market_share_percent: 6,
    revenue_growth_rate: 14
  })
  const selected = useMemo(() => competitors.find((item) => item.id === selectedId) || competitors[0], [competitors, selectedId])
  const { data: analysis } = useCompetitorAnalysis(selected?.id)

  const createCompetitor = useMutation({
    mutationFn: async () => {
      await apiClient.post("/competitors", {
        ...form,
        ticker_symbol: form.ticker_symbol || null
      })
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["competitors"] })
    }
  })

  return (
    <AuthGuard>
      <div className="space-y-8">
        <PremiumPageHero
          eyebrow="Competitive intelligence"
          title="Map rival momentum, media pressure, and strategic exposure from one premium command surface."
          description="Track developers, exchanges, and adjacent players through SWOT automation, news intelligence, threat scoring, and market-position context built directly on the DUBNEWSAI graph."
          chips={["SWOT automation", "Threat scoring", "Narrative drift", "Market position"]}
          stats={[
            { label: "Tracked competitors", value: `${competitors.length}`, hint: "Seeded and manually added profiles" },
            { label: "Threat level", value: titleCase(analysis?.threat_assessment.threat_level || "pending"), hint: "Current read on selected competitor pressure" },
            { label: "Top rival", value: selected?.name || "None", hint: selected?.sector || "Select a competitor to inspect" },
            { label: "Recent mentions", value: `${analysis?.news_intelligence.total_mentions ?? 0}`, hint: "Coverage counted over the recent analysis window" }
          ]}
          tone="rose"
        />

        <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
          <article className="panel-premium p-6 sm:p-8">
            <p className="story-kicker">Competitor registry</p>
            <h2 className="mt-4 text-3xl font-semibold text-white">Tracked companies and strategic peers</h2>
            <div className="mt-6 space-y-3">
              {competitors.map((competitor) => (
                <button
                  key={competitor.id}
                  onClick={() => setSelectedId(competitor.id)}
                  className={`w-full rounded-[1.5rem] border p-4 text-left transition ${
                    selected?.id === competitor.id ? "border-rose-300/30 bg-rose-300/[0.08]" : "border-white/10 bg-white/[0.03]"
                  }`}
                >
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <div className="text-sm font-medium text-white">{competitor.name}</div>
                      <div className="mt-1 text-xs uppercase tracking-[0.22em] text-white/40">
                        {competitor.sector || "Sector pending"} {competitor.ticker_symbol ? `· ${competitor.ticker_symbol}` : ""}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-white/66">{competitor.market_share_percent?.toFixed(1) || "0"}%</div>
                      <div className="text-xs text-white/40">share</div>
                    </div>
                  </div>
                </button>
              ))}
            </div>

            <div className="mt-8 rounded-[1.6rem] border border-white/10 bg-white/[0.03] p-5">
              <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Add competitor</div>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <Field label="Name">
                  <input className="input-premium" value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} />
                </Field>
                <Field label="Sector">
                  <input className="input-premium" value={form.sector} onChange={(event) => setForm((current) => ({ ...current, sector: event.target.value }))} />
                </Field>
                <Field label="Industry">
                  <input className="input-premium" value={form.industry} onChange={(event) => setForm((current) => ({ ...current, industry: event.target.value }))} />
                </Field>
                <Field label="Ticker">
                  <input className="input-premium" value={form.ticker_symbol} onChange={(event) => setForm((current) => ({ ...current, ticker_symbol: event.target.value.toUpperCase() }))} />
                </Field>
                <Field label="Headquarters">
                  <input className="input-premium" value={form.headquarters} onChange={(event) => setForm((current) => ({ ...current, headquarters: event.target.value }))} />
                </Field>
                <Field label="Market share %">
                  <input type="number" className="input-premium" value={form.market_share_percent} onChange={(event) => setForm((current) => ({ ...current, market_share_percent: Number(event.target.value) }))} />
                </Field>
              </div>
              <button onClick={() => createCompetitor.mutate()} className="action-premium mt-5">
                <Plus className="h-4 w-4" />
                Add competitor
              </button>
            </div>
          </article>

          <article className="panel-premium p-6 sm:p-8">
            <p className="story-kicker">Selected analysis</p>
            <h2 className="mt-4 text-3xl font-semibold text-white">{selected?.name || "Choose a competitor"}</h2>
            {selected && analysis ? (
              <div className="mt-6 space-y-6">
                <div className="grid gap-4 md:grid-cols-4">
                  <MetricTile label="Market cap" value={selected.market_cap ? formatCompactCurrency(selected.market_cap, "USD") : "N/A"} icon={Building2} />
                  <MetricTile label="Growth" value={`${selected.revenue_growth_rate?.toFixed(1) || "0"}%`} icon={TrendingUp} />
                  <MetricTile label="Threat score" value={`${analysis.threat_assessment.threat_score}`} icon={ShieldAlert} />
                  <MetricTile label="Position" value={titleCase(analysis.swot_analysis.competitive_position || "niche")} icon={Crosshair} />
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <Panel title="Threat factors" icon={ShieldAlert}>
                    {analysis.threat_assessment.threat_factors.map((item) => (
                      <LineItem key={`${item.factor}-${item.description}`} label={item.factor} value={titleCase(item.severity)} text={item.description} />
                    ))}
                  </Panel>
                  <Panel title="Strategic insights" icon={Swords}>
                    {analysis.strategic_insights.map((item) => (
                      <LineItem key={item.title} label={item.title} value={titleCase(item.priority)} text={item.recommendation} />
                    ))}
                  </Panel>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <Panel title="SWOT strengths" icon={TrendingUp}>
                    {analysis.swot_analysis.strengths.map((item) => (
                      <LineItem key={`${item.category}-${item.description}`} label={item.category} value={titleCase(item.impact)} text={item.description} />
                    ))}
                  </Panel>
                  <Panel title="SWOT weaknesses" icon={AlertTriangle}>
                    {analysis.swot_analysis.weaknesses.map((item) => (
                      <LineItem key={`${item.category}-${item.description}`} label={item.category} value={titleCase(item.impact)} text={item.description} />
                    ))}
                  </Panel>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <Panel title="News intelligence" icon={Newspaper}>
                    <MetricRow label="Mentions" value={`${analysis.news_intelligence.total_mentions}`} />
                    <MetricRow label="Average sentiment" value={`${analysis.news_intelligence.average_sentiment.toFixed(2)}`} />
                    <MetricRow label="Coverage trend" value={titleCase(analysis.news_intelligence.coverage_trend)} />
                    <div className="mt-4 flex flex-wrap gap-2">
                      {Object.entries(analysis.news_intelligence.mention_breakdown).map(([key, value]) => (
                        <span key={key} className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/60">
                          {titleCase(key)} {value}
                        </span>
                      ))}
                    </div>
                  </Panel>
                  <Panel title="Top stories" icon={Building2}>
                    {analysis.news_intelligence.top_stories.map((story) => (
                      <div key={`${story.title}-${story.published_at}`} className="rounded-[1.2rem] border border-white/10 bg-white/[0.03] p-3">
                        <div className="text-sm font-medium text-white">{story.title}</div>
                        <div className="mt-2 text-xs text-white/42">
                          {story.source} · {formatDateTime(story.published_at)}
                        </div>
                      </div>
                    ))}
                  </Panel>
                </div>

                <Panel title="Recommended actions" icon={Swords}>
                  <div className="flex flex-wrap gap-2">
                    {analysis.threat_assessment.recommended_actions.map((item) => (
                      <span key={item} className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/64">
                        {item}
                      </span>
                    ))}
                  </div>
                </Panel>
              </div>
            ) : (
              <div className="mt-6 rounded-[1.6rem] border border-dashed border-white/12 bg-white/[0.02] p-6 text-sm text-white/46">
                Select a competitor to see SWOT, narrative pressure, market position, and strategic recommendations.
              </div>
            )}
          </article>
        </section>
      </div>
    </AuthGuard>
  )
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">{label}</div>
      {children}
    </label>
  )
}

function MetricTile({ label, value, icon: Icon }: { label: string; value: string; icon: typeof Building2 }) {
  return (
    <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.03] p-4">
      <div className="inline-flex items-center gap-2 text-[10px] uppercase tracking-[0.28em] text-white/38">
        <Icon className="h-3.5 w-3.5 text-rose-200" />
        {label}
      </div>
      <div className="mt-3 text-xl font-semibold text-white">{value}</div>
    </div>
  )
}

function Panel({ title, icon: Icon, children }: { title: string; icon: typeof Building2; children: ReactNode }) {
  return (
    <div className="rounded-[1.6rem] border border-white/10 bg-white/[0.03] p-5">
      <div className="inline-flex items-center gap-2 text-[10px] uppercase tracking-[0.28em] text-white/38">
        <Icon className="h-3.5 w-3.5 text-rose-200" />
        {title}
      </div>
      <div className="mt-4 space-y-3">{children}</div>
    </div>
  )
}

function LineItem({ label, value, text }: { label: string; value: string; text: string }) {
  return (
    <div className="rounded-[1.2rem] border border-white/10 bg-white/[0.02] p-3">
      <div className="flex items-center justify-between gap-4">
        <div className="text-sm font-medium text-white">{label}</div>
        <div className="text-xs uppercase tracking-[0.2em] text-white/40">{value}</div>
      </div>
      <div className="mt-2 text-sm leading-7 text-white/56">{text}</div>
    </div>
  )
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-white/8 pb-3 last:border-b-0 last:pb-0">
      <div className="text-xs uppercase tracking-[0.2em] text-white/40">{label}</div>
      <div className="text-sm text-white/70">{value}</div>
    </div>
  )
}
