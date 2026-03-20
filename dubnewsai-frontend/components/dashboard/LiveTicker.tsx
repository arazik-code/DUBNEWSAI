"use client"

import { motion } from "framer-motion"
import { Activity, ArrowUpRight, TrendingDown, TrendingUp } from "lucide-react"
import Link from "next/link"

import { useMarketData } from "@/lib/hooks/useMarketData"
import { formatCompactCurrency } from "@/lib/utils/formatters"

export function LiveTicker() {
  const { data: stocks, isLoading } = useMarketData(12)

  if (isLoading) {
    return <TickerSkeleton />
  }

  const items = stocks?.length ? stocks : []
  const marqueeItems = [...items, ...items]

  return (
    <section className="panel-deep overflow-hidden p-4 sm:p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[10px] uppercase tracking-[0.3em] text-white/54">
            <Activity className="h-3.5 w-3.5 text-emerald-300" />
            Market pulse ribbon
          </div>
          <p className="mt-3 text-sm text-white/58">Track the names moving across Dubai and the wider watchlist without leaving the dashboard.</p>
        </div>
        <div className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-xs text-white/72">
          {items.length} symbols in rotation
        </div>
      </div>

      <div className="relative mt-5 overflow-hidden [mask-image:linear-gradient(to_right,transparent,white_12%,white_88%,transparent)]">
        <motion.div
          className="flex w-max gap-4"
          animate={{ x: ["0%", "-50%"] }}
          transition={{
            x: {
              repeat: Infinity,
              repeatType: "loop",
              duration: 28,
              ease: "linear"
            }
          }}
        >
          {marqueeItems.map((stock, index) => (
            <TickerItem key={`${stock.symbol}-${index}`} stock={stock} />
          ))}
        </motion.div>
      </div>
    </section>
  )
}

function TickerItem({
  stock
}: {
  stock: { symbol: string; name?: string; price: number; change: number; change_percent: number; currency?: string; is_live_data?: boolean }
}) {
  const isPositive = stock.change >= 0

  return (
    <Link
      href={`/market/${stock.symbol}`}
      className="group flex min-w-[17rem] items-center justify-between rounded-[1.6rem] border border-white/10 bg-white/[0.04] px-4 py-4 transition hover:bg-white/[0.07]"
    >
      <div>
        <div className="text-[10px] uppercase tracking-[0.28em] text-white/40">{stock.name || "Market signal"}</div>
        <div className="mt-2 text-lg font-semibold text-white">{stock.symbol}</div>
      </div>

      {stock.is_live_data === false ? (
        <div className="text-right">
          <div className="text-sm font-medium uppercase tracking-[0.18em] text-amber-200/82">Verified snapshot</div>
          <div className="mt-2 inline-flex items-center gap-1 text-xs text-white/42">
            Reference board
            <ArrowUpRight className="h-3.5 w-3.5" />
          </div>
        </div>
      ) : (
        <div className="text-right">
          <div className="text-lg font-semibold text-white">{formatCompactCurrency(stock.price, stock.currency || "AED")}</div>
          <div className={`mt-2 inline-flex items-center gap-1 text-xs font-medium ${isPositive ? "text-emerald-300" : "text-red-300"}`}>
            {isPositive ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}
            {Math.abs(stock.change_percent).toFixed(2)}%
          </div>
        </div>
      )}
    </Link>
  )
}

function TickerSkeleton() {
  return (
    <div className="panel-deep animate-pulse p-5">
      <div className="h-24 rounded-[1.5rem] bg-white/5" />
    </div>
  )
}
