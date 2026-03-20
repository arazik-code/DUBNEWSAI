 "use client"

import { useState } from "react"
import { BrainCircuit, Radar, TrendingUp } from "lucide-react"

import { LiveTicker } from "@/components/dashboard/LiveTicker"
import { MarketOverview } from "@/components/dashboard/MarketOverview"
import { PropertyValuationStudio } from "@/components/intelligence/PropertyValuationStudio"
import { PremiumPageHero } from "@/components/ui/premium-page-hero"
import { useMarketTrend, usePricePrediction, usePropertyTrend } from "@/lib/hooks/useEnterprise"
import { formatCompactCurrency, titleCase } from "@/lib/utils/formatters"

export default function MarketPage() {
  const [predictionSymbol, setPredictionSymbol] = useState("EMAAR.DU")
  const [predictionLocation, setPredictionLocation] = useState("Dubai Marina")
  const { data: pricePrediction } = usePricePrediction(predictionSymbol)
  const { data: marketTrend } = useMarketTrend("UAE")
  const { data: propertyTrend } = usePropertyTrend(predictionLocation, "apartment")

  return (
    <div className="space-y-8">
      <PremiumPageHero
        eyebrow="Market command"
        title="Track Dubai markets with the context serious decisions require."
        description="Follow UAE-listed names, global real-estate benchmarks, FX, macro indicators, and Dubai weather in one board built to help you brief fast and go deep when needed."
        chips={["UAE boards", "Global real-estate", "Macro signals", "FX + weather"]}
        stats={[
          {
            label: "Primary lens",
            value: "UAE + GCC capital flow",
            hint: "Focused on local developers and the broader capital picture"
          },
          {
            label: "Context layer",
            value: "Macro + FX + weather",
            hint: "The surrounding signals that shape price interpretation"
          },
          {
            label: "Decision speed",
            value: "Brief in seconds",
            hint: "Provider, quality, and fallback visibility stay in the interface"
          },
          {
            label: "Coverage mode",
            value: "Signal, then depth",
            hint: "Start with the snapshot and expand only when necessary"
          }
        ]}
        tone="amber"
      />

      <LiveTicker />
      <MarketOverview />
      <section className="grid gap-6 xl:grid-cols-[1.04fr_0.96fr]">
        <article className="panel-premium p-6 sm:p-8">
          <p className="story-kicker">Predictive layer</p>
          <h2 className="mt-4 text-3xl font-semibold text-white">Statistical outlooks for the symbols you actually watch</h2>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <label className="block">
              <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">Symbol</div>
              <input className="input-premium" value={predictionSymbol} onChange={(event) => setPredictionSymbol(event.target.value.toUpperCase())} />
            </label>
            <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
              <div className="inline-flex items-center gap-2 text-[10px] uppercase tracking-[0.28em] text-white/38">
                <BrainCircuit className="h-3.5 w-3.5 text-amber-200" />
                Market outlook
              </div>
              <div className="mt-3 text-xl font-semibold text-white">{titleCase(marketTrend?.prediction || "pending")}</div>
              <p className="mt-3 text-sm leading-7 text-white/56">{marketTrend?.recommendation}</p>
            </div>
          </div>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <ForecastTile label="Target price" value={pricePrediction ? formatCompactCurrency(pricePrediction.prediction.target_price, "AED") : "Pending"} icon={TrendingUp} />
            <ForecastTile label="Expected return" value={pricePrediction ? `${pricePrediction.prediction.expected_return_percent.toFixed(2)}%` : "Pending"} icon={Radar} />
            <ForecastTile label="Confidence" value={pricePrediction ? `${(pricePrediction.model_info.r_squared * 100).toFixed(0)}% fit` : "Pending"} icon={BrainCircuit} />
          </div>
        </article>

        <article className="panel-premium p-6 sm:p-8">
          <p className="story-kicker">Property trend</p>
          <h2 className="mt-4 text-3xl font-semibold text-white">Location-level appreciation outlook</h2>
          <label className="mt-6 block">
            <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">Location</div>
            <input className="input-premium" value={predictionLocation} onChange={(event) => setPredictionLocation(event.target.value)} />
          </label>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <ForecastTile label="Current average" value={propertyTrend ? formatCompactCurrency(propertyTrend.current_avg_price, "AED") : "Pending"} icon={TrendingUp} />
            <ForecastTile label="12M appreciation" value={propertyTrend ? `${propertyTrend.forecast_12m.expected_appreciation.toFixed(2)}%` : "Pending"} icon={Radar} />
          </div>
          <div className="mt-6 rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
            <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Trend narrative</div>
            <p className="mt-3 text-sm leading-7 text-white/58">
              {propertyTrend
                ? `${predictionLocation} is screening as ${propertyTrend.forecast_12m.trend} with ${propertyTrend.confidence} confidence and ${propertyTrend.data_quality.data_points} historical points supporting the estimate.`
                : "Enter a location to generate the property trend outlook."}
            </p>
          </div>
        </article>
      </section>
      <PropertyValuationStudio />
    </div>
  )
}

function ForecastTile({
  label,
  value,
  icon: Icon
}: {
  label: string
  value: string
  icon: typeof BrainCircuit
}) {
  return (
    <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.03] p-4">
      <div className="inline-flex items-center gap-2 text-[10px] uppercase tracking-[0.28em] text-white/38">
        <Icon className="h-3.5 w-3.5 text-amber-200" />
        {label}
      </div>
      <div className="mt-3 text-xl font-semibold text-white">{value}</div>
    </div>
  )
}
