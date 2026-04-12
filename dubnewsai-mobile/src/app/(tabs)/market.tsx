import { useEffect, useMemo, useState } from "react";

import { Ionicons } from "@expo/vector-icons";
import { useMutation, useQuery } from "@tanstack/react-query";
import { router } from "expo-router";
import { ScrollView, StyleSheet, Text, View } from "react-native";

import { ChoiceChip } from "@/components/choice-chip";
import { MarketCard } from "@/components/market-card";
import { PrimaryButton } from "@/components/primary-button";
import { ScreenShell } from "@/components/screen-shell";
import { SectionHeader } from "@/components/section-header";
import { StatePanel } from "@/components/state-panel";
import { Surface } from "@/components/surface";
import { TextField } from "@/components/text-field";
import { mobileApi } from "@/lib/api/queries";
import type { PropertyPreset, ROIResult } from "@/lib/api/types";
import { formatCompactNumber, formatCurrency, formatPercent, sentenceCase } from "@/lib/formatters";
import { useAppTheme } from "@/lib/theme";

function parseNumber(value: string, fallback = 0) {
  const parsed = Number(value.replace(/,/g, "").trim());
  return Number.isFinite(parsed) ? parsed : fallback;
}

function buildRoiView(
  payload: Record<string, unknown>,
  fallback: PropertyPreset["roi_defaults"],
): ROIResult {
  const projections = Array.isArray(payload.projections)
    ? (payload.projections as Array<Record<string, unknown>>)
    : [];
  const projectionYearFive = projections.find((item) => Number(item.year) === 5);

  return {
    gross_yield_percent:
      Number(payload.gross_yield_percent ?? payload.gross_rental_yield_percent ?? payload.cap_rate ?? 0) || 0,
    net_yield_percent:
      Number(payload.net_yield_percent ?? payload.net_rental_yield_percent ?? payload.cash_on_cash_return ?? 0) || 0,
    annual_cash_flow: Number(payload.annual_cash_flow ?? payload.annual_net_income ?? 0) || 0,
    five_year_projection:
      Number(
        payload.five_year_projection ??
          payload.total_return_5y ??
          payload.projected_value_5y ??
          projectionYearFive?.total_return ??
          0,
      ) || 0,
    payback_period_years:
      Number(payload.payback_period_years ?? payload.break_even_years ?? payload.payback_years ?? 0) ||
      Math.max(
        fallback.purchase_price /
          Math.max((fallback.rental_income_monthly - fallback.expenses_monthly) * 12, 1),
        0,
      ),
  };
}

export default function MarketScreen() {
  const { colors } = useAppTheme();
  const optionsQuery = useQuery({
    queryKey: ["mobile-prediction-options"],
    queryFn: mobileApi.getPredictionOptions,
  });
  const marketOverviewQuery = useQuery({
    queryKey: ["mobile-market-overview"],
    queryFn: mobileApi.getMarketOverview,
  });
  const marketTrendQuery = useQuery({
    queryKey: ["mobile-market-trend"],
    queryFn: mobileApi.getMarketTrend,
  });
  const propertyOptionsQuery = useQuery({
    queryKey: ["mobile-property-options"],
    queryFn: mobileApi.getPropertyOptions,
  });

  const [selectedSymbol, setSelectedSymbol] = useState("");
  const [selectedLocation, setSelectedLocation] = useState("");
  const [selectedPropertyType, setSelectedPropertyType] = useState("");
  const [areaSqft, setAreaSqft] = useState("980");
  const [bedrooms, setBedrooms] = useState("2");
  const [purchasePrice, setPurchasePrice] = useState("0");
  const [rentalIncome, setRentalIncome] = useState("0");
  const [monthlyExpenses, setMonthlyExpenses] = useState("0");
  const [appreciationRate, setAppreciationRate] = useState("0");
  const [roiResult, setRoiResult] = useState<ROIResult | null>(null);
  const locationOptions = propertyOptionsQuery.data?.locations ?? [];
  const activeLocation = useMemo(
    () => locationOptions.find((item) => item.name === selectedLocation) ?? null,
    [locationOptions, selectedLocation],
  );
  const availablePropertyTypes = useMemo(() => {
    if (activeLocation?.supported_types?.length) {
      return activeLocation.supported_types;
    }
    return propertyOptionsQuery.data?.property_types ?? [];
  }, [activeLocation, propertyOptionsQuery.data]);

  useEffect(() => {
    const firstSymbol = optionsQuery.data?.symbols[0]?.canonical_symbol;
    if (!selectedSymbol && firstSymbol) {
      setSelectedSymbol(firstSymbol);
    }
  }, [optionsQuery.data, selectedSymbol]);

  useEffect(() => {
    const firstLocation = propertyOptionsQuery.data?.locations[0]?.name;
    if (!selectedLocation && firstLocation) {
      setSelectedLocation(firstLocation);
    }
  }, [propertyOptionsQuery.data, selectedLocation]);

  useEffect(() => {
    const firstType = availablePropertyTypes[0];
    if (!selectedPropertyType && firstType) {
      setSelectedPropertyType(firstType);
    }
  }, [availablePropertyTypes, selectedPropertyType]);

  useEffect(() => {
    if (!selectedPropertyType || !availablePropertyTypes.includes(selectedPropertyType)) {
      const firstSupported = availablePropertyTypes[0];
      if (firstSupported) {
        setSelectedPropertyType(firstSupported);
      }
    }
  }, [availablePropertyTypes, selectedPropertyType]);

  const pricePredictionQuery = useQuery({
    queryKey: ["mobile-price-prediction", selectedSymbol],
    queryFn: () => mobileApi.getPricePrediction(selectedSymbol, 30),
    enabled: Boolean(selectedSymbol),
  });

  const propertyPresetQuery = useQuery({
    queryKey: ["mobile-property-preset", selectedLocation, selectedPropertyType],
    queryFn: () => mobileApi.getPropertyPreset(selectedLocation, selectedPropertyType),
    enabled: Boolean(selectedLocation && selectedPropertyType),
  });

  const propertyTrendQuery = useQuery({
    queryKey: ["mobile-property-trend", selectedLocation, selectedPropertyType],
    queryFn: () => mobileApi.getPropertyTrend(selectedLocation, selectedPropertyType),
    enabled: Boolean(selectedLocation && selectedPropertyType),
  });

  useEffect(() => {
    const preset = propertyPresetQuery.data;
    if (!preset) {
      return;
    }

    setPurchasePrice(String(Math.round(preset.roi_defaults.purchase_price)));
    setRentalIncome(String(Math.round(preset.roi_defaults.rental_income_monthly)));
    setMonthlyExpenses(String(Math.round(preset.roi_defaults.expenses_monthly)));
    setAppreciationRate(String(Number((preset.roi_defaults.appreciation_rate * 100).toFixed(2))));
    setAreaSqft(String(Math.round(preset.valuation_defaults.area_sqft)));
    setBedrooms(String(preset.valuation_defaults.bedrooms));
    setRoiResult(null);
  }, [propertyPresetQuery.data]);

  const estimateMutation = useMutation({
    mutationFn: () =>
      mobileApi.estimateProperty({
        location: selectedLocation,
        property_type: selectedPropertyType,
        area_sqft: parseNumber(areaSqft, propertyPresetQuery.data?.valuation_defaults.area_sqft ?? 900),
        bedrooms: parseNumber(bedrooms, propertyPresetQuery.data?.valuation_defaults.bedrooms ?? 2),
        year_built: propertyPresetQuery.data?.valuation_defaults.year_built,
        amenities: propertyPresetQuery.data?.valuation_defaults.amenities,
      }),
  });

  const roiMutation = useMutation({
    mutationFn: async () => {
      const fallback = propertyPresetQuery.data?.roi_defaults ?? {
        purchase_price: 0,
        rental_income_monthly: 0,
        expenses_monthly: 0,
        appreciation_rate: 0,
      };

      const response = await mobileApi.calculateRoi({
        purchase_price: parseNumber(purchasePrice, fallback.purchase_price),
        rental_income_monthly: parseNumber(rentalIncome, fallback.rental_income_monthly),
        expenses_monthly: parseNumber(monthlyExpenses, fallback.expenses_monthly),
        appreciation_rate: parseNumber(appreciationRate, fallback.appreciation_rate * 100) / 100,
      });

      return buildRoiView(response, fallback);
    },
    onSuccess: (result) => {
      setRoiResult(result);
    },
  });

  const activeSymbol = useMemo(
    () =>
      optionsQuery.data?.symbols.find(
        (item) =>
          item.canonical_symbol === selectedSymbol || item.symbol === selectedSymbol,
      ) ?? null,
    [optionsQuery.data, selectedSymbol],
  );

  const movers = marketOverviewQuery.data?.stocks.slice(0, 8) ?? [];
  const indices = marketOverviewQuery.data?.indices.slice(0, 4) ?? [];
  const leaders = marketOverviewQuery.data?.real_estate_companies.slice(0, 6) ?? [];

  if (
    optionsQuery.isLoading ||
    marketOverviewQuery.isLoading ||
    propertyOptionsQuery.isLoading
  ) {
    return (
      <ScreenShell>
        <StatePanel
          title="Loading market intelligence"
          body="Pulling live movers, predictions, and property presets for the mobile studio."
          loading
        />
      </ScreenShell>
    );
  }

  if (
    optionsQuery.isError ||
    marketOverviewQuery.isError ||
    propertyOptionsQuery.isError
  ) {
    return (
      <ScreenShell>
        <StatePanel
          title="Market intelligence unavailable"
          body="The mobile market surface could not be loaded right now."
        />
      </ScreenShell>
    );
  }

  return (
    <ScreenShell>
      <View style={styles.header}>
        <Text style={[styles.kicker, { color: colors.accent }]}>
          Market intelligence
        </Text>
        <Text style={[styles.title, { color: colors.text }]}>
          Forecasts, movers, and property conviction.
        </Text>
        <Text style={[styles.body, { color: colors.textMuted }]}>
          A native market cockpit built around quick symbol decisions and real-estate
          underwriting on the move.
        </Text>
      </View>

      <Surface style={styles.heroPanel}>
        <View style={styles.heroRow}>
          <View style={styles.heroStat}>
            <Text style={[styles.heroValue, { color: colors.text }]}>
              {marketTrendQuery.data ? sentenceCase(marketTrendQuery.data.prediction) : "Live"}
            </Text>
            <Text style={[styles.heroLabel, { color: colors.textMuted }]}>
              regional trend
            </Text>
          </View>
          <View style={styles.heroStat}>
            <Text style={[styles.heroValue, { color: colors.text }]}>
              {marketTrendQuery.data ? marketTrendQuery.data.trend_score.toFixed(0) : "--"}
            </Text>
            <Text style={[styles.heroLabel, { color: colors.textMuted }]}>trend score</Text>
          </View>
          <View style={styles.heroStat}>
            <Text style={[styles.heroValue, { color: colors.text }]}>
              {formatCompactNumber(movers.length)}
            </Text>
            <Text style={[styles.heroLabel, { color: colors.textMuted }]}>
              tracked movers
            </Text>
          </View>
        </View>
        {marketTrendQuery.data ? (
          <Text style={[styles.heroBody, { color: colors.textSoft }]}>
            {marketTrendQuery.data.recommendation}
          </Text>
        ) : null}
      </Surface>

      <View>
        <SectionHeader
          eyebrow="Predictive layer"
          title="Price movement forecast"
          description="Curated instruments only, so the mobile app stays fast and the prediction universe stays clean."
        />
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.rail}
        >
          {(optionsQuery.data?.symbols ?? []).slice(0, 10).map((item) => (
            <ChoiceChip
              key={item.canonical_symbol}
              label={item.symbol}
              selected={selectedSymbol === item.canonical_symbol}
              onPress={() => setSelectedSymbol(item.canonical_symbol)}
            />
          ))}
        </ScrollView>
        {activeSymbol ? (
          <Surface style={styles.predictionCard}>
            <View style={styles.predictionTop}>
              <View style={styles.copyBlock}>
                <Text style={[styles.predictionSymbol, { color: colors.text }]}>
                  {activeSymbol.symbol}
                </Text>
                <Text style={[styles.predictionName, { color: colors.textMuted }]}>
                  {activeSymbol.name}
                </Text>
              </View>
              <View
                style={[
                  styles.deltaPill,
                  {
                    backgroundColor:
                      activeSymbol.change_percent >= 0
                        ? "rgba(49, 196, 141, 0.16)"
                        : "rgba(248, 113, 113, 0.16)",
                  },
                ]}
              >
                <Text
                  style={{
                    color:
                      activeSymbol.change_percent >= 0
                        ? colors.success
                        : colors.danger,
                    fontWeight: "800",
                    fontSize: 12,
                  }}
                >
                  {formatPercent(activeSymbol.change_percent)}
                </Text>
              </View>
            </View>
            {pricePredictionQuery.isLoading ? (
              <Text style={[styles.inlineHint, { color: colors.textMuted }]}>
                Generating a 30-day forecast...
              </Text>
            ) : pricePredictionQuery.data ? (
              <View style={styles.metricGrid}>
                <View style={styles.metricItem}>
                  <Text style={[styles.metricLabel, { color: colors.textMuted }]}>
                    Current price
                  </Text>
                  <Text style={[styles.metricValue, { color: colors.text }]}>
                    {formatCurrency(pricePredictionQuery.data.current_price)}
                  </Text>
                </View>
                <View style={styles.metricItem}>
                  <Text style={[styles.metricLabel, { color: colors.textMuted }]}>
                    Target price
                  </Text>
                  <Text style={[styles.metricValue, { color: colors.text }]}>
                    {formatCurrency(pricePredictionQuery.data.prediction.target_price)}
                  </Text>
                </View>
                <View style={styles.metricItem}>
                  <Text style={[styles.metricLabel, { color: colors.textMuted }]}>
                    Expected return
                  </Text>
                  <Text
                    style={[
                      styles.metricValue,
                      {
                        color:
                          pricePredictionQuery.data.prediction.expected_return_percent >= 0
                            ? colors.success
                            : colors.danger,
                      },
                    ]}
                  >
                    {formatPercent(
                      pricePredictionQuery.data.prediction.expected_return_percent,
                    )}
                  </Text>
                </View>
                <View style={styles.metricItem}>
                  <Text style={[styles.metricLabel, { color: colors.textMuted }]}>
                    Model confidence
                  </Text>
                  <Text style={[styles.metricValue, { color: colors.text }]}>
                    {(pricePredictionQuery.data.model_info.r_squared * 100).toFixed(0)}%
                  </Text>
                </View>
              </View>
            ) : (
              <Text style={[styles.inlineHint, { color: colors.textMuted }]}>
                Prediction unavailable right now for this symbol.
              </Text>
            )}
          </Surface>
        ) : null}
      </View>

      <View>
        <SectionHeader
          eyebrow="Live board"
          title="Stocks and real-estate leaders"
          description="A mobile-first watch rail with enough context to decide where to dive deeper."
        />
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.rail}
        >
          {movers.map((item) => (
            <View key={item.symbol} style={styles.marketCardWrap}>
              <MarketCard
                item={item}
                onPress={() => router.push(`/market/${encodeURIComponent(item.symbol)}`)}
              />
            </View>
          ))}
        </ScrollView>
        <View style={styles.indexGrid}>
          {indices.map((item) => (
            <Surface key={item.symbol} style={styles.indexCard}>
              <Text style={[styles.indexSymbol, { color: colors.text }]}>{item.symbol}</Text>
              <Text
                style={[styles.indexName, { color: colors.textMuted }]}
                numberOfLines={1}
              >
                {item.name}
              </Text>
              <Text
                style={[
                  styles.indexChange,
                  {
                    color:
                      item.change_percent >= 0 ? colors.success : colors.danger,
                  },
                ]}
              >
                {formatPercent(item.change_percent)}
              </Text>
            </Surface>
          ))}
        </View>
      </View>

      <View>
        <SectionHeader
          eyebrow="Property valuation studio"
          title="Underwrite a property without leaving your phone"
          description="Switch location and property type, then recalculate valuation and ROI with sensible market defaults."
        />
        <Surface style={styles.studio}>
          <View style={styles.fieldBlock}>
            <Text style={[styles.groupLabel, { color: colors.textSoft }]}>Location</Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.rail}
            >
              {locationOptions.map((location) => (
                <ChoiceChip
                  key={location.name}
                  label={location.name}
                  selected={selectedLocation === location.name}
                  onPress={() => setSelectedLocation(location.name)}
                />
              ))}
            </ScrollView>
          </View>
          <View style={styles.fieldBlock}>
            <Text style={[styles.groupLabel, { color: colors.textSoft }]}>
              Property type
            </Text>
            <View style={styles.chipWrap}>
              {availablePropertyTypes.map((propertyType) => (
                <ChoiceChip
                  key={propertyType}
                  label={propertyType}
                  selected={selectedPropertyType === propertyType}
                  onPress={() => setSelectedPropertyType(propertyType)}
                />
              ))}
            </View>
          </View>
          {propertyPresetQuery.data ? (
            <View style={styles.metricGrid}>
              <View style={styles.metricItem}>
                <Text style={[styles.metricLabel, { color: colors.textMuted }]}>
                  Average price/sqft
                </Text>
                <Text style={[styles.metricValue, { color: colors.text }]}>
                  {formatCurrency(propertyPresetQuery.data.market_context.baseline_price_per_sqft)}
                </Text>
              </View>
              <View style={styles.metricItem}>
                <Text style={[styles.metricLabel, { color: colors.textMuted }]}>
                  Average sale price
                </Text>
                <Text style={[styles.metricValue, { color: colors.text }]}>
                  {formatCurrency(propertyPresetQuery.data.roi_defaults.purchase_price)}
                </Text>
              </View>
              <View style={styles.metricItem}>
                <Text style={[styles.metricLabel, { color: colors.textMuted }]}>
                  Rent yield
                </Text>
                <Text style={[styles.metricValue, { color: colors.text }]}>
                  {(
                    (propertyPresetQuery.data.roi_defaults.rental_income_monthly * 12) /
                    Math.max(propertyPresetQuery.data.roi_defaults.purchase_price, 1)
                  * 100
                  ).toFixed(1)}
                  %
                </Text>
              </View>
              <View style={styles.metricItem}>
                <Text style={[styles.metricLabel, { color: colors.textMuted }]}>
                  12M trend
                </Text>
                <Text style={[styles.metricValue, { color: colors.text }]}>
                  {propertyTrendQuery.data
                    ? sentenceCase(propertyTrendQuery.data.forecast_12m.trend)
                    : "Loading"}
                </Text>
              </View>
            </View>
          ) : null}

          <View style={styles.doubleFieldRow}>
            <View style={styles.flexField}>
              <TextField
                label="Area (sqft)"
                value={areaSqft}
                onChangeText={setAreaSqft}
                keyboardType="numeric"
              />
            </View>
            <View style={styles.flexField}>
              <TextField
                label="Bedrooms"
                value={bedrooms}
                onChangeText={setBedrooms}
                keyboardType="numeric"
              />
            </View>
          </View>

          <View style={styles.doubleFieldRow}>
            <View style={styles.flexField}>
              <TextField
                label="Purchase price"
                value={purchasePrice}
                onChangeText={setPurchasePrice}
                keyboardType="numeric"
              />
            </View>
            <View style={styles.flexField}>
              <TextField
                label="Monthly rent"
                value={rentalIncome}
                onChangeText={setRentalIncome}
                keyboardType="numeric"
              />
            </View>
          </View>

          <View style={styles.doubleFieldRow}>
            <View style={styles.flexField}>
              <TextField
                label="Monthly expenses"
                value={monthlyExpenses}
                onChangeText={setMonthlyExpenses}
                keyboardType="numeric"
              />
            </View>
            <View style={styles.flexField}>
              <TextField
                label="Appreciation rate %"
                value={appreciationRate}
                onChangeText={setAppreciationRate}
                keyboardType="numeric"
              />
            </View>
          </View>

          <PrimaryButton
            label={estimateMutation.isPending ? "Estimating value..." : "Estimate property value"}
            onPress={() => estimateMutation.mutate()}
            loading={estimateMutation.isPending}
          />
          <PrimaryButton
            label={roiMutation.isPending ? "Calculating ROI..." : "Calculate ROI"}
            onPress={() => roiMutation.mutate()}
            loading={roiMutation.isPending}
            variant="secondary"
          />

          {estimateMutation.data ? (
            <Surface style={styles.innerPanel}>
              <Text style={[styles.innerTitle, { color: colors.text }]}>
                Estimated market value
              </Text>
              <Text style={[styles.innerValue, { color: colors.text }]}>
                {formatCurrency(estimateMutation.data.estimated_value_aed)}
              </Text>
              <Text style={[styles.inlineHint, { color: colors.textMuted }]}>
                Range {formatCurrency(estimateMutation.data.confidence_interval.low)} -{" "}
                {formatCurrency(estimateMutation.data.confidence_interval.high)}
              </Text>
            </Surface>
          ) : null}

          {roiResult ? (
            <Surface style={styles.innerPanel}>
              <Text style={[styles.innerTitle, { color: colors.text }]}>ROI snapshot</Text>
              <View style={styles.metricGrid}>
                <View style={styles.metricItem}>
                  <Text style={[styles.metricLabel, { color: colors.textMuted }]}>
                    Cap rate
                  </Text>
                  <Text style={[styles.metricValue, { color: colors.text }]}>
                    {roiResult.gross_yield_percent.toFixed(2)}%
                  </Text>
                </View>
                <View style={styles.metricItem}>
                  <Text style={[styles.metricLabel, { color: colors.textMuted }]}>
                    Cash on cash
                  </Text>
                  <Text style={[styles.metricValue, { color: colors.text }]}>
                    {roiResult.net_yield_percent.toFixed(2)}%
                  </Text>
                </View>
                <View style={styles.metricItem}>
                  <Text style={[styles.metricLabel, { color: colors.textMuted }]}>
                    Annual cash flow
                  </Text>
                  <Text style={[styles.metricValue, { color: colors.text }]}>
                    {formatCurrency(roiResult.annual_cash_flow)}
                  </Text>
                </View>
                <View style={styles.metricItem}>
                  <Text style={[styles.metricLabel, { color: colors.textMuted }]}>
                    5-year projection
                  </Text>
                  <Text style={[styles.metricValue, { color: colors.text }]}>
                    {formatCurrency(roiResult.five_year_projection)}
                  </Text>
                </View>
              </View>
            </Surface>
          ) : null}
        </Surface>
      </View>

      <View>
        <SectionHeader
          eyebrow="Real-estate names"
          title="Public market leaders tied to the Dubai cycle"
          description="A clean shortlist of the companies shaping market sentiment."
        />
        <View style={styles.leaderList}>
          {leaders.map((item) => (
            <Surface key={item.symbol} style={styles.leaderCard}>
              <View style={styles.leaderTop}>
                <View style={styles.iconBadge}>
                  <Ionicons name="business" size={16} color={colors.accent} />
                </View>
                <Text style={[styles.leaderSymbol, { color: colors.text }]}>
                  {item.symbol}
                </Text>
              </View>
              <Text
                style={[styles.leaderName, { color: colors.textMuted }]}
                numberOfLines={2}
              >
                {item.name}
              </Text>
              <Text style={[styles.leaderPrice, { color: colors.text }]}>
                {formatCurrency(item.price)}
              </Text>
            </Surface>
          ))}
        </View>
      </View>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  header: {
    gap: 10,
    paddingTop: 12,
  },
  kicker: {
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1.6,
    textTransform: "uppercase",
  },
  title: {
    fontSize: 34,
    lineHeight: 38,
    fontWeight: "900",
    letterSpacing: -0.9,
  },
  body: {
    fontSize: 15,
    lineHeight: 24,
  },
  heroPanel: {
    gap: 16,
  },
  heroRow: {
    flexDirection: "row",
    gap: 12,
  },
  heroStat: {
    flex: 1,
    gap: 6,
  },
  heroValue: {
    fontSize: 19,
    fontWeight: "800",
  },
  heroLabel: {
    fontSize: 12,
    lineHeight: 18,
  },
  heroBody: {
    fontSize: 14,
    lineHeight: 21,
  },
  rail: {
    gap: 10,
    paddingRight: 20,
  },
  predictionCard: {
    gap: 16,
  },
  predictionTop: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 12,
  },
  copyBlock: {
    flex: 1,
    gap: 4,
  },
  predictionSymbol: {
    fontSize: 22,
    fontWeight: "900",
  },
  predictionName: {
    fontSize: 14,
    lineHeight: 21,
  },
  deltaPill: {
    alignSelf: "flex-start",
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderRadius: 999,
  },
  inlineHint: {
    fontSize: 13,
    lineHeight: 20,
  },
  metricGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 12,
  },
  metricItem: {
    minWidth: "47%",
    flexGrow: 1,
    gap: 6,
  },
  metricLabel: {
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 0.3,
  },
  metricValue: {
    fontSize: 18,
    fontWeight: "800",
  },
  marketCardWrap: {
    width: 220,
  },
  indexGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 12,
    marginTop: 14,
  },
  indexCard: {
    width: "47%",
    gap: 8,
  },
  indexSymbol: {
    fontSize: 17,
    fontWeight: "800",
  },
  indexName: {
    fontSize: 13,
    lineHeight: 19,
  },
  indexChange: {
    fontSize: 15,
    fontWeight: "800",
  },
  studio: {
    gap: 16,
  },
  fieldBlock: {
    gap: 10,
  },
  groupLabel: {
    fontSize: 13,
    fontWeight: "700",
  },
  chipWrap: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  doubleFieldRow: {
    flexDirection: "row",
    gap: 12,
  },
  flexField: {
    flex: 1,
  },
  innerPanel: {
    gap: 12,
  },
  innerTitle: {
    fontSize: 17,
    fontWeight: "800",
  },
  innerValue: {
    fontSize: 28,
    fontWeight: "900",
  },
  leaderList: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 12,
  },
  leaderCard: {
    width: "47%",
    gap: 12,
  },
  leaderTop: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  iconBadge: {
    width: 34,
    height: 34,
    borderRadius: 999,
    alignItems: "center",
    justifyContent: "center",
  },
  leaderSymbol: {
    fontSize: 15,
    fontWeight: "800",
  },
  leaderName: {
    fontSize: 13,
    lineHeight: 20,
  },
  leaderPrice: {
    fontSize: 18,
    fontWeight: "800",
  },
});

