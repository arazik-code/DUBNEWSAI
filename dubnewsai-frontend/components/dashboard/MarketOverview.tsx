"use client"

import type { ReactNode } from "react"
import { Activity, CloudSun, Landmark, TrendingDown, TrendingUp } from "lucide-react"

import { useMarketOverview } from "@/lib/hooks/useMarketData"
import { formatCompactCurrency, formatCompactNumber, titleCase } from "@/lib/utils/formatters"
import type { CurrencyRate, EconomicIndicator, MarketStock } from "@/types"

function ChangeBadge({ value }: { value: number }) {
  const positive = value >= 0

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium ${
        positive ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500"
      }`}
    >
      {positive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
      {Math.abs(value).toFixed(2)}%
    </span>
  )
}

function ProviderLabel({ provider, fallback }: { provider?: string | null; fallback?: boolean }) {
  if (fallback) {
    return (
      <span className="rounded-full bg-amber-500/10 px-2 py-1 text-[11px] font-medium uppercase tracking-[0.18em] text-amber-600 dark:text-amber-300">
        Watchlist fallback
      </span>
    )
  }

  if (!provider) {
    return null
  }

  return (
    <span className="rounded-full bg-cyber-500/10 px-2 py-1 text-[11px] font-medium uppercase tracking-[0.18em] text-cyber-600 dark:text-cyber-300">
      {titleCase(provider)}
    </span>
  )
}

function StockTable({
  title,
  subtitle,
  stocks
}: {
  title: string
  subtitle: string
  stocks: MarketStock[]
}) {
  return (
    <div className="rounded-3xl border border-white/10 bg-slate-950/5 p-4 dark:bg-white/5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">{title}</p>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{subtitle}</p>
        </div>
        <div className="rounded-full bg-white/60 px-3 py-1 text-xs font-medium text-slate-600 dark:bg-slate-900/60 dark:text-slate-300">
          {stocks.length} symbols
        </div>
      </div>

      <div className="space-y-3">
        {stocks.map((stock) => {
          const fallback = stock.is_live_data === false

          return (
            <div
              key={stock.symbol}
              className="grid gap-3 rounded-2xl border border-white/10 bg-white/60 p-4 dark:bg-slate-950/40 lg:grid-cols-[1.4fr_0.9fr_0.8fr]"
            >
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-base font-semibold text-slate-900 dark:text-white">{stock.symbol}</span>
                  <ProviderLabel provider={stock.primary_provider} fallback={fallback} />
                  {stock.region ? (
                    <span className="text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
                      {stock.region}
                    </span>
                  ) : null}
                </div>
                <div className="text-sm text-slate-600 dark:text-slate-300">{stock.name}</div>
                <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
                  {stock.exchange ? <span>{stock.exchange.toUpperCase()}</span> : null}
                  {stock.asset_class ? <span>{titleCase(stock.asset_class)}</span> : null}
                  {stock.confidence_level ? <span>{titleCase(stock.confidence_level)} confidence</span> : null}
                </div>
              </div>

              <div className="space-y-1 text-sm text-slate-600 dark:text-slate-300">
                {fallback ? (
                  <div className="text-sm font-medium uppercase tracking-[0.2em] text-amber-600 dark:text-amber-300">
                    Awaiting live quote
                  </div>
                ) : (
                  <>
                    <div className="text-xl font-semibold text-slate-950 dark:text-white">{formatCompactCurrency(stock.price, stock.currency || "AED")}</div>
                    <div>{formatCompactNumber(stock.volume)} volume</div>
                    {stock.market_cap ? <div>{formatCompactNumber(stock.market_cap)} market cap</div> : null}
                  </>
                )}
              </div>

              <div className="flex flex-col items-start gap-2 lg:items-end">
                {!fallback ? <ChangeBadge value={stock.change_percent} /> : null}
                {stock.data_quality_score !== undefined && stock.data_quality_score !== null ? (
                  <span className="text-xs text-slate-500 dark:text-slate-400">
                    Quality {stock.data_quality_score.toFixed(0)}%
                  </span>
                ) : null}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function CompactMetricCard({
  title,
  children
}: {
  title: string
  children: ReactNode
}) {
  return (
    <div className="rounded-3xl border border-white/10 bg-slate-950/5 p-4 dark:bg-white/5">
      <p className="text-xs font-medium uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">{title}</p>
      <div className="mt-4 space-y-3">{children}</div>
    </div>
  )
}

function CurrencyGrid({ currencies }: { currencies: CurrencyRate[] }) {
  return (
    <CompactMetricCard title="FX and Currency">
      <div className="grid gap-3 sm:grid-cols-2">
        {currencies.map((currency) => (
          <div key={`${currency.from_currency}-${currency.to_currency}`} className="rounded-2xl border border-white/10 px-3 py-3">
            <div className="text-sm font-semibold text-slate-900 dark:text-white">
              {currency.from_currency}/{currency.to_currency}
            </div>
            <div className="mt-1 text-sm text-slate-600 dark:text-slate-300">{formatCompactNumber(currency.rate)}</div>
          </div>
        ))}
      </div>
    </CompactMetricCard>
  )
}

function IndicatorList({ indicators }: { indicators: EconomicIndicator[] }) {
  return (
    <CompactMetricCard title="Macro and Economic Indicators">
      {indicators.map((indicator) => (
        <div key={indicator.indicator_code} className="flex items-start justify-between gap-3">
          <div>
            <div className="text-sm font-semibold text-slate-900 dark:text-white">{indicator.indicator_name}</div>
            <div className="text-xs text-slate-500 dark:text-slate-400">
              {indicator.country} | {indicator.source || "Macro feed"}
            </div>
          </div>
          <div className="text-right text-sm font-medium text-slate-900 dark:text-white">
            {formatCompactNumber(indicator.value)}
          </div>
        </div>
      ))}
    </CompactMetricCard>
  )
}

export function MarketOverview() {
  const { data } = useMarketOverview()
  const hasFallbackOnly = Boolean(data?.stocks.length) && Boolean(data?.stocks.every((stock) => stock.is_live_data === false))

  return (
    <section className="panel space-y-6 p-5">
      <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Landmark className="h-4 w-4 text-cyber-500" />
            <h3 className="text-lg font-display font-semibold text-slate-950 dark:text-white">Market Intelligence Overview</h3>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Multi-source UAE equities, global real estate, FX, commodities, macro signals, and Dubai market weather.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {data?.market_status?.uae_markets ? (
            <span className="rounded-full bg-white/60 px-3 py-2 text-xs font-medium uppercase tracking-[0.18em] text-slate-600 dark:bg-slate-900/60 dark:text-slate-300">
              UAE {data.market_status.uae_markets}
            </span>
          ) : null}
          {data?.market_status?.us_markets ? (
            <span className="rounded-full bg-white/60 px-3 py-2 text-xs font-medium uppercase tracking-[0.18em] text-slate-600 dark:bg-slate-900/60 dark:text-slate-300">
              US {data.market_status.us_markets}
            </span>
          ) : null}
          {data?.weather ? (
            <span className="inline-flex items-center gap-2 rounded-full bg-cyber-500/10 px-3 py-2 text-xs font-medium uppercase tracking-[0.18em] text-cyber-600 dark:text-cyber-300">
              <CloudSun className="h-3.5 w-3.5" />
              Dubai {data.weather.temperature_c.toFixed(0)}C
            </span>
          ) : null}
        </div>
      </div>

      {hasFallbackOnly ? (
        <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-700 dark:text-amber-300">
          UAE watchlist coverage is present, but several local symbols are still falling back to watchlist metadata until an upstream live provider returns a valid quote.
        </div>
      ) : null}

      <div className="grid gap-6 2xl:grid-cols-[1.8fr_1fr]">
        <div className="space-y-6">
          <StockTable
            title="UAE Market Board"
            subtitle="DFM and ADX coverage for developers, banks, and core market names"
            stocks={data?.stocks || []}
          />

          <StockTable
            title="Global Real Estate"
            subtitle="International REITs and homebuilder coverage for cross-market context"
            stocks={data?.global_real_estate || []}
          />
        </div>

        <div className="space-y-6">
          {data?.weather ? (
            <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-cyber-500/10 via-white/70 to-gold-500/10 p-4 dark:from-cyber-500/10 dark:via-slate-950/70 dark:to-gold-500/10">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-medium uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">Dubai Market Weather</p>
                  <div className="mt-2 text-3xl font-semibold text-slate-950 dark:text-white">
                    {data.weather.temperature_c.toFixed(1)}C
                  </div>
                  <div className="mt-1 text-sm text-slate-600 dark:text-slate-300">{data.weather.weather_summary}</div>
                </div>
                <CloudSun className="h-8 w-8 text-gold-500" />
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-3">
                <div className="rounded-2xl border border-white/10 px-3 py-3">
                  <div className="text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Feels Like</div>
                  <div className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">
                    {data.weather.apparent_temperature_c?.toFixed(1) ?? "--"}C
                  </div>
                </div>
                <div className="rounded-2xl border border-white/10 px-3 py-3">
                  <div className="text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Humidity</div>
                  <div className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">
                    {data.weather.humidity_percent ?? "--"}%
                  </div>
                </div>
                <div className="rounded-2xl border border-white/10 px-3 py-3">
                  <div className="text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Wind</div>
                  <div className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">
                    {data.weather.wind_speed_kph?.toFixed(1) ?? "--"} km/h
                  </div>
                </div>
              </div>
            </div>
          ) : null}

          <CompactMetricCard title="Indices">
            {(data?.indices || []).map((index) => (
              <div key={index.symbol} className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-slate-900 dark:text-white">{index.symbol}</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">{index.name}</div>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <div className="text-sm font-medium text-slate-900 dark:text-white">{formatCompactCurrency(index.price, index.currency || "USD")}</div>
                  <ChangeBadge value={index.change_percent} />
                </div>
              </div>
            ))}
          </CompactMetricCard>

          <CurrencyGrid currencies={data?.currencies || []} />
          <IndicatorList indicators={data?.economic_indicators || []} />

          <CompactMetricCard title="Commodities">
            {(data?.commodities || []).map((commodity) => (
              <div key={commodity.symbol} className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-slate-900 dark:text-white">{commodity.name}</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">{commodity.symbol}</div>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <div className="text-sm font-medium text-slate-900 dark:text-white">{formatCompactCurrency(commodity.price, commodity.currency || "USD")}</div>
                  <ChangeBadge value={commodity.change_percent} />
                </div>
              </div>
            ))}
          </CompactMetricCard>

          <CompactMetricCard title="Coverage Snapshot">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl border border-white/10 px-3 py-3">
                <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
                  <Activity className="h-3.5 w-3.5" />
                  Stored equities
                </div>
                <div className="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">
                  {(data?.stocks.length || 0) + (data?.global_real_estate.length || 0)}
                </div>
              </div>
              <div className="rounded-2xl border border-white/10 px-3 py-3">
                <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
                  <CloudSun className="h-3.5 w-3.5" />
                  Macro + FX
                </div>
                <div className="mt-2 text-2xl font-semibold text-slate-950 dark:text-white">
                  {(data?.economic_indicators.length || 0) + (data?.currencies.length || 0)}
                </div>
              </div>
            </div>
          </CompactMetricCard>
        </div>
      </div>
    </section>
  )
}
