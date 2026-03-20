"use client"

import type { ReactNode } from "react"
import { useMemo, useState } from "react"
import { useMutation } from "@tanstack/react-query"
import { motion } from "framer-motion"
import { Calculator, Landmark, LineChart, ScanSearch } from "lucide-react"

import { apiClient } from "@/lib/api/client"
import { formatCompactCurrency, formatCompactNumber } from "@/lib/utils/formatters"
import type {
  ComparativeAnalysisRequest,
  ComparativeAnalysisResponse,
  PropertyValuationRequest,
  PropertyValuationResponse,
  ROIRequest,
  ROIResponse
} from "@/types"

const defaultValuation: PropertyValuationRequest = {
  area_sqft: 1350,
  bedrooms: 2,
  location: "Dubai Marina",
  property_type: "Apartment",
  year_built: 2020,
  amenities: ["Pool", "Gym", "Sea View", "Parking"]
}

const defaultRoi: ROIRequest = {
  purchase_price: 2650000,
  rental_income_monthly: 16500,
  expenses_monthly: 2200,
  appreciation_rate: 0.055
}

export function PropertyValuationStudio() {
  const [valuationForm, setValuationForm] = useState(defaultValuation)
  const [roiForm, setRoiForm] = useState(defaultRoi)
  const [amenitiesInput, setAmenitiesInput] = useState(defaultValuation.amenities.join(", "))

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

  const valuationReady = useMemo(
    () => valuationMutation.data || roiMutation.data || cmaMutation.data,
    [valuationMutation.data, roiMutation.data, cmaMutation.data]
  )

  function syncAmenities(value: string) {
    setAmenitiesInput(value)
    setValuationForm((current) => ({
      ...current,
      amenities: value
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean)
    }))
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
    <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <article className="panel-premium p-6 sm:p-8">
        <p className="story-kicker">Property valuation studio</p>
        <h2 className="mt-4 text-3xl font-semibold text-white">Estimate value, return profile, and market fit</h2>
        <p className="mt-4 max-w-2xl text-sm leading-7 text-white/58">
          Phase 1 brings a production-ready valuation layer to DUBNEWSAI so investors and operators can move from board
          intelligence into property underwriting without leaving the platform.
        </p>

        <div className="mt-8 grid gap-4 md:grid-cols-2">
          <Field label="Location">
            <input
              value={valuationForm.location}
              onChange={(event) => setValuationForm((current) => ({ ...current, location: event.target.value }))}
              className="input-premium"
            />
          </Field>
          <Field label="Property type">
            <input
              value={valuationForm.property_type}
              onChange={(event) => setValuationForm((current) => ({ ...current, property_type: event.target.value }))}
              className="input-premium"
            />
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
          <Field label="Amenities">
            <input value={amenitiesInput} onChange={(event) => syncAmenities(event.target.value)} className="input-premium" />
          </Field>
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-4">
          <button onClick={runValuation} className="action-premium">
            <Landmark className="h-4 w-4" />
            Estimate value
          </button>
          <button onClick={runRoi} className="action-premium">
            <Calculator className="h-4 w-4" />
            Model ROI
          </button>
        </div>

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
        <p className="story-kicker">Phase 1 output</p>
        <h2 className="mt-4 text-3xl font-semibold text-white">Underwriting board</h2>

        {!valuationReady ? (
          <div className="mt-8 rounded-[1.75rem] border border-dashed border-white/12 bg-white/[0.02] p-6 text-sm leading-7 text-white/48">
            Run a valuation or ROI model to populate the underwriting board. The comparable set, confidence range, and
            return path will appear here.
          </div>
        ) : (
          <div className="mt-8 space-y-6">
            {valuationMutation.data ? (
              <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  <InsightTile
                    icon={Landmark}
                    label="Estimated value"
                    value={formatCompactCurrency(valuationMutation.data.estimated_value_aed, "AED")}
                  />
                  <InsightTile
                    icon={LineChart}
                    label="Price / sqft"
                    value={formatCompactCurrency(valuationMutation.data.price_per_sqft, "AED")}
                  />
                  <InsightTile
                    icon={ScanSearch}
                    label="Market trend"
                    value={`${valuationMutation.data.market_trend.toFixed(2)}%`}
                  />
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
                  <InsightTile
                    icon={Calculator}
                    label="Cash on cash"
                    value={`${roiMutation.data.cash_on_cash_return.toFixed(2)}%`}
                  />
                  <InsightTile
                    icon={Calculator}
                    label="Annual net"
                    value={formatCompactCurrency(roiMutation.data.annual_net_income, "AED")}
                  />
                  <InsightTile icon={Calculator} label="Grade" value={roiMutation.data.investment_grade} />
                </div>
                <div className="rounded-[1.6rem] border border-white/10 bg-white/[0.03] p-5">
                  <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Ten-year return path</div>
                  <div className="mt-4 grid gap-3 md:grid-cols-2">
                    {roiMutation.data.projections.slice(0, 6).map((item) => (
                      <div key={item.year} className="rounded-[1.2rem] border border-white/8 bg-black/10 p-4">
                        <div className="text-xs uppercase tracking-[0.24em] text-white/42">Year {item.year}</div>
                        <div className="mt-2 text-sm text-white/72">
                          Value: {formatCompactCurrency(item.property_value, "AED")}
                        </div>
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
