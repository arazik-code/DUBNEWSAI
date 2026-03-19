"use client"

import { Landmark, TrendingDown, TrendingUp } from "lucide-react"

import { useMarketOverview } from "@/lib/hooks/useMarketData"
import { formatCompactCurrency, formatCompactNumber } from "@/lib/utils/formatters"

export function MarketOverview() {
  const { data } = useMarketOverview()
  const hasFallbackOnly = Boolean(data?.stocks.length) && Boolean(data?.stocks.every((stock) => stock.is_live_data === false))

  return (
    <section className="panel space-y-6 p-5">
      <div className="mb-5 flex items-center gap-2">
        <Landmark className="h-4 w-4 text-cyber-500" />
        <h3 className="text-lg font-display font-semibold text-slate-950 dark:text-white">Market Overview</h3>
      </div>

      {hasFallbackOnly ? (
        <div className="mb-4 rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-700 dark:text-amber-300">
          Watchlist symbols are loaded, but live UAE pricing is not available from the current market data provider.
        </div>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        <div className="space-y-3">
          <p className="text-xs font-medium uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">Core Stocks</p>
          {data?.stocks.slice(0, 6).map((stock) => {
            const positive = stock.change >= 0
            const hasLiveData = stock.is_live_data !== false

            return (
              <div
                key={stock.symbol}
                className="flex items-center justify-between rounded-2xl border border-white/10 bg-slate-950/5 p-3 dark:bg-white/5"
              >
                <div>
                  <div className="font-semibold text-slate-900 dark:text-white">{stock.symbol}</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">{stock.name}</div>
                </div>
                <div className="text-right">
                  {hasLiveData ? (
                    <>
                      <div className="font-medium text-slate-900 dark:text-white">{formatCompactCurrency(stock.price)}</div>
                      <div className={`inline-flex items-center gap-1 text-xs ${positive ? "text-emerald-500" : "text-red-500"}`}>
                        {positive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                        {stock.change_percent.toFixed(2)}%
                      </div>
                    </>
                  ) : (
                    <div className="text-xs font-medium uppercase tracking-[0.2em] text-amber-600 dark:text-amber-300">
                      Awaiting live feed
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        <div className="space-y-4">
          <div className="rounded-2xl border border-white/10 bg-slate-950/5 p-4 dark:bg-white/5">
            <p className="text-xs font-medium uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">Indices</p>
            <div className="mt-3 space-y-3">
              {data?.indices.slice(0, 4).map((index) => (
                <div key={index.symbol} className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-slate-900 dark:text-white">{index.symbol}</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">{index.name}</div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium text-slate-900 dark:text-white">{formatCompactCurrency(index.price)}</div>
                    <div className={`text-xs ${index.change >= 0 ? "text-emerald-500" : "text-red-500"}`}>
                      {index.change_percent.toFixed(2)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-slate-950/5 p-4 dark:bg-white/5">
            <p className="text-xs font-medium uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">FX Pairs</p>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              {data?.currencies.slice(0, 6).map((currency) => (
                <div key={`${currency.from_currency}-${currency.to_currency}`} className="rounded-xl border border-white/10 px-3 py-2">
                  <div className="text-sm font-semibold text-slate-900 dark:text-white">
                    {currency.from_currency}/{currency.to_currency}
                  </div>
                  <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">{formatCompactNumber(currency.rate)}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-white/10 bg-slate-950/5 p-4 dark:bg-white/5">
            <p className="text-xs font-medium uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">Macro Signals</p>
            <div className="mt-3 space-y-2">
              {data?.economic_indicators.slice(0, 6).map((indicator) => (
                <div key={indicator.indicator_code} className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-slate-900 dark:text-white">{indicator.indicator_name}</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">{indicator.country} | {indicator.source || "Macro"}</div>
                  </div>
                  <div className="text-right text-sm font-medium text-slate-900 dark:text-white">
                    {formatCompactNumber(indicator.value)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
