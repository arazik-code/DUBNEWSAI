"use client"

import Link from "next/link"
import { ArrowLeft, Clock3, Layers3, ScanSearch, ShieldCheck, TrendingDown, TrendingUp } from "lucide-react"

import { LoadingSpinner } from "@/components/shared/LoadingSpinner"
import { PremiumPageHero } from "@/components/ui/premium-page-hero"
import { useMarketSymbol } from "@/lib/hooks/useMarketData"
import { formatCompactCurrency, formatCompactNumber, formatDateTime, titleCase } from "@/lib/utils/formatters"

interface MarketSymbolPageProps {
  params: {
    symbol: string
  }
}

function buildNarrative(data: {
  symbol: string
  name: string
  price: number
  change_percent: number
  volume: number
  exchange?: string | null
  region?: string | null
  primary_provider?: string | null
  is_live_data?: boolean
  data_source?: string
}) {
  const movement =
    data.change_percent >= 1.5
      ? "is pushing higher with conviction"
      : data.change_percent <= -1.5
        ? "is under visible pressure"
        : "is trading in a more measured band"
  const freshness = data.is_live_data === false ? "latest verified snapshot" : "current active board feed"
  const provider = data.primary_provider ? titleCase(data.primary_provider) : "the current market stack"
  return `${data.name} ${movement} on ${data.exchange || "the monitored exchange"} with ${formatCompactNumber(
    data.volume
  )} volume going through ${freshness}. DUBNEWSAI is currently reading this symbol through ${provider}, so the operator can judge price direction and source trust at the same time.`
}

export default function MarketSymbolPage({ params }: MarketSymbolPageProps) {
  const symbol = params.symbol.toUpperCase()
  const { data, isLoading } = useMarketSymbol(symbol)

  if (isLoading) {
    return (
      <div className="panel-deep p-8">
        <LoadingSpinner />
      </div>
    )
  }

  if (!data) {
    return (
      <div className="panel-deep p-8">
        <p className="text-sm text-red-300">Symbol not found.</p>
      </div>
    )
  }

  const positive = data.change >= 0
  const hasLiveData = data.is_live_data !== false
  const narrative = buildNarrative(data)

  const metricCards = [
    {
      label: "Current price",
      value: data.price > 0 ? formatCompactCurrency(data.price, data.currency || "AED") : "Unavailable",
      accent: positive ? "text-emerald-300" : "text-red-300"
    },
    {
      label: "Session change",
      value: `${data.change_percent.toFixed(2)}%`,
      accent: positive ? "text-emerald-300" : "text-red-300"
    },
    {
      label: "Volume",
      value: formatCompactNumber(data.volume),
      accent: "text-white"
    },
    {
      label: "Previous close",
      value: data.previous_close ? formatCompactCurrency(data.previous_close, data.currency || "AED") : "N/A",
      accent: "text-white"
    }
  ]

  const executionRows = [
    { label: "Exchange", value: data.exchange || "Not tagged" },
    { label: "Region", value: data.region || "Not tagged" },
    { label: "Provider", value: data.primary_provider ? titleCase(data.primary_provider) : "Not available" },
    { label: "Data mode", value: hasLiveData ? "Live board feed" : "Verified snapshot" },
    { label: "Updated", value: formatDateTime(data.data_timestamp) },
    { label: "Confidence", value: data.confidence_level ? titleCase(data.confidence_level) : "N/A" }
  ]

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between gap-4">
        <Link href="/market" className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm font-medium text-white/76 transition hover:text-white">
          <ArrowLeft className="h-4 w-4" />
          Back to market
        </Link>
        <div className={`inline-flex rounded-full border px-4 py-2 text-sm font-medium uppercase tracking-[0.22em] ${hasLiveData ? "border-emerald-300/15 bg-emerald-300/10 text-emerald-200/82" : "border-amber-300/15 bg-amber-300/10 text-amber-200/82"}`}>
          {hasLiveData ? "Live coverage" : "Verified snapshot"}
        </div>
      </div>

      <PremiumPageHero
        eyebrow="Symbol detail"
        title={`${data.symbol} is explained like an active board, not a generic asset page.`}
        description={narrative}
        chips={[
          data.exchange || "Exchange pending",
          data.region || "Region pending",
          data.asset_class ? titleCase(data.asset_class) : "Asset unclassified",
          data.primary_provider ? titleCase(data.primary_provider) : "Provider pending"
        ]}
        stats={[
          {
            label: "Current price",
            value: data.price > 0 ? formatCompactCurrency(data.price, data.currency || "AED") : "Unavailable",
            hint: hasLiveData ? "Current active quote path" : "Latest verified stored snapshot"
          },
          {
            label: "Session move",
            value: `${data.change_percent.toFixed(2)}%`,
            hint: positive ? "Upward session tone" : "Downward session tone"
          },
          {
            label: "Volume",
            value: formatCompactNumber(data.volume),
            hint: "Most recent observable board volume"
          },
          {
            label: "Quality",
            value: data.data_quality_score !== null && data.data_quality_score !== undefined ? `${Math.round(data.data_quality_score)}%` : "N/A",
            hint: "Completeness and provider trust score"
          }
        ]}
        tone={positive ? "emerald" : "rose"}
      />

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metricCards.map((card) => (
          <MetricCard key={card.label} label={card.label} value={card.value} accent={card.accent} />
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-6">
          <article className="panel-premium p-6 sm:p-8">
            <p className="story-kicker">Operator brief</p>
            <h2 className="mt-4 text-3xl font-semibold text-white">What matters right now</h2>
            <p className="mt-5 max-w-3xl text-base leading-8 text-white/58">{narrative}</p>
            <div className="mt-6 grid gap-4 md:grid-cols-3">
              <SignalPill
                icon={positive ? TrendingUp : TrendingDown}
                label="Price tone"
                text={positive ? "Session is leaning constructive" : "Session is leaning defensive"}
              />
              <SignalPill
                icon={Layers3}
                label="Market context"
                text={`${data.exchange || "Exchange"} ${data.asset_class ? titleCase(data.asset_class) : "asset"} coverage`}
              />
              <SignalPill
                icon={Clock3}
                label="Freshness"
                text={hasLiveData ? "Current active board row" : "Latest stored verified snapshot"}
              />
            </div>
          </article>

          <article className="panel-premium p-6 sm:p-8">
            <p className="story-kicker">Session structure</p>
            <h2 className="mt-4 text-3xl font-semibold text-white">Price frame</h2>
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              <ValueTile label="Open" value={data.open_price ? formatCompactCurrency(data.open_price, data.currency || "AED") : "N/A"} />
              <ValueTile label="High" value={data.high_price ? formatCompactCurrency(data.high_price, data.currency || "AED") : "N/A"} />
              <ValueTile label="Low" value={data.low_price ? formatCompactCurrency(data.low_price, data.currency || "AED") : "N/A"} />
              <ValueTile label="Market cap" value={data.market_cap ? formatCompactNumber(data.market_cap) : "N/A"} />
            </div>
          </article>
        </div>

        <div className="space-y-4">
          <div className="panel-premium p-5">
            <div className="story-kicker">Execution context</div>
            <div className="mt-5 space-y-4 text-sm text-white/72">
              {executionRows.map((row) => (
                <InfoRow key={row.label} label={row.label} value={row.value} />
              ))}
            </div>
          </div>

          <div className="panel-premium p-5">
            <div className="story-kicker">Trust layer</div>
            <div className="mt-5 space-y-3 text-sm text-white/58">
              <div className="inline-flex items-center gap-2 rounded-full border border-white/10 px-3 py-2 text-xs text-white/68">
                <ScanSearch className="h-3.5 w-3.5 text-cyan-200" />
                Provider-aware quote path
              </div>
              <div className="inline-flex items-center gap-2 rounded-full border border-white/10 px-3 py-2 text-xs text-white/68">
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-200" />
                Quality and confidence surfaced
              </div>
              <div className="inline-flex items-center gap-2 rounded-full border border-white/10 px-3 py-2 text-xs text-white/68">
                <Clock3 className="h-3.5 w-3.5 text-amber-200" />
                Freshness never hidden
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

function MetricCard({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <article className="panel-premium p-5">
      <p className="text-[10px] uppercase tracking-[0.3em] text-white/40">{label}</p>
      <p className={`mt-4 text-2xl font-semibold ${accent || "text-white"}`}>{value}</p>
    </article>
  )
}

function ValueTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.03] p-4">
      <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">{label}</div>
      <div className="mt-3 text-lg font-medium text-white/84">{value}</div>
    </div>
  )
}

function SignalPill({
  icon: Icon,
  label,
  text
}: {
  icon: typeof TrendingUp
  label: string
  text: string
}) {
  return (
    <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.03] p-4">
      <div className="inline-flex items-center gap-2 text-[10px] uppercase tracking-[0.28em] text-white/38">
        <Icon className="h-3.5 w-3.5 text-cyan-200" />
        {label}
      </div>
      <p className="mt-3 text-sm leading-7 text-white/68">{text}</p>
    </div>
  )
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-white/8 pb-3 last:border-b-0 last:pb-0">
      <span className="text-[10px] uppercase tracking-[0.28em] text-white/38">{label}</span>
      <span className="max-w-[60%] text-right text-sm text-white/82">{value}</span>
    </div>
  )
}
