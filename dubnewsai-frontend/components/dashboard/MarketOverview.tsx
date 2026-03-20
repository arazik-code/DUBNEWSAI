"use client"

import type { ReactNode } from "react"
import Link from "next/link"
import { CloudSun, Landmark, TrendingDown, TrendingUp } from "lucide-react"

import { useMarketOverview } from "@/lib/hooks/useMarketData"
import { formatCompactCurrency, formatCompactNumber, titleCase } from "@/lib/utils/formatters"
import type { CurrencyRate, EconomicIndicator, MarketStock } from "@/types"

function ChangeBadge({ value }: { value: number }) {
  const positive = value >= 0

  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium ${positive ? "bg-emerald-500/10 text-emerald-300" : "bg-red-500/10 text-red-300"}`}>
      {positive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
      {Math.abs(value).toFixed(2)}%
    </span>
  )
}

function ProviderLabel({ provider, fallback }: { provider?: string | null; fallback?: boolean }) {
  if (fallback) {
    return (
      <span className="rounded-full border border-amber-300/15 bg-amber-300/10 px-2.5 py-1 text-[10px] uppercase tracking-[0.18em] text-amber-200/82">
        Reference snapshot
      </span>
    )
  }

  if (!provider) {
    return null
  }

  return (
    <span className="rounded-full border border-cyan-300/15 bg-cyan-300/10 px-2.5 py-1 text-[10px] uppercase tracking-[0.18em] text-cyan-100/82">
      {titleCase(provider)}
    </span>
  )
}

function SummaryTile({ title, value, caption }: { title: string; value: string; caption: string }) {
  return (
    <div className="rounded-[1.6rem] border border-white/10 bg-white/[0.03] p-4">
      <div className="text-[10px] uppercase tracking-[0.28em] text-white/40">{title}</div>
      <div className="mt-3 text-2xl font-semibold text-white">{value}</div>
      <div className="mt-2 text-sm text-white/46">{caption}</div>
    </div>
  )
}

function BoardRow({ stock }: { stock: MarketStock }) {
  const fallback = stock.is_live_data === false

  return (
    <Link
      href={`/market/${stock.symbol}`}
      className="group grid gap-3 rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-4 transition hover:bg-white/[0.06] lg:grid-cols-[1.3fr_0.9fr_0.7fr]"
    >
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-base font-semibold text-white">{stock.symbol}</span>
          <ProviderLabel provider={stock.primary_provider} fallback={fallback} />
        </div>
        <div className="mt-2 text-sm text-white/58">{stock.name}</div>
        <div className="mt-2 flex flex-wrap items-center gap-3 text-[11px] uppercase tracking-[0.18em] text-white/36">
          {stock.exchange ? <span>{stock.exchange}</span> : null}
          {stock.asset_class ? <span>{titleCase(stock.asset_class)}</span> : null}
          {stock.region ? <span>{stock.region}</span> : null}
        </div>
      </div>

      <div className="space-y-1 text-sm text-white/52">
        {fallback ? (
          <>
            <div className="text-sm font-medium uppercase tracking-[0.18em] text-amber-200/82">Last verified snapshot</div>
            {stock.price > 0 ? <div className="text-xl font-semibold text-white">{formatCompactCurrency(stock.price, stock.currency || "AED")}</div> : null}
            <div>{stock.data_source === "historical_snapshot" ? "Stored market snapshot" : "Reference board coverage"}</div>
          </>
        ) : (
          <>
            <div className="text-xl font-semibold text-white">{formatCompactCurrency(stock.price, stock.currency || "AED")}</div>
            <div>{formatCompactNumber(stock.volume)} volume</div>
            {stock.market_cap ? <div>{formatCompactNumber(stock.market_cap)} market cap</div> : null}
          </>
        )}
      </div>

      <div className="flex flex-col items-start gap-2 lg:items-end">
        {!fallback ? <ChangeBadge value={stock.change_percent} /> : null}
        {stock.data_quality_score !== undefined && stock.data_quality_score !== null ? (
          <span className="text-xs text-white/40">Quality {stock.data_quality_score.toFixed(0)}%</span>
        ) : null}
      </div>
    </Link>
  )
}

function BoardCard({
  title,
  subtitle,
  stocks
}: {
  title: string
  subtitle: string
  stocks: MarketStock[]
}) {
  return (
    <section className="panel-premium min-w-0 p-6">
      <div className="mb-5 flex items-end justify-between gap-3">
        <div>
          <div className="text-[10px] uppercase tracking-[0.32em] text-white/42">{title}</div>
          <p className="mt-2 text-sm text-white/56">{subtitle}</p>
        </div>
        <div className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs text-white/66">{stocks.length} symbols</div>
      </div>

      {stocks.length ? (
        <div className="space-y-3">
          {stocks.map((stock) => (
            <BoardRow key={stock.symbol} stock={stock} />
          ))}
        </div>
      ) : (
        <div className="rounded-[1.3rem] border border-white/10 bg-white/[0.03] px-4 py-4 text-sm text-white/56">
          No live rows are available for this board right now.
        </div>
      )}
    </section>
  )
}

function StackPanel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="panel-premium p-5">
      <div className="text-[10px] uppercase tracking-[0.32em] text-white/42">{title}</div>
      <div className="mt-5 space-y-4">{children}</div>
    </section>
  )
}

function CurrencyGrid({ currencies }: { currencies: CurrencyRate[] }) {
  return (
    <StackPanel title="FX and currency">
      {currencies.length ? (
        <div className="grid gap-3 sm:grid-cols-2">
          {currencies.map((currency) => (
            <div key={`${currency.from_currency}-${currency.to_currency}`} className="rounded-[1.3rem] border border-white/10 bg-white/[0.03] px-4 py-3">
              <div className="text-sm font-semibold text-white">{currency.from_currency}/{currency.to_currency}</div>
              <div className="mt-2 text-sm text-white/56">{formatCompactNumber(currency.rate)}</div>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-[1.3rem] border border-white/10 bg-white/[0.03] px-4 py-4 text-sm text-white/56">
          Currency rates are temporarily unavailable.
        </div>
      )}
    </StackPanel>
  )
}

function IndicatorList({ indicators }: { indicators: EconomicIndicator[] }) {
  return (
    <StackPanel title="Macro indicators">
      {indicators.length ? (
        indicators.map((indicator) => (
          <div key={indicator.indicator_code} className="flex items-start justify-between gap-3 rounded-[1.2rem] border border-white/10 bg-white/[0.03] px-4 py-3">
            <div>
              <div className="text-sm font-semibold text-white">{indicator.indicator_name}</div>
              <div className="mt-1 text-xs text-white/42">{indicator.country} | {indicator.source || "Macro feed"}</div>
            </div>
            <div className="text-right text-sm font-medium text-white">{formatCompactNumber(indicator.value)}</div>
          </div>
        ))
      ) : (
        <div className="rounded-[1.2rem] border border-white/10 bg-white/[0.03] px-4 py-4 text-sm text-white/56">
          Macro indicators are not available yet.
        </div>
      )}
    </StackPanel>
  )
}

export function MarketOverview({ compact = false }: { compact?: boolean }) {
  const { data, isLoading } = useMarketOverview()
  const hasFallbackOnly = Boolean(data?.stocks.length) && Boolean(data?.stocks.every((stock) => stock.is_live_data === false))
  const stocks = compact ? (data?.stocks || []).slice(0, 6) : (data?.stocks || [])
  const globalRealEstate = compact ? (data?.global_real_estate || []).slice(0, 4) : (data?.global_real_estate || [])
  const indices = compact ? (data?.indices || []).slice(0, 3) : (data?.indices || [])
  const currencies = compact ? (data?.currencies || []).slice(0, 4) : (data?.currencies || [])
  const indicators = compact ? (data?.economic_indicators || []).slice(0, 4) : (data?.economic_indicators || [])
  const commodities = compact ? [] : (data?.commodities || [])

  if (isLoading) {
    return <div className="panel-premium h-96 animate-pulse bg-white/[0.03]" />
  }

  if (compact) {
    return (
      <section className="min-w-0 space-y-6">
        <div className="panel-premium relative overflow-hidden p-6 sm:p-7">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.1),transparent_24%),radial-gradient(circle_at_bottom_right,rgba(245,158,11,0.1),transparent_22%)]" />
          <div className="relative">
            <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
              <div className="max-w-3xl">
                <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[10px] uppercase tracking-[0.3em] text-white/54">
                  <Landmark className="h-3.5 w-3.5 text-cyan-200" />
                  Market snapshot
                </div>
                <h3 className="mt-4 text-balance text-3xl font-semibold text-white sm:text-[2.2rem]">
                  The dashboard keeps the essentials close and sends the deep read to the full market board.
                </h3>
                <p className="mt-4 max-w-2xl text-sm leading-7 text-white/56 sm:text-base">
                  Watch the most important UAE names, read current FX and macro context, and jump into the dedicated market page when you need the full board.
                </p>
              </div>

              <Link
                href="/market"
                className="inline-flex items-center justify-center rounded-full bg-white px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-white/92"
              >
                Open full market board
              </Link>
            </div>

            <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <SummaryTile title="UAE board" value={`${stocks.length}`} caption="Most relevant symbols on the dashboard" />
              <SummaryTile title="Indices" value={`${indices.length}`} caption="Core benchmarks shown in quick view" />
              <SummaryTile title="FX pairs" value={`${currencies.length}`} caption="AED and major crosses" />
              <SummaryTile title="Macro signals" value={`${indicators.length}`} caption="High-level context for decisions" />
            </div>
          </div>
        </div>

        {hasFallbackOnly ? (
          <div className="rounded-[1.6rem] border border-amber-300/20 bg-amber-300/10 px-4 py-3 text-sm text-amber-200/82">
            Some local symbols are currently showing the latest verified snapshot while upstream boards refresh.
          </div>
        ) : null}

        <div className="grid min-w-0 gap-6 xl:grid-cols-[1.25fr_0.75fr]">
          <div className="min-w-0 space-y-6">
            <BoardCard title="UAE market board" subtitle="The names most likely to matter first on a normal operating day" stocks={stocks} />
            <BoardCard title="Global real-estate context" subtitle="A compact international read for benchmark comparison" stocks={globalRealEstate} />
          </div>

          <div className="min-w-0 space-y-6">
            {data?.weather ? (
              <section className="panel-premium overflow-hidden p-5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-[10px] uppercase tracking-[0.32em] text-white/42">Dubai weather</div>
                    <div className="mt-3 text-4xl font-semibold text-white">{data.weather.temperature_c.toFixed(1)}C</div>
                    <div className="mt-2 text-sm text-white/56">{data.weather.weather_summary}</div>
                  </div>
                  <CloudSun className="h-8 w-8 text-amber-200" />
                </div>
              </section>
            ) : null}

            <StackPanel title="Indices">
              {indices.map((index) => (
                <div key={index.symbol} className="flex items-start justify-between gap-3 rounded-[1.2rem] border border-white/10 bg-white/[0.03] px-4 py-3">
                  <div>
                    <div className="text-sm font-semibold text-white">{index.symbol}</div>
                    <div className="mt-1 text-xs text-white/42">{index.name}</div>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <div className="text-sm font-medium text-white">{formatCompactCurrency(index.price, index.currency || "USD")}</div>
                    <ChangeBadge value={index.change_percent} />
                  </div>
                </div>
              ))}
            </StackPanel>

            <CurrencyGrid currencies={currencies} />
            <IndicatorList indicators={indicators} />
          </div>
        </div>
      </section>
    )
  }

  return (
    <section className="min-w-0 space-y-6">
      <div className="panel-premium relative overflow-hidden p-6 sm:p-8">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.1),transparent_24%),radial-gradient(circle_at_bottom_right,rgba(245,158,11,0.1),transparent_22%)]" />
        <div className="relative">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
            <div className="max-w-3xl">
              <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[10px] uppercase tracking-[0.3em] text-white/54">
                <Landmark className="h-3.5 w-3.5 text-cyan-200" />
                Market intelligence board
              </div>
              <h3 className="mt-4 text-balance text-3xl font-semibold text-white sm:text-4xl">
                Read Dubai-listed names with the context that usually lives across five different tabs.
              </h3>
              <p className="mt-4 text-sm leading-7 text-white/56 sm:text-base">
                DUBNEWSAI combines UAE boards, global real-estate context, FX, weather, and macro signals so you can move from headline to pricing context without leaving the platform.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              {data?.market_status?.uae_markets ? (
                <span className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-xs uppercase tracking-[0.22em] text-white/72">
                  UAE {data.market_status.uae_markets}
                </span>
              ) : null}
              {data?.market_status?.us_markets ? (
                <span className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-xs uppercase tracking-[0.22em] text-white/72">
                  US {data.market_status.us_markets}
                </span>
              ) : null}
              {data?.weather ? (
                <span className="inline-flex items-center gap-2 rounded-full border border-cyan-300/15 bg-cyan-300/10 px-4 py-2 text-xs uppercase tracking-[0.22em] text-cyan-100/82">
                  <CloudSun className="h-3.5 w-3.5" />
                  Dubai {data.weather.temperature_c.toFixed(0)}C
                </span>
              ) : null}
            </div>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <SummaryTile title="Tracked boards" value={`${data?.stocks.length || 0}`} caption="UAE symbols in the active board" />
            <SummaryTile title="Global context" value={`${data?.global_real_estate.length || 0}`} caption="Cross-market real-estate names" />
            <SummaryTile title="FX coverage" value={`${data?.currencies.length || 0}`} caption="AED and major cross pairs" />
            <SummaryTile title="Macro set" value={`${data?.economic_indicators.length || 0}`} caption="Economic indicators feeding context" />
          </div>
        </div>
      </div>

      {hasFallbackOnly ? (
        <div className="rounded-[1.6rem] border border-amber-300/20 bg-amber-300/10 px-4 py-3 text-sm text-amber-200/82">
          Some local symbols are currently showing the latest verified snapshot while upstream boards refresh.
        </div>
      ) : null}

      <div className="grid min-w-0 gap-6 2xl:grid-cols-[1.7fr_1fr]">
        <div className="min-w-0 space-y-6">
          <BoardCard title="UAE market board" subtitle="DFM and ADX coverage for developers, banks, and high-signal names" stocks={stocks} />
          <BoardCard title="Global real-estate board" subtitle="REITs and homebuilders for international context" stocks={globalRealEstate} />
        </div>

        <div className="min-w-0 space-y-6">
          {data?.weather ? (
            <section className="panel-premium overflow-hidden p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-[10px] uppercase tracking-[0.32em] text-white/42">Dubai market weather</div>
                  <div className="mt-3 text-4xl font-semibold text-white">{data.weather.temperature_c.toFixed(1)}C</div>
                  <div className="mt-2 text-sm text-white/56">{data.weather.weather_summary}</div>
                </div>
                <CloudSun className="h-8 w-8 text-amber-200" />
              </div>
              <div className="mt-5 grid gap-3 sm:grid-cols-3">
                <SummaryTile title="Feels like" value={`${data.weather.apparent_temperature_c?.toFixed(1) ?? "--"}C`} caption="Perceived temperature" />
                <SummaryTile title="Humidity" value={`${data.weather.humidity_percent ?? "--"}%`} caption="Current moisture" />
                <SummaryTile title="Wind" value={`${data.weather.wind_speed_kph?.toFixed(1) ?? "--"} km/h`} caption="Surface conditions" />
              </div>
            </section>
          ) : null}

          <StackPanel title="Indices">
            {indices.map((index) => (
              <div key={index.symbol} className="flex items-start justify-between gap-3 rounded-[1.2rem] border border-white/10 bg-white/[0.03] px-4 py-3">
                <div>
                  <div className="text-sm font-semibold text-white">{index.symbol}</div>
                  <div className="mt-1 text-xs text-white/42">{index.name}</div>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <div className="text-sm font-medium text-white">{formatCompactCurrency(index.price, index.currency || "USD")}</div>
                  <ChangeBadge value={index.change_percent} />
                </div>
              </div>
            ))}
          </StackPanel>

          <CurrencyGrid currencies={currencies} />
          <IndicatorList indicators={indicators} />

          <StackPanel title="Commodities">
            {commodities.length ? (
              commodities.map((commodity) => (
                <div key={commodity.symbol} className="flex items-start justify-between gap-3 rounded-[1.2rem] border border-white/10 bg-white/[0.03] px-4 py-3">
                  <div>
                    <div className="text-sm font-semibold text-white">{commodity.name}</div>
                    <div className="mt-1 text-xs text-white/42">{commodity.symbol}</div>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <div className="text-sm font-medium text-white">{formatCompactCurrency(commodity.price, commodity.currency || "USD")}</div>
                    <ChangeBadge value={commodity.change_percent} />
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-[1.2rem] border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-white/56">
                Commodity boards are refreshing. The platform will surface the latest verified commodity rows as soon as the active feed responds.
              </div>
            )}
          </StackPanel>

          <StackPanel title="Coverage snapshot">
            <div className="grid gap-3 sm:grid-cols-2">
              <SummaryTile title="Stored equities" value={`${stocks.length + globalRealEstate.length}`} caption="Tracked across UAE and global boards" />
              <SummaryTile title="Macro + FX" value={`${indicators.length + currencies.length}`} caption="Context modules active" />
            </div>
          </StackPanel>
        </div>
      </div>
    </section>
  )
}
