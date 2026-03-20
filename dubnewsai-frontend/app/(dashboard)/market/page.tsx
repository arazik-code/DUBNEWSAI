"use client"

import { useDeferredValue, useEffect, useMemo, useState } from "react"
import { BrainCircuit, Radar, TrendingUp } from "lucide-react"

import { LiveTicker } from "@/components/dashboard/LiveTicker"
import { MarketOverview } from "@/components/dashboard/MarketOverview"
import { PropertyValuationStudio } from "@/components/intelligence/PropertyValuationStudio"
import { PremiumPageHero } from "@/components/ui/premium-page-hero"
import { useMarketTrend, usePredictionUniverse, usePricePrediction, usePropertyTrend } from "@/lib/hooks/useEnterprise"
import { formatCompactCurrency, titleCase } from "@/lib/utils/formatters"

export default function MarketPage() {
  const { data: predictionUniverse } = usePredictionUniverse()
  const [predictionSymbol, setPredictionSymbol] = useState("")
  const [predictionLocation, setPredictionLocation] = useState("")
  const [predictionPropertyType, setPredictionPropertyType] = useState("Apartment")
  const deferredPredictionSymbol = useDeferredValue(predictionSymbol.trim())
  const deferredPredictionLocation = useDeferredValue(predictionLocation.trim())
  const { data: pricePrediction, isLoading: isPricePredictionLoading, error: pricePredictionError } = usePricePrediction(deferredPredictionSymbol)
  const { data: marketTrend } = useMarketTrend("UAE")
  const { data: propertyTrend, isLoading: isPropertyTrendLoading, error: propertyTrendError } = usePropertyTrend(
    deferredPredictionLocation,
    predictionPropertyType
  )
  const selectedSymbol = useMemo(
    () => predictionUniverse?.symbols.find((item) => item.symbol === predictionSymbol) || predictionUniverse?.symbols[0],
    [predictionSymbol, predictionUniverse?.symbols]
  )
  const selectedLocation = useMemo(
    () => predictionUniverse?.locations.find((item) => item.name === predictionLocation) || predictionUniverse?.locations[0],
    [predictionLocation, predictionUniverse?.locations]
  )

  useEffect(() => {
    if (!predictionSymbol && predictionUniverse?.symbols?.length) {
      setPredictionSymbol(predictionUniverse.symbols[0].symbol)
    }
  }, [predictionSymbol, predictionUniverse?.symbols])

  useEffect(() => {
    if (!predictionLocation && predictionUniverse?.locations?.length) {
      setPredictionLocation(predictionUniverse.locations[0].name)
      setPredictionPropertyType(predictionUniverse.locations[0].supported_types[0] || "Apartment")
    }
  }, [predictionLocation, predictionUniverse?.locations])

  useEffect(() => {
    if (selectedLocation && !selectedLocation.supported_types.includes(predictionPropertyType)) {
      setPredictionPropertyType(selectedLocation.supported_types[0] || "Apartment")
    }
  }, [predictionPropertyType, selectedLocation])

  const targetPrice = pricePrediction?.prediction?.target_price
  const expectedReturn = pricePrediction?.prediction?.expected_return_percent
  const confidenceFit = pricePrediction?.model_info?.r_squared
  const appreciation = propertyTrend?.forecast_12m?.expected_appreciation

  return (
    <div className="space-y-8">
      <PremiumPageHero
        eyebrow="Market command"
        title="Track Dubai markets with the context serious decisions require."
        description="Follow UAE boards, global real-estate benchmarks, macro, FX, and Dubai weather from one live market surface."
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
          <h2 className="mt-4 text-3xl font-semibold text-white">Fast statistical outlooks for watched symbols</h2>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <label className="block">
              <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">Symbol</div>
              <select className="input-premium" value={predictionSymbol} onChange={(event) => setPredictionSymbol(event.target.value)}>
                {(predictionUniverse?.symbols || []).map((item) => (
                  <option key={item.symbol} value={item.symbol}>
                    {item.symbol} - {item.name}
                  </option>
                ))}
              </select>
            </label>
            <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
              <div className="inline-flex items-center gap-2 text-[10px] uppercase tracking-[0.28em] text-white/38">
                <BrainCircuit className="h-3.5 w-3.5 text-amber-200" />
                Market outlook
              </div>
              <div className="mt-3 text-xl font-semibold text-white">{titleCase(marketTrend?.prediction || "pending")}</div>
              <p className="mt-3 text-sm leading-7 text-white/56">{marketTrend?.recommendation || "Generating outlook..."}</p>
              {selectedSymbol ? (
                <div className="mt-4 text-xs text-white/48">
                  {selectedSymbol.exchange || "Exchange"} · {selectedSymbol.sector || "Sector"} · {formatCompactCurrency(selectedSymbol.price, "AED")} · {selectedSymbol.change_percent.toFixed(2)}%
                </div>
              ) : null}
            </div>
          </div>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            <ForecastTile
              label="Target price"
              value={targetPrice !== undefined ? formatCompactCurrency(targetPrice, "AED") : isPricePredictionLoading ? "Loading" : "Unavailable"}
              icon={TrendingUp}
            />
            <ForecastTile
              label="Expected return"
              value={expectedReturn !== undefined ? `${expectedReturn.toFixed(2)}%` : isPricePredictionLoading ? "Loading" : "Unavailable"}
              icon={Radar}
            />
            <ForecastTile
              label="Confidence"
              value={confidenceFit !== undefined ? `${(confidenceFit * 100).toFixed(0)}% fit` : isPricePredictionLoading ? "Loading" : "Unavailable"}
              icon={BrainCircuit}
            />
          </div>
          {pricePredictionError ? <p className="mt-4 text-sm text-rose-300">Prediction unavailable for this symbol right now.</p> : null}
        </article>

        <article className="panel-premium p-6 sm:p-8">
          <p className="story-kicker">Property trend</p>
          <h2 className="mt-4 text-3xl font-semibold text-white">Location-level appreciation outlook</h2>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <label className="block">
              <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">Location</div>
              <select className="input-premium" value={predictionLocation} onChange={(event) => setPredictionLocation(event.target.value)}>
                {(predictionUniverse?.locations || []).map((item) => (
                  <option key={item.name} value={item.name}>
                    {item.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">Property type</div>
              <select className="input-premium" value={predictionPropertyType} onChange={(event) => setPredictionPropertyType(event.target.value)}>
                {(selectedLocation?.supported_types || predictionUniverse?.property_types || []).map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <ForecastTile
              label="Current average"
              value={propertyTrend?.current_avg_price !== undefined ? formatCompactCurrency(propertyTrend.current_avg_price, "AED") : isPropertyTrendLoading ? "Loading" : "Unavailable"}
              icon={TrendingUp}
            />
            <ForecastTile
              label="12M appreciation"
              value={appreciation !== undefined ? `${appreciation.toFixed(2)}%` : isPropertyTrendLoading ? "Loading" : "Unavailable"}
              icon={Radar}
            />
          </div>
          <div className="mt-6 rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
            <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Trend narrative</div>
            <p className="mt-3 text-sm leading-7 text-white/58">
              {propertyTrend?.forecast_12m && propertyTrend?.data_quality
                ? `${predictionLocation} ${predictionPropertyType.toLowerCase()} values are screening as ${propertyTrend.forecast_12m.trend} with ${propertyTrend.confidence} confidence and ${propertyTrend.data_quality.data_points} historical points supporting the estimate.`
                : "Enter a location to generate the property trend outlook."}
            </p>
            {selectedLocation ? (
              <div className="mt-4 text-xs text-white/48">
                Current baseline {formatCompactCurrency(selectedLocation.price_per_sqft, "AED")} / sqft · 30-day location trend {selectedLocation.trend_percent.toFixed(2)}%
              </div>
            ) : null}
          </div>
          {propertyTrendError ? <p className="mt-4 text-sm text-rose-300">Property trend unavailable for this location yet.</p> : null}
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
