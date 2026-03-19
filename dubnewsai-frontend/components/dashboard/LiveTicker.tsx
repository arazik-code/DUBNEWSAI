"use client"

import { motion } from "framer-motion"
import { TrendingDown, TrendingUp } from "lucide-react"

import { useMarketData } from "@/lib/hooks/useMarketData"

export function LiveTicker() {
  const { data: stocks, isLoading } = useMarketData()

  if (isLoading) {
    return <TickerSkeleton />
  }

  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 p-4 dark:bg-slate-950">
      <div className="mb-2 flex items-center gap-2">
        <div className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
        <span className="text-xs font-medium uppercase tracking-[0.25em] text-slate-400">Live Market Data</span>
      </div>
      <div className="relative overflow-hidden">
        <motion.div
          className="flex gap-6"
          animate={{ x: [0, -1000] }}
          transition={{
            x: {
              repeat: Infinity,
              repeatType: "loop",
              duration: 20,
              ease: "linear"
            }
          }}
        >
          {stocks?.map((stock) => (
            <TickerItem key={stock.symbol} stock={stock} />
          ))}
          {stocks?.map((stock) => (
            <TickerItem key={`${stock.symbol}-dup`} stock={stock} />
          ))}
        </motion.div>
      </div>
    </div>
  )
}

function TickerItem({
  stock
}: {
  stock: { symbol: string; price: number; change: number; change_percent: number; is_live_data?: boolean }
}) {
  if (stock.is_live_data === false) {
    return (
      <div className="flex shrink-0 items-center gap-3">
        <span className="text-sm font-bold text-white">{stock.symbol}</span>
        <span className="text-xs uppercase tracking-[0.2em] text-amber-300">Awaiting feed</span>
      </div>
    )
  }

  const isPositive = stock.change >= 0

  return (
    <div className="flex shrink-0 items-center gap-3">
      <span className="text-sm font-bold text-white">{stock.symbol}</span>
      <span className="text-sm text-slate-400">{stock.price.toFixed(2)}</span>
      <div className={`flex items-center gap-1 text-xs font-medium ${isPositive ? "text-emerald-400" : "text-red-400"}`}>
        {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
        {Math.abs(stock.change_percent).toFixed(2)}%
      </div>
    </div>
  )
}

function TickerSkeleton() {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900 p-4 animate-pulse">
      <div className="h-16 rounded-xl bg-slate-800" />
    </div>
  )
}
