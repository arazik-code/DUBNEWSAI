"use client"

import { Landmark, TrendingDown, TrendingUp } from "lucide-react"

import { useMarketData } from "@/lib/hooks/useMarketData"
import { formatCompactCurrency } from "@/lib/utils/formatters"

export function MarketOverview() {
  const { data } = useMarketData(4)
  const hasFallbackOnly = Boolean(data?.length) && Boolean(data?.every((stock) => stock.is_live_data === false))

  return (
    <section className="panel p-5">
      <div className="mb-5 flex items-center gap-2">
        <Landmark className="h-4 w-4 text-cyber-500" />
        <h3 className="text-lg font-display font-semibold text-slate-950 dark:text-white">Market Overview</h3>
      </div>

      {hasFallbackOnly ? (
        <div className="mb-4 rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-700 dark:text-amber-300">
          Watchlist symbols are loaded, but live UAE pricing is not available from the current market data provider.
        </div>
      ) : null}

      <div className="space-y-3">
        {data?.slice(0, 4).map((stock) => {
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
    </section>
  )
}
