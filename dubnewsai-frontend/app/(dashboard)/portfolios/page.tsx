"use client"

import type { ReactNode } from "react"
import { useEffect, useMemo, useState } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { BarChart3, BellRing, Briefcase, Plus, ShieldCheck, Target } from "lucide-react"

import { AuthGuard } from "@/components/auth/AuthGuard"
import { ActionStatus } from "@/components/shared/ActionStatus"
import { PremiumPageHero } from "@/components/ui/premium-page-hero"
import { apiClient } from "@/lib/api/client"
import { useInvestmentScore, usePortfolioAnalytics, usePortfolioAssetCatalog, usePortfolios, useWatchlists } from "@/lib/hooks/usePortfolio"
import { formatCompactCurrency, formatDateTime } from "@/lib/utils/formatters"

export default function PortfoliosPage() {
  const queryClient = useQueryClient()
  const { data: portfolios = [] } = usePortfolios()
  const { data: watchlists = [] } = useWatchlists()
  const { data: assetCatalog = [] } = usePortfolioAssetCatalog()
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<number | undefined>(undefined)
  const [selectedWatchlistId, setSelectedWatchlistId] = useState<number | undefined>(undefined)
  const [scoreSymbol, setScoreSymbol] = useState("")
  const [riskProfile, setRiskProfile] = useState("moderate")
  const [portfolioForm, setPortfolioForm] = useState({
    name: "Dubai Growth Sleeve",
    description: "Core UAE and real-estate allocation",
    portfolio_type: "mixed",
    base_currency: "AED"
  })
  const [transactionForm, setTransactionForm] = useState({
    symbol: "",
    quantity: 120,
    price: 0,
    transaction_type: "buy",
    fees: 8,
    transaction_date: ""
  })
  const [watchlistForm, setWatchlistForm] = useState({
    name: "Opportunity Radar",
    description: "Names to monitor for entries and follow-through"
  })
  const [watchlistItemForm, setWatchlistItemForm] = useState({
    symbol: "",
    asset_type: "stock",
    asset_name: "",
    target_buy_price: 0,
    target_sell_price: 0,
    notes: "Watch for sentiment confirmation and volume pickup",
    tags: "undervalued, dividend, uae"
  })

  const selectedPortfolio = useMemo(
    () => portfolios.find((item) => item.id === selectedPortfolioId) || portfolios[0],
    [portfolios, selectedPortfolioId]
  )
  const selectedWatchlist = useMemo(
    () => watchlists.find((item) => item.id === selectedWatchlistId) || watchlists[0],
    [selectedWatchlistId, watchlists]
  )
  const selectedTransactionAsset = useMemo(
    () => assetCatalog.find((item) => item.symbol === transactionForm.symbol) || assetCatalog[0],
    [assetCatalog, transactionForm.symbol]
  )
  const selectedWatchAsset = useMemo(
    () => assetCatalog.find((item) => item.symbol === watchlistItemForm.symbol) || assetCatalog[0],
    [assetCatalog, watchlistItemForm.symbol]
  )

  useEffect(() => {
    setTransactionForm((current) =>
      current.transaction_date
        ? current
        : {
            ...current,
            transaction_date: new Date().toISOString().slice(0, 16)
          }
    )
  }, [])

  useEffect(() => {
    if (!transactionForm.symbol && assetCatalog.length) {
      const firstAsset = assetCatalog[0]
      setTransactionForm((current) => ({
        ...current,
        symbol: firstAsset.symbol,
        price: firstAsset.price
      }))
    }
    if (!watchlistItemForm.symbol && assetCatalog.length) {
      const firstAsset = assetCatalog[0]
      setWatchlistItemForm((current) => ({
        ...current,
        symbol: firstAsset.symbol,
        asset_name: firstAsset.name,
        target_buy_price: Number((firstAsset.price * 0.96).toFixed(2)),
        target_sell_price: Number((firstAsset.price * 1.08).toFixed(2))
      }))
    }
    if (!scoreSymbol && assetCatalog.length) {
      setScoreSymbol(assetCatalog[0].symbol)
    }
  }, [assetCatalog, scoreSymbol, transactionForm.symbol, watchlistItemForm.symbol])

  useEffect(() => {
    if (selectedTransactionAsset) {
      setTransactionForm((current) => ({
        ...current,
        symbol: selectedTransactionAsset.symbol,
        price: Number(selectedTransactionAsset.price.toFixed(2))
      }))
    }
  }, [selectedTransactionAsset])

  useEffect(() => {
    if (selectedWatchAsset) {
      setWatchlistItemForm((current) => ({
        ...current,
        symbol: selectedWatchAsset.symbol,
        asset_name: selectedWatchAsset.name,
        target_buy_price:
          current.target_buy_price > 0 ? current.target_buy_price : Number((selectedWatchAsset.price * 0.96).toFixed(2)),
        target_sell_price:
          current.target_sell_price > 0 ? current.target_sell_price : Number((selectedWatchAsset.price * 1.08).toFixed(2))
      }))
    }
  }, [selectedWatchAsset])

  useEffect(() => {
    if (!selectedWatchlistId && watchlists.length) {
      setSelectedWatchlistId(watchlists[0].id)
    }
  }, [selectedWatchlistId, watchlists])

  const { data: analytics } = usePortfolioAnalytics(selectedPortfolio?.id)
  const { data: investmentScore } = useInvestmentScore(scoreSymbol, riskProfile)

  const createPortfolio = useMutation({
    mutationFn: async () => {
      await apiClient.post("/portfolios", portfolioForm)
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["portfolios"] })
    }
  })

  const addTransaction = useMutation({
    mutationFn: async () => {
      if (!selectedPortfolio?.id) return
      await apiClient.post(`/portfolios/id/${selectedPortfolio.id}/transactions`, transactionForm)
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["portfolios"] })
      await queryClient.invalidateQueries({ queryKey: ["portfolios", selectedPortfolio?.id, "analytics"] })
    }
  })

  const createWatchlist = useMutation({
    mutationFn: async () => {
      await apiClient.post("/portfolios/watchlists", watchlistForm)
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["watchlists"] })
    }
  })

  const addWatchlistItem = useMutation({
    mutationFn: async () => {
      const activeWatchlist = selectedWatchlist
      if (!activeWatchlist) return
      await apiClient.post(`/portfolios/watchlists/${activeWatchlist.id}/items`, {
        ...watchlistItemForm,
        tags: watchlistItemForm.tags
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean)
      })
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["watchlists"] })
    }
  })

  const overview = analytics?.overview
  const concentration = analytics?.allocation.concentration

  return (
    <AuthGuard>
      <div className="space-y-8">
        <PremiumPageHero
          eyebrow="Investor intelligence"
          title="Run portfolios, watchlists, and symbol scoring from one investor workspace."
          description="A lighter command surface for tracking books, logging trades, and screening new ideas."
          chips={["Portfolio tracking", "Watchlists", "Risk view", "Investment scoring"]}
          stats={[
            {
              label: "Portfolios",
              value: `${portfolios.length}`,
              hint: "Tracked sleeves and investor books"
            },
            {
              label: "Watchlists",
              value: `${watchlists.length}`,
              hint: "Opportunity and monitoring lists"
            },
            {
              label: "Current book",
              value: selectedPortfolio ? formatCompactCurrency(selectedPortfolio.total_value_aed, "AED") : "0",
              hint: selectedPortfolio?.name || "No active portfolio yet"
            },
            {
              label: "Score lens",
              value: investmentScore ? `${investmentScore.overall_score}` : "Pending",
              hint: investmentScore?.recommendation || "Run a symbol score"
            }
          ]}
          tone="cyan"
        />

        <section className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
          <article className="panel-premium p-6 sm:p-8">
            <p className="story-kicker">Portfolio creation</p>
            <h2 className="mt-4 text-3xl font-semibold text-white">Create a portfolio</h2>
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              <Field label="Name">
                <input
                  className="input-premium"
                  value={portfolioForm.name}
                  onChange={(event) => setPortfolioForm((current) => ({ ...current, name: event.target.value }))}
                />
              </Field>
              <Field label="Type">
                <select
                  className="input-premium"
                  value={portfolioForm.portfolio_type}
                  onChange={(event) => setPortfolioForm((current) => ({ ...current, portfolio_type: event.target.value }))}
                >
                  <option value="mixed">Mixed</option>
                  <option value="stocks">Stocks</option>
                  <option value="real_estate">Real estate</option>
                  <option value="watchlist">Watchlist</option>
                </select>
              </Field>
              <Field label="Description">
                <input
                  className="input-premium"
                  value={portfolioForm.description}
                  onChange={(event) => setPortfolioForm((current) => ({ ...current, description: event.target.value }))}
                />
              </Field>
              <Field label="Base currency">
                <input
                  className="input-premium"
                  value={portfolioForm.base_currency}
                  onChange={(event) => setPortfolioForm((current) => ({ ...current, base_currency: event.target.value.toUpperCase() }))}
                />
              </Field>
            </div>
            <button onClick={() => createPortfolio.mutate()} className="action-premium mt-6" disabled={createPortfolio.isPending}>
              <Plus className="h-4 w-4" />
              {createPortfolio.isPending ? "Creating..." : "Create portfolio"}
            </button>
            <ActionStatus
              isPending={createPortfolio.isPending}
              isSuccess={createPortfolio.isSuccess}
              error={createPortfolio.error}
              successMessage="Portfolio created."
            />

            <div className="mt-8 space-y-3">
              {portfolios.map((portfolio) => (
                <button
                  key={portfolio.id}
                  onClick={() => setSelectedPortfolioId(portfolio.id)}
                  className={`w-full rounded-[1.5rem] border px-4 py-4 text-left transition ${
                    selectedPortfolio?.id === portfolio.id
                      ? "border-cyan-300/30 bg-cyan-300/[0.06]"
                      : "border-white/10 bg-white/[0.03]"
                  }`}
                >
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <div className="text-sm font-medium text-white">{portfolio.name}</div>
                      <div className="mt-1 text-xs text-white/44">{portfolio.description}</div>
                    </div>
                    <div className="text-right text-sm text-white/68">
                      <div>{formatCompactCurrency(portfolio.total_value_aed, "AED")}</div>
                      <div className={portfolio.total_return_percent >= 0 ? "text-emerald-300" : "text-rose-300"}>
                        {portfolio.total_return_percent.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </article>

          <article className="panel-premium p-6 sm:p-8">
            <p className="story-kicker">Selected portfolio</p>
            <h2 className="mt-4 text-3xl font-semibold text-white">
              {selectedPortfolio?.name || "Choose a portfolio to inspect"}
            </h2>
            {selectedPortfolio ? (
              <>
                <div className="mt-6 grid gap-4 md:grid-cols-4">
                  <MetricTile label="Value" value={formatCompactCurrency(selectedPortfolio.total_value_aed, "AED")} />
                  <MetricTile label="Cost" value={formatCompactCurrency(selectedPortfolio.total_cost_aed, "AED")} />
                  <MetricTile
                    label="Return"
                    value={`${selectedPortfolio.total_return_percent.toFixed(2)}%`}
                    accent={selectedPortfolio.total_return_percent >= 0 ? "text-emerald-300" : "text-rose-300"}
                  />
                  <MetricTile label="Holdings" value={`${selectedPortfolio.holdings.length}`} />
                </div>

                <div className="mt-6 rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
                  <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Transaction intake</div>
                  <div className="mt-4 grid gap-4 md:grid-cols-2">
                    <Field label="Symbol">
                      <select
                        className="input-premium"
                        value={transactionForm.symbol}
                        onChange={(event) => setTransactionForm((current) => ({ ...current, symbol: event.target.value }))}
                      >
                        {assetCatalog.map((item) => (
                          <option key={item.symbol} value={item.symbol}>
                            {item.symbol} - {item.name}
                          </option>
                        ))}
                      </select>
                    </Field>
                    <Field label="Type">
                      <select
                        className="input-premium"
                        value={transactionForm.transaction_type}
                        onChange={(event) => setTransactionForm((current) => ({ ...current, transaction_type: event.target.value }))}
                      >
                        <option value="buy">Buy</option>
                        <option value="sell">Sell</option>
                        <option value="dividend">Dividend</option>
                      </select>
                    </Field>
                    <Field label="Quantity">
                      <input
                        type="number"
                        className="input-premium"
                        value={transactionForm.quantity}
                        onChange={(event) => setTransactionForm((current) => ({ ...current, quantity: Number(event.target.value) }))}
                      />
                    </Field>
                    <Field label="Price">
                      <input
                        type="number"
                        className="input-premium"
                        value={transactionForm.price}
                        onChange={(event) => setTransactionForm((current) => ({ ...current, price: Number(event.target.value) }))}
                      />
                    </Field>
                    <Field label="Fees">
                      <input
                        type="number"
                        className="input-premium"
                        value={transactionForm.fees}
                        onChange={(event) => setTransactionForm((current) => ({ ...current, fees: Number(event.target.value) }))}
                      />
                    </Field>
                    <Field label="Transaction time">
                      <input
                        type="datetime-local"
                        className="input-premium"
                        value={transactionForm.transaction_date}
                        onChange={(event) => setTransactionForm((current) => ({ ...current, transaction_date: event.target.value }))}
                      />
                    </Field>
                  </div>
                  {selectedTransactionAsset ? (
                    <div className="mt-4 text-xs text-white/46">
                      {selectedTransactionAsset.sector} • {selectedTransactionAsset.exchange || "Exchange"} • Live {formatCompactCurrency(selectedTransactionAsset.price, selectedTransactionAsset.currency)}
                    </div>
                  ) : null}
                  <button onClick={() => addTransaction.mutate()} className="action-premium mt-5" disabled={addTransaction.isPending}>
                    <Briefcase className="h-4 w-4" />
                    {addTransaction.isPending ? "Saving..." : "Add transaction"}
                  </button>
                  <ActionStatus
                    isPending={addTransaction.isPending}
                    isSuccess={addTransaction.isSuccess}
                    error={addTransaction.error}
                    successMessage="Transaction saved."
                  />
                </div>
              </>
            ) : (
              <div className="mt-6 rounded-[1.5rem] border border-dashed border-white/12 bg-white/[0.02] p-6 text-sm text-white/46">
                Create a portfolio first, then start adding positions and transactions.
              </div>
            )}
          </article>
        </section>

        <section className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
          <article className="panel-premium p-6 sm:p-8">
            <p className="story-kicker">Portfolio analytics</p>
            <h2 className="mt-4 text-3xl font-semibold text-white">Performance, allocation, and concentration</h2>
            {analytics ? (
              <div className="mt-6 space-y-6">
                <div className="grid gap-4 md:grid-cols-4">
                  <MetricTile label="Holdings" value={`${overview?.holdings_count ?? 0}`} />
                  <MetricTile label="Win rate" value={`${Number(analytics.performance.win_rate || 0).toFixed(2)}%`} />
                  <MetricTile label="Sharpe" value={`${Number(analytics.performance.sharpe_ratio || 0).toFixed(2)}`} />
                  <MetricTile label="Risk grade" value={`${analytics.risk_metrics.risk_grade || "N/A"}`} />
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
                    <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Asset allocation</div>
                    <div className="mt-4 space-y-3">
                      {Object.entries(analytics.allocation.by_asset).slice(0, 6).map(([symbol, item]) => (
                        <div key={symbol} className="flex items-center justify-between gap-4">
                          <div className="text-sm text-white">{symbol}</div>
                          <div className="text-sm text-white/62">{item.percent.toFixed(2)}%</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
                    <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Concentration</div>
                    <div className="mt-4 space-y-4">
                      <MetricRow label="Top 5 concentration" value={`${Number(concentration?.top_5_concentration || 0).toFixed(2)}%`} />
                      <MetricRow label="Herfindahl index" value={`${Number(concentration?.herfindahl_index || 0).toFixed(4)}`} />
                      <MetricRow label="Diversification score" value={`${Number(concentration?.diversification_score || 0).toFixed(2)}`} />
                    </div>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <PerformerPanel title="Top performers" items={analytics.top_performers} />
                  <PerformerPanel title="Bottom performers" items={analytics.bottom_performers} />
                </div>
              </div>
            ) : (
              <div className="mt-6 rounded-[1.5rem] border border-dashed border-white/12 bg-white/[0.02] p-6 text-sm text-white/46">
                Portfolio analytics will appear once the selected book has at least one tracked position.
              </div>
            )}
          </article>

          <article className="panel-premium p-6 sm:p-8">
            <p className="story-kicker">Investment scoring</p>
            <h2 className="mt-4 text-3xl font-semibold text-white">Score a symbol with live platform context</h2>
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              <Field label="Symbol">
                <select className="input-premium" value={scoreSymbol} onChange={(event) => setScoreSymbol(event.target.value)}>
                  {assetCatalog.map((item) => (
                    <option key={item.symbol} value={item.symbol}>
                      {item.symbol} - {item.name}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Risk profile">
                <select className="input-premium" value={riskProfile} onChange={(event) => setRiskProfile(event.target.value)}>
                  <option value="conservative">Conservative</option>
                  <option value="moderate">Moderate</option>
                  <option value="aggressive">Aggressive</option>
                </select>
              </Field>
            </div>

            {investmentScore ? (
              <div className="mt-6 space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  <MetricTile label="Score" value={`${investmentScore.overall_score}`} />
                  <MetricTile label="Action" value={investmentScore.recommendation} />
                  <MetricTile label="Confidence" value={investmentScore.confidence} />
                </div>
                <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
                  <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Rationale</div>
                  <p className="mt-3 text-sm leading-7 text-white/60">{investmentScore.rationale}</p>
                  <div className="mt-5 grid gap-4 md:grid-cols-2">
                    <MetricRow
                      label="Target price"
                      value={
                        investmentScore.target_price !== undefined
                          ? formatCompactCurrency(investmentScore.target_price, "AED")
                          : "Unavailable"
                      }
                    />
                    <MetricRow
                      label="Stop loss"
                      value={
                        investmentScore.stop_loss !== undefined
                          ? formatCompactCurrency(investmentScore.stop_loss, "AED")
                          : "Unavailable"
                      }
                    />
                    <MetricRow label="Time horizon" value={investmentScore.time_horizon} />
                    <MetricRow label="Generated" value={formatDateTime(investmentScore.generated_at)} />
                  </div>
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <BadgePanel icon={Target} title="Key factors" items={investmentScore.key_factors} />
                  <BadgePanel icon={ShieldCheck} title="Risks" items={investmentScore.risks} />
                </div>
              </div>
            ) : (
              <div className="mt-6 rounded-[1.5rem] border border-dashed border-white/12 bg-white/[0.02] p-6 text-sm text-white/46">
                Enter a symbol and the scoring engine will generate a recommendation view using technicals, sentiment, macro context, and valuation.
              </div>
            )}
          </article>
        </section>

        <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
          <article className="panel-premium p-6 sm:p-8">
            <p className="story-kicker">Watchlists</p>
            <h2 className="mt-4 text-3xl font-semibold text-white">Track opportunities before they become positions</h2>
            <div className="mt-6 grid gap-4">
              <Field label="Watchlist name">
                <input className="input-premium" value={watchlistForm.name} onChange={(event) => setWatchlistForm((current) => ({ ...current, name: event.target.value }))} />
              </Field>
              <Field label="Description">
                <input className="input-premium" value={watchlistForm.description} onChange={(event) => setWatchlistForm((current) => ({ ...current, description: event.target.value }))} />
              </Field>
              <button onClick={() => createWatchlist.mutate()} className="action-premium" disabled={createWatchlist.isPending}>
                <BellRing className="h-4 w-4" />
                {createWatchlist.isPending ? "Creating..." : "Create watchlist"}
              </button>
              <ActionStatus
                isPending={createWatchlist.isPending}
                isSuccess={createWatchlist.isSuccess}
                error={createWatchlist.error}
                successMessage="Watchlist created."
              />
            </div>

            <div className="mt-8 rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
              <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">Add watch item</div>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <Field label="Destination watchlist">
                  <select
                    className="input-premium"
                    value={selectedWatchlist?.id || ""}
                    onChange={(event) => setSelectedWatchlistId(Number(event.target.value))}
                  >
                    {watchlists.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.name}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Symbol">
                  <select
                    className="input-premium"
                    value={watchlistItemForm.symbol}
                    onChange={(event) => setWatchlistItemForm((current) => ({ ...current, symbol: event.target.value }))}
                  >
                    {assetCatalog.map((item) => (
                      <option key={item.symbol} value={item.symbol}>
                        {item.symbol} - {item.name}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field label="Asset name">
                  <input className="input-premium" value={watchlistItemForm.asset_name} onChange={(event) => setWatchlistItemForm((current) => ({ ...current, asset_name: event.target.value }))} />
                </Field>
                <Field label="Target buy">
                  <input type="number" className="input-premium" value={watchlistItemForm.target_buy_price} onChange={(event) => setWatchlistItemForm((current) => ({ ...current, target_buy_price: Number(event.target.value) }))} />
                </Field>
                <Field label="Target sell">
                  <input type="number" className="input-premium" value={watchlistItemForm.target_sell_price} onChange={(event) => setWatchlistItemForm((current) => ({ ...current, target_sell_price: Number(event.target.value) }))} />
                </Field>
                <Field label="Tags">
                  <input className="input-premium" value={watchlistItemForm.tags} onChange={(event) => setWatchlistItemForm((current) => ({ ...current, tags: event.target.value }))} />
                </Field>
                <Field label="Notes">
                  <input className="input-premium" value={watchlistItemForm.notes} onChange={(event) => setWatchlistItemForm((current) => ({ ...current, notes: event.target.value }))} />
                </Field>
              </div>
              {selectedWatchAsset ? (
                <div className="mt-4 text-xs text-white/46">
                  {selectedWatchAsset.sector} • {selectedWatchAsset.exchange || "Exchange"} • Live {formatCompactCurrency(selectedWatchAsset.price, selectedWatchAsset.currency)}
                </div>
              ) : null}
              <button
                onClick={() => addWatchlistItem.mutate()}
                className="action-premium mt-5"
                disabled={!selectedWatchlist || addWatchlistItem.isPending}
              >
                <Plus className="h-4 w-4" />
                {addWatchlistItem.isPending ? "Adding..." : "Add to watchlist"}
              </button>
              <ActionStatus
                isPending={addWatchlistItem.isPending}
                isSuccess={addWatchlistItem.isSuccess}
                error={addWatchlistItem.error}
                successMessage="Watchlist item added."
              />
            </div>
          </article>

          <article className="panel-premium p-6 sm:p-8">
            <p className="story-kicker">Current watchlists</p>
            <h2 className="mt-4 text-3xl font-semibold text-white">Opportunity radar and monitoring queues</h2>
            <div className="mt-6 space-y-4">
              {watchlists.map((watchlist) => (
                <div key={watchlist.id} className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <div className="text-sm font-medium text-white">{watchlist.name}</div>
                      <div className="mt-1 text-xs text-white/44">{watchlist.description}</div>
                    </div>
                    <div className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/56">
                      {watchlist.items.length} items
                    </div>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {watchlist.items.slice(0, 6).map((item) => (
                      <span key={item.id} className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/60">
                        {item.symbol}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </article>
        </section>
      </div>
    </AuthGuard>
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

function MetricTile({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.03] p-4">
      <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">{label}</div>
      <div className={`mt-3 text-xl font-semibold ${accent || "text-white"}`}>{value}</div>
    </div>
  )
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-white/8 pb-3 last:border-b-0 last:pb-0">
      <div className="text-xs uppercase tracking-[0.2em] text-white/40">{label}</div>
      <div className="text-sm text-white/72">{value}</div>
    </div>
  )
}

function PerformerPanel({
  title,
  items
}: {
  title: string
  items: { symbol: string; return_percent: number; return_amount: number; current_value: number }[]
}) {
  return (
    <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
      <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">{title}</div>
      <div className="mt-4 space-y-3">
        {items.map((item) => (
          <div key={`${title}-${item.symbol}`} className="flex items-center justify-between gap-4">
            <div className="text-sm text-white">{item.symbol}</div>
            <div className="text-sm text-white/62">{item.return_percent.toFixed(2)}%</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function BadgePanel({
  icon: Icon,
  title,
  items
}: {
  icon: typeof BarChart3
  title: string
  items: string[]
}) {
  return (
    <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-5">
      <div className="inline-flex items-center gap-2 text-[10px] uppercase tracking-[0.28em] text-white/38">
        <Icon className="h-3.5 w-3.5 text-cyan-200" />
        {title}
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {items.map((item) => (
          <span key={item} className="rounded-full border border-white/10 px-3 py-1 text-xs text-white/60">
            {item}
          </span>
        ))}
      </div>
    </div>
  )
}
