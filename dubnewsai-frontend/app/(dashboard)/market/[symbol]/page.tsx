"use client"

import { TrendingDown, TrendingUp } from "lucide-react"

import { LoadingSpinner } from "@/components/shared/LoadingSpinner"
import { useMarketSymbol } from "@/lib/hooks/useMarketData"
import { formatCompactCurrency, formatCompactNumber, formatDateTime } from "@/lib/utils/formatters"

interface MarketSymbolPageProps {
  params: {
    symbol: string
  }
}

export default function MarketSymbolPage({ params }: MarketSymbolPageProps) {
  const symbol = params.symbol.toUpperCase()
  const { data, isLoading } = useMarketSymbol(symbol)

  if (isLoading) {
    return (
      <div className="panel p-8">
        <LoadingSpinner />
      </div>
    )
  }

  if (!data) {
    return (
      <div className="panel p-8">
        <p className="text-sm text-red-500">Symbol not found.</p>
      </div>
    )
  }

  const positive = data.change >= 0
  const hasLiveData = data.is_live_data !== false

  return (
    <div className="space-y-6">
      <section className="panel p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-[0.25em] text-cyber-500">Symbol Detail</p>
            <h1 className="mt-2 text-4xl font-display font-semibold text-slate-950 dark:text-white">{data.symbol}</h1>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">{data.name}</p>
          </div>

          <div className="text-right">
            {hasLiveData ? (
              <>
                <div className="text-4xl font-display font-semibold text-slate-950 dark:text-white">
                  {formatCompactCurrency(data.price)}
                </div>
                <div className={`mt-2 inline-flex items-center gap-2 text-sm font-medium ${positive ? "text-emerald-500" : "text-red-500"}`}>
                  {positive ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                  {data.change_percent.toFixed(2)}%
                </div>
              </>
            ) : (
              <div className="text-sm font-medium uppercase tracking-[0.25em] text-amber-600 dark:text-amber-300">
                Live pricing unavailable
              </div>
            )}
          </div>
        </div>

        {!hasLiveData ? (
          <p className="mt-4 text-sm text-amber-700 dark:text-amber-300">
            This symbol is on the Dubai watchlist, but the current market provider is not returning live pricing for it.
          </p>
        ) : null}
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <article className="panel p-5">
          <p className="text-sm text-slate-500 dark:text-slate-400">Change</p>
          <p className="mt-3 text-3xl font-display font-semibold text-slate-950 dark:text-white">{data.change.toFixed(2)}</p>
        </article>
        <article className="panel p-5">
          <p className="text-sm text-slate-500 dark:text-slate-400">Volume</p>
          <p className="mt-3 text-3xl font-display font-semibold text-slate-950 dark:text-white">{formatCompactNumber(data.volume)}</p>
        </article>
        <article className="panel p-5">
          <p className="text-sm text-slate-500 dark:text-slate-400">Market Cap</p>
          <p className="mt-3 text-3xl font-display font-semibold text-slate-950 dark:text-white">
            {data.market_cap ? formatCompactCurrency(data.market_cap) : "N/A"}
          </p>
        </article>
        <article className="panel p-5">
          <p className="text-sm text-slate-500 dark:text-slate-400">Updated</p>
          <p className="mt-3 text-xl font-display font-semibold text-slate-950 dark:text-white">{formatDateTime(data.data_timestamp)}</p>
        </article>
      </section>
    </div>
  )
}
