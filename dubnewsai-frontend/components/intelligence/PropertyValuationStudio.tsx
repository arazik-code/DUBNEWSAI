"use client"

import type { ReactNode } from "react"
import { useEffect, useMemo, useState } from "react"
import { useMutation } from "@tanstack/react-query"
import { motion } from "framer-motion"
import { Calculator, Landmark, LineChart, ScanSearch } from "lucide-react"

import { ActionStatus } from "@/components/shared/ActionStatus"
import { apiClient } from "@/lib/api/client"
import { usePropertyValuationOptions, usePropertyValuationPreset } from "@/lib/hooks/useMarketData"
import { formatCompactCurrency, formatCompactNumber } from "@/lib/utils/formatters"
import type {
  ComparativeAnalysisRequest,
  ComparativeAnalysisResponse,
  PropertyValuationRequest,
  PropertyValuationResponse,
  ROIRequest,
  ROIResponse
} from "@/types"

const EMPTY_VALUATION: PropertyValuationRequest = {
  area_sqft: 0,
  bedrooms: 0,
  location: "",
  property_type: "Apartment",
  year_built: 2022,
  amenities: []
}

const EMPTY_ROI: ROIRequest = {
  purchase_price: 0,
  rental_income_monthly: 0,
  expenses_monthly: 0,
  appreciation_rate: 0.05
}

export function PropertyValuationStudio() {
  const { data: options } = usePropertyValuationOptions()
  const [selectedLocation, setSelectedLocation] = useState("")
  const [selectedType, setSelectedType] = useState("Apartment")
  const [valuationForm, setValuationForm] = useState<PropertyValuationRequest>(EMPTY_VALUATION)
  const [roiForm, setRoiForm] = useState<ROIRequest>(EMPTY_ROI)
  const { data: preset } = usePropertyValuationPreset(selectedLocation, selectedType)

  const activeLocation = useMemo(
    () => options?.locations.find((item) => item.name === selectedLocation) || options?.locations[0],
    [options?.locations, selectedLocation]
  )

  useEffect(() => {
    if (!selectedLocation && options?.locations?.length) {
      const initialLocation = options.locations[0]
      setSelectedLocation(initialLocation.name)
      setSelectedType(initialLocation.supported_types[0] || "Apartment")
    }
  }, [options?.locations, selectedLocation])

  useEffect(() => {
    if (activeLocation && !activeLocation.supported_types.includes(selectedType)) {
      setSelectedType(activeLocation.supported_types[0] || "Apartment")
    }
  }, [activeLocation, selectedType])

  useEffect(() => {
    if (preset) {
      setValuationForm(preset.valuation_defaults)
      setRoiForm(preset.roi_defaults)
    }
  }, [preset])

  useEffect(() => {
    if (selectedLocation) {
      setValuationForm((current) => ({ ...current, location: selectedLocation, property_type: selectedType }))
    }
  }, [selectedLocation, selectedType])

  const valuationMutation = useMutation({
    mutationFn: async (payload: PropertyValuationRequest) => {
      const response = await apiClient.post<PropertyValuationResponse>("/market/property-valuation/estimate", payload)
      return response.data
    }
  })

  const roiMutation = useMutation({
    mutationFn: async (payload: ROIRequest) => {
      const response = await apiClient.post<ROIResponse>("/market/property-valuation/roi", payload)
      return response.data
    }
  })

  const cmaMutation = useMutation({
    mutationFn: async (payload: ComparativeAnalysisRequest) => {
      const response = await apiClient.post<ComparativeAnalysisResponse>("/market/property-valuation/comparative-analysis", payload)
      return response.data
    }
  })

  const hasOutput = Boolean(valuationMutation.data || roiMutation.data || cmaMutation.data)

  useEffect(() => {
    if (valuationMutation.data) {
      setRoiForm((current) => ({
        ...current,
        purchase_price: Number(valuationMutation.data.estimated_value_aed.toFixed(2))
      }))
    }
  }, [valuationMutation.data])

  function toggleAmenity(amenity: string) {
    setValuationForm((current) => {
      const exists = current.amenities.includes(amenity)
      return {
        ...current,
        amenities: exists ? current.amenities.filter((item) => item !== amenity) : [...current.amenities, amenity]
      }
    })
  }

  function runValuation() {
    valuationMutation.mutate(valuationForm)
    cmaMutation.mutate({
      location: valuationForm.location,
      property_type: valuationForm.property_type,
      bedrooms: valuationForm.bedrooms,
      area_sqft: valuationForm.area_sqft,
      year_built: valuationForm.year_built,
      radius_km: 2
    })
  }

  function runRoi() {
    roiMutation.mutate(roiForm)
  }

  return (
    <section className="grid gap-6 xl:grid-cols-[0.94fr_1.06fr]">
      <article className="panel-premium p-6 sm:p-8">
        <p className="story-kicker">Property valuation studio</p>
        <h2 className="mt-4 text-3xl font-semibold text-white">Value and underwrite with supported market presets</h2>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-white/58">
          Choose a supported location and property type, then adjust the underwriting assumptions instead of typing blind.
        </p>

        <div className="mt-8 grid gap-4 md:grid-cols-2">
          <Field label="Location">
            <select className="input-premium" value={selectedLocation} onChange={(event) => setSelectedLocation(event.target.value)}>
              {(options?.locations || []).map((item) => (
                <option key={item.name} value={item.name}>
                  {item.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Property type">
            <select className="input-premium" value={selectedType} onChange={(event) => setSelectedType(event.target.value)}>
              {(activeLocation?.supported_types || options?.property_types || []).map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Area (sqft)">
            <input
              type="number"
              value={valuationForm.area_sqft}
              onChange={(event) => setValuationForm((current) => ({ ...current, area_sqft: Number(event.target.value) }))}
              className="input-premium"
            />
          </Field>
          <Field label="Bedrooms">
            <input
              type="number"
              value={valuationForm.bedrooms}
              onChange={(event) => setValuationForm((current) => ({ ...current, bedrooms: Number(event.target.value) }))}
              className="input-premium"
            />
          </Field>
          <Field label="Year built">
            <input
              type="number"
              value={valuationForm.year_built}
              onChange={(event) => setValuationForm((current) => ({ ...current, year_built: Number(event.target.value) }))}
              className="input-premium"
            />
          </Field>
          <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
            <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Preset context</div>
            <div className="mt-3 text-sm text-white/72">
              {preset
                ? `${formatCompactCurrency(preset.market_context.baseline_price_per_sqft, "AED")} / sqft · ${preset.market_context.market_trend_percent.toFixed(2)}% trend`
                : "Loading preset..."}
            </div>
            <div className="mt-2 text-xs text-white/44">
              {activeLocation ? `${activeLocation.supported_types.join(" · ")}` : "Supported property mix"}
            </div>
          </div>
        </div>

        <div className="mt-6">
          <div className="mb-3 text-[10px] uppercase tracking-[0.28em] text-white/38">Amenities</div>
          <div className="flex flex-wrap gap-2">
            {(options?.amenities || []).map((amenity) => {
              const selected = valuationForm.amenities.includes(amenity)
              return (
                <button
                  key={amenity}
                  type="button"
                  onClick={() => toggleAmenity(amenity)}
                  className={`rounded-full border px-3 py-2 text-xs transition ${
                    selected ? "border-cyan-300/35 bg-cyan-300/[0.08] text-white" : "border-white/10 text-white/60"
                  }`}
                >
                  {amenity}
                </button>
              )
            })}
          </div>
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-2">
          <button onClick={runValuation} className="action-premium" disabled={valuationMutation.isPending || cmaMutation.isPending}>
            <Landmark className="h-4 w-4" />
            {valuationMutation.isPending || cmaMutation.isPending ? "Running..." : "Estimate value"}
          </button>
          <button onClick={runRoi} className="action-premium" disabled={roiMutation.isPending}>
            <Calculator className="h-4 w-4" />
            {roiMutation.isPending ? "Running..." : "Model ROI"}
          </button>
        </div>

        <ActionStatus
          isPending={valuationMutation.isPending || cmaMutation.isPending || roiMutation.isPending}
          isSuccess={valuationMutation.isSuccess || cmaMutation.isSuccess || roiMutation.isSuccess}
          error={valuationMutation.error || cmaMutation.error || roiMutation.error}
          successMessage="Studio outputs refreshed."
        />

        <div className="mt-8 grid gap-4 md:grid-cols-2">
          <Field label="Purchase price">
            <input
              type="number"
              value={roiForm.purchase_price}
              onChange={(event) => setRoiForm((current) => ({ ...current, purchase_price: Number(event.target.value) }))}
              className="input-premium"
            />
          </Field>
          <Field label="Monthly rent">
            <input
              type="number"
              value={roiForm.rental_income_monthly}
              onChange={(event) => setRoiForm((current) => ({ ...current, rental_income_monthly: Number(event.target.value) }))}
              className="input-premium"
            />
          </Field>
          <Field label="Monthly expenses">
            <input
              type="number"
              value={roiForm.expenses_monthly}
              onChange={(event) => setRoiForm((current) => ({ ...current, expenses_monthly: Number(event.target.value) }))}
              className="input-premium"
            />
          </Field>
          <Field label="Appreciation rate">
            <input
              type="number"
              step="0.005"
              value={roiForm.appreciation_rate}
              onChange={(event) => setRoiForm((current) => ({ ...current, appreciation_rate: Number(event.target.value) }))}
              className="input-premium"
            />
          </Field>
        </div>
      </article>

      <article className="panel-premium p-6 sm:p-8">
        <p className="story-kicker">Output board</p>
        <h2 className="mt-4 text-3xl font-semibold text-white">Live underwriting view</h2>

        {!hasOutput ? (
          <div className="mt-8 rounded-[1.75rem] border border-dashed border-white/12 bg-white/[0.02] p-6 text-sm leading-7 text-white/48">
            Pick a supported market preset and run the valuation or ROI model to populate the board.
          </div>
        ) : (
          <div className="mt-8 space-y-6">
            {valuationMutation.data ? (
              <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  <InsightTile icon={Landmark} label="Estimated value" value={formatCompactCurrency(valuationMutation.data.estimated_value_aed, "AED")} />
                  <InsightTile icon={LineChart} label="Price / sqft" value={formatCompactCurrency(valuationMutation.data.price_per_sqft, "AED")} />
                  <InsightTile icon={ScanSearch} label="Market trend" value={`${valuationMutation.data.market_trend.toFixed(2)}%`} />
                </div>

                <div className="rounded-[1.6rem] border border-white/10 bg-white/[0.03] p-5">
                  <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Narrative</div>
                  <p className="mt-3 text-sm leading-7 text-white/64">{valuationMutation.data.narrative}</p>
                  <div className="mt-4 text-sm text-white/52">
                    Confidence band: {formatCompactCurrency(valuationMutation.data.confidence_interval.lower, "AED")} to{" "}
                    {formatCompactCurrency(valuationMutation.data.confidence_interval.upper, "AED")}
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="rounded-[1.6rem] border border-white/10 bg-white/[0.03] p-5">
                    <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Value drivers</div>
                    <div className="mt-4 space-y-3">
                      {valuationMutation.data.value_drivers.map((driver) => (
                        <div key={driver.label} className="flex items-start justify-between gap-4 border-b border-white/8 pb-3 last:border-b-0 last:pb-0">
                          <div>
                            <div className="text-sm font-medium text-white">{driver.label}</div>
                            <div className="mt-1 text-xs text-white/46">{driver.context}</div>
                          </div>
                          <div className="text-sm text-white/70">{driver.value}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-[1.6rem] border border-white/10 bg-white/[0.03] p-5">
                    <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Comparables</div>
                    <div className="mt-4 space-y-3">
                      {valuationMutation.data.comparables.slice(0, 4).map((item) => (
                        <div key={item.title} className="rounded-[1.25rem] border border-white/8 bg-black/10 p-4">
                          <div className="text-sm font-medium text-white">{item.title}</div>
                          <div className="mt-1 text-xs text-white/46">
                            {item.property_type} · {item.bedrooms} BR · {formatCompactNumber(item.area_sqft)} sqft
                          </div>
                          <div className="mt-3 flex items-center justify-between gap-4 text-sm text-white/68">
                            <span>{formatCompactCurrency(item.estimated_price_aed, "AED")}</span>
                            <span>{item.similarity_score}% match</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </motion.div>
            ) : null}

            {roiMutation.data ? (
              <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                <div className="grid gap-4 md:grid-cols-4">
                  <InsightTile icon={Calculator} label="Cap rate" value={`${roiMutation.data.cap_rate.toFixed(2)}%`} />
                  <InsightTile icon={Calculator} label="Cash on cash" value={`${roiMutation.data.cash_on_cash_return.toFixed(2)}%`} />
                  <InsightTile icon={Calculator} label="Annual net" value={formatCompactCurrency(roiMutation.data.annual_net_income, "AED")} />
                  <InsightTile icon={Calculator} label="Grade" value={roiMutation.data.investment_grade} />
                </div>
                <div className="rounded-[1.6rem] border border-white/10 bg-white/[0.03] p-5">
                  <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Ten-year return path</div>
                  <div className="mt-4 grid gap-3 md:grid-cols-2">
                    {roiMutation.data.projections.slice(0, 6).map((item) => (
                      <div key={item.year} className="rounded-[1.2rem] border border-white/8 bg-black/10 p-4">
                        <div className="text-xs uppercase tracking-[0.24em] text-white/42">Year {item.year}</div>
                        <div className="mt-2 text-sm text-white/72">Value: {formatCompactCurrency(item.property_value, "AED")}</div>
                        <div className="mt-1 text-sm text-white/72">ROI: {item.roi_percent.toFixed(2)}%</div>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            ) : null}

            {cmaMutation.data ? (
              <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} className="rounded-[1.6rem] border border-white/10 bg-white/[0.03] p-5">
                <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Comparative market analysis</div>
                <p className="mt-3 text-sm leading-7 text-white/62">{cmaMutation.data.recommendation}</p>
                {cmaMutation.data.market_statistics ? (
                  <div className="mt-5 grid gap-4 md:grid-cols-4">
                    <MetricChip label="Average" value={formatCompactCurrency(cmaMutation.data.market_statistics.average_price, "AED")} />
                    <MetricChip label="Median" value={formatCompactCurrency(cmaMutation.data.market_statistics.median_price, "AED")} />
                    <MetricChip label="Price / sqft" value={formatCompactCurrency(cmaMutation.data.market_statistics.average_price_per_sqft, "AED")} />
                    <MetricChip label="Activity" value={cmaMutation.data.market_activity} />
                  </div>
                ) : null}
              </motion.div>
            ) : null}
          </div>
        )}
      </article>
    </section>
  )
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <div className="mb-2 text-[10px] uppercase tracking-[0.28em] text-white/38">{label}</div>
      {children}
    </label>
  )
}

function InsightTile({ icon: Icon, label, value }: { icon: typeof Landmark; label: string; value: string }) {
  return (
    <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.03] p-4">
      <div className="inline-flex items-center gap-2 text-[10px] uppercase tracking-[0.28em] text-white/38">
        <Icon className="h-3.5 w-3.5 text-cyan-200" />
        {label}
      </div>
      <div className="mt-3 text-xl font-semibold text-white">{value}</div>
    </div>
  )
}

function MetricChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1.2rem] border border-white/8 bg-black/10 px-4 py-4">
      <div className="text-[10px] uppercase tracking-[0.24em] text-white/40">{label}</div>
      <div className="mt-2 text-sm text-white/76">{value}</div>
    </div>
  )
}
