import { router, useLocalSearchParams } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { ScrollView, StyleSheet, Text, View } from "react-native";

import { PrimaryButton } from "@/components/primary-button";
import { ScreenShell } from "@/components/screen-shell";
import { StatePanel } from "@/components/state-panel";
import { Surface } from "@/components/surface";
import { mobileApi } from "@/lib/api/queries";
import { formatCurrency, formatPercent, sentenceCase } from "@/lib/formatters";
import { useAppTheme } from "@/lib/theme";

export default function MarketSymbolScreen() {
  const { colors } = useAppTheme();
  const params = useLocalSearchParams<{ symbol?: string }>();
  const symbol = typeof params.symbol === "string" ? decodeURIComponent(params.symbol) : "";

  const symbolQuery = useQuery({
    queryKey: ["mobile-market-symbol", symbol],
    queryFn: () => mobileApi.getMarketSymbol(symbol),
    enabled: Boolean(symbol),
  });

  const predictionQuery = useQuery({
    queryKey: ["mobile-market-symbol-prediction", symbol],
    queryFn: () => mobileApi.getPricePrediction(symbol, 30),
    enabled: Boolean(symbol),
  });

  if (symbolQuery.isLoading) {
    return (
      <ScreenShell>
        <StatePanel title="Loading symbol" body="Pulling price action and forecast." loading />
      </ScreenShell>
    );
  }

  if (symbolQuery.isError || !symbolQuery.data) {
    return (
      <ScreenShell>
        <StatePanel title="Symbol unavailable" body="This market instrument could not be loaded right now." />
      </ScreenShell>
    );
  }

  const item = symbolQuery.data;

  return (
    <ScreenShell>
      <View style={styles.header}>
        <Text style={[styles.kicker, { color: colors.accent }]}>{item.exchange || item.market_type}</Text>
        <Text style={[styles.title, { color: colors.text }]}>{item.symbol}</Text>
        <Text style={[styles.subtitle, { color: colors.textMuted }]}>{item.name}</Text>
      </View>

      <Surface style={styles.pricePanel}>
        <Text style={[styles.price, { color: colors.text }]}>{formatCurrency(item.price, item.currency)}</Text>
        <Text
          style={[
            styles.change,
            { color: item.change_percent >= 0 ? colors.success : colors.danger },
          ]}
        >
          {formatPercent(item.change_percent)}
        </Text>
        <View style={styles.metricGrid}>
          <View style={styles.metricItem}>
            <Text style={[styles.metricLabel, { color: colors.textMuted }]}>Open</Text>
            <Text style={[styles.metricValue, { color: colors.text }]}>
              {formatCurrency(item.open_price ?? item.price, item.currency)}
            </Text>
          </View>
          <View style={styles.metricItem}>
            <Text style={[styles.metricLabel, { color: colors.textMuted }]}>High</Text>
            <Text style={[styles.metricValue, { color: colors.text }]}>
              {formatCurrency(item.high_price ?? item.price, item.currency)}
            </Text>
          </View>
          <View style={styles.metricItem}>
            <Text style={[styles.metricLabel, { color: colors.textMuted }]}>Low</Text>
            <Text style={[styles.metricValue, { color: colors.text }]}>
              {formatCurrency(item.low_price ?? item.price, item.currency)}
            </Text>
          </View>
          <View style={styles.metricItem}>
            <Text style={[styles.metricLabel, { color: colors.textMuted }]}>Volume</Text>
            <Text style={[styles.metricValue, { color: colors.text }]}>
              {(item.volume ?? 0).toLocaleString("en-US")}
            </Text>
          </View>
        </View>
      </Surface>

      <Surface style={styles.forecastPanel}>
        <Text style={[styles.panelTitle, { color: colors.text }]}>30-day forecast</Text>
        {predictionQuery.isLoading ? (
          <Text style={[styles.supportText, { color: colors.textMuted }]}>Building forecast...</Text>
        ) : predictionQuery.data ? (
          <>
            <View style={styles.metricGrid}>
              <View style={styles.metricItem}>
                <Text style={[styles.metricLabel, { color: colors.textMuted }]}>Target</Text>
                <Text style={[styles.metricValue, { color: colors.text }]}>
                  {formatCurrency(predictionQuery.data.prediction.target_price, item.currency)}
                </Text>
              </View>
              <View style={styles.metricItem}>
                <Text style={[styles.metricLabel, { color: colors.textMuted }]}>Expected return</Text>
                <Text
                  style={[
                    styles.metricValue,
                    {
                      color:
                        predictionQuery.data.prediction.expected_return_percent >= 0
                          ? colors.success
                          : colors.danger,
                    },
                  ]}
                >
                  {formatPercent(predictionQuery.data.prediction.expected_return_percent)}
                </Text>
              </View>
              <View style={styles.metricItem}>
                <Text style={[styles.metricLabel, { color: colors.textMuted }]}>Trend</Text>
                <Text style={[styles.metricValue, { color: colors.text }]}>
                  {sentenceCase(predictionQuery.data.trend.direction)}
                </Text>
              </View>
              <View style={styles.metricItem}>
                <Text style={[styles.metricLabel, { color: colors.textMuted }]}>Confidence</Text>
                <Text style={[styles.metricValue, { color: colors.text }]}>
                  {(predictionQuery.data.model_info.r_squared * 100).toFixed(0)}%
                </Text>
              </View>
            </View>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.seriesRail}>
              {predictionQuery.data.forecast_series.slice(0, 7).map((point) => (
                <Surface key={point.days_ahead} style={styles.seriesCard}>
                  <Text style={[styles.seriesLabel, { color: colors.textMuted }]}>Day {point.days_ahead}</Text>
                  <Text style={[styles.seriesValue, { color: colors.text }]}>
                    {formatCurrency(point.predicted_price, item.currency)}
                  </Text>
                </Surface>
              ))}
            </ScrollView>
          </>
        ) : (
          <Text style={[styles.supportText, { color: colors.textMuted }]}>No forecast available.</Text>
        )}
      </Surface>

      <PrimaryButton label="Back to market" variant="secondary" onPress={() => router.back()} />
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  header: {
    gap: 8,
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
    fontWeight: "900",
    letterSpacing: -0.9,
  },
  subtitle: {
    fontSize: 15,
    lineHeight: 22,
  },
  pricePanel: {
    gap: 14,
  },
  price: {
    fontSize: 34,
    fontWeight: "900",
  },
  change: {
    fontSize: 18,
    fontWeight: "800",
  },
  metricGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 12,
  },
  metricItem: {
    minWidth: "47%",
    gap: 6,
    flexGrow: 1,
  },
  metricLabel: {
    fontSize: 12,
    fontWeight: "700",
  },
  metricValue: {
    fontSize: 17,
    fontWeight: "800",
  },
  forecastPanel: {
    gap: 14,
  },
  panelTitle: {
    fontSize: 18,
    fontWeight: "800",
  },
  supportText: {
    fontSize: 14,
    lineHeight: 21,
  },
  seriesRail: {
    gap: 12,
    paddingRight: 20,
  },
  seriesCard: {
    minWidth: 138,
    gap: 8,
  },
  seriesLabel: {
    fontSize: 12,
    fontWeight: "700",
  },
  seriesValue: {
    fontSize: 16,
    fontWeight: "800",
  },
});
