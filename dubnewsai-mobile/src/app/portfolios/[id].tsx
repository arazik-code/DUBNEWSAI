import { useState } from "react";

import { useMutation, useQuery } from "@tanstack/react-query";
import { router, useLocalSearchParams } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { ChoiceChip } from "@/components/choice-chip";
import { PrimaryButton } from "@/components/primary-button";
import { ScreenShell } from "@/components/screen-shell";
import { SectionHeader } from "@/components/section-header";
import { StatePanel } from "@/components/state-panel";
import { Surface } from "@/components/surface";
import { TextField } from "@/components/text-field";
import { mobileApi } from "@/lib/api/queries";
import { formatCurrency, formatPercent, sentenceCase } from "@/lib/formatters";
import { queryClient } from "@/lib/providers/app-providers";
import { useAppTheme } from "@/lib/theme";

const TRANSACTION_TYPES = ["buy", "sell", "dividend", "split"];

export default function PortfolioDetailScreen() {
  const { colors } = useAppTheme();
  const params = useLocalSearchParams<{ id?: string }>();
  const portfolioId = Number(params.id);
  const [transactionType, setTransactionType] = useState("buy");
  const [selectedSymbol, setSelectedSymbol] = useState("");
  const [quantity, setQuantity] = useState("100");
  const [price, setPrice] = useState("0");
  const [notes, setNotes] = useState("");

  const portfolioQuery = useQuery({
    queryKey: ["mobile-portfolio-detail", portfolioId],
    queryFn: () => mobileApi.getPortfolio(portfolioId),
    enabled: Number.isFinite(portfolioId),
  });

  const analyticsQuery = useQuery({
    queryKey: ["mobile-portfolio-analytics", portfolioId],
    queryFn: () => mobileApi.getPortfolioAnalytics(portfolioId),
    enabled: Number.isFinite(portfolioId),
  });

  const assetCatalogQuery = useQuery({
    queryKey: ["mobile-asset-catalog-detail"],
    queryFn: mobileApi.getAssetCatalog,
    enabled: Number.isFinite(portfolioId),
  });

  const transactionMutation = useMutation({
    mutationFn: () =>
      mobileApi.addPortfolioTransaction(portfolioId, {
        transaction_type: transactionType,
        symbol: selectedSymbol,
        quantity: Number(quantity || "0"),
        price: Number(price || "0"),
        transaction_date: new Date().toISOString(),
        notes: notes.trim() || undefined,
      }),
    onSuccess: async () => {
      setNotes("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["mobile-portfolio-detail", portfolioId] }),
        queryClient.invalidateQueries({ queryKey: ["mobile-portfolio-analytics", portfolioId] }),
        queryClient.invalidateQueries({ queryKey: ["mobile-portfolios"] }),
      ]);
    },
  });

  if (portfolioQuery.isLoading || analyticsQuery.isLoading || assetCatalogQuery.isLoading) {
    return (
      <ScreenShell>
        <StatePanel title="Loading portfolio" body="Syncing holdings and analytics." loading />
      </ScreenShell>
    );
  }

  if (portfolioQuery.isError || analyticsQuery.isError || !portfolioQuery.data || !analyticsQuery.data) {
    return (
      <ScreenShell>
        <StatePanel title="Portfolio unavailable" body="This portfolio could not be loaded right now." />
      </ScreenShell>
    );
  }

  const portfolio = portfolioQuery.data;
  const analytics = analyticsQuery.data;
  const quickAssets = (assetCatalogQuery.data ?? []).slice(0, 8);

  return (
    <ScreenShell>
      <View style={styles.header}>
        <Text style={[styles.kicker, { color: colors.accent }]}>
          {sentenceCase(portfolio.portfolio_type)}
        </Text>
        <Text style={[styles.title, { color: colors.text }]}>{portfolio.name}</Text>
        <Text style={[styles.body, { color: colors.textMuted }]}>
          {portfolio.description || "Holdings, analytics, and transaction entry in one mobile surface."}
        </Text>
      </View>

      <View style={styles.grid}>
        <Surface style={styles.summaryCard}>
          <Text style={[styles.summaryLabel, { color: colors.textMuted }]}>Market value</Text>
          <Text style={[styles.summaryValue, { color: colors.text }]}>
            {formatCurrency(portfolio.total_value_aed)}
          </Text>
        </Surface>
        <Surface style={styles.summaryCard}>
          <Text style={[styles.summaryLabel, { color: colors.textMuted }]}>Return</Text>
          <Text
            style={[
              styles.summaryValue,
              { color: portfolio.total_return_percent >= 0 ? colors.success : colors.danger },
            ]}
          >
            {formatPercent(portfolio.total_return_percent)}
          </Text>
        </Surface>
      </View>

      <Surface style={styles.formCard}>
        <Text style={[styles.formTitle, { color: colors.text }]}>Add transaction</Text>
        <View style={styles.chipWrap}>
          {TRANSACTION_TYPES.map((type) => (
            <ChoiceChip
              key={type}
              label={sentenceCase(type)}
              selected={transactionType === type}
              onPress={() => setTransactionType(type)}
            />
          ))}
        </View>
        <View style={styles.chipWrap}>
          {quickAssets.map((asset) => (
            <ChoiceChip
              key={asset.canonical_symbol}
              label={asset.symbol}
              selected={selectedSymbol === asset.symbol}
              onPress={() => {
                setSelectedSymbol(asset.symbol);
                setPrice(String(asset.price));
              }}
            />
          ))}
        </View>
        <TextField label="Symbol" value={selectedSymbol} onChangeText={setSelectedSymbol} autoCapitalize="characters" />
        <View style={styles.row}>
          <View style={styles.flexField}>
            <TextField label="Quantity" value={quantity} onChangeText={setQuantity} keyboardType="numeric" />
          </View>
          <View style={styles.flexField}>
            <TextField label="Price" value={price} onChangeText={setPrice} keyboardType="numeric" />
          </View>
        </View>
        <TextField label="Notes" value={notes} onChangeText={setNotes} placeholder="Optional transaction context..." />
        {transactionMutation.error ? (
          <Text style={[styles.errorText, { color: colors.danger }]}>{transactionMutation.error.message}</Text>
        ) : null}
        <PrimaryButton
          label={transactionMutation.isPending ? "Saving transaction..." : "Add transaction"}
          onPress={() => transactionMutation.mutate()}
          loading={transactionMutation.isPending}
        />
      </Surface>

      <View>
        <SectionHeader
          eyebrow="Holdings"
          title="Current positions"
          description="A compact mobile read of each position in the book."
        />
        <View style={styles.list}>
          {portfolio.holdings.map((holding) => (
            <Surface key={holding.id} style={styles.holdingCard}>
              <Text style={[styles.holdingSymbol, { color: colors.text }]}>{holding.symbol}</Text>
              <Text style={[styles.holdingMeta, { color: colors.textMuted }]} numberOfLines={1}>
                {holding.asset_name || "Tracked asset"}
              </Text>
              <Text style={[styles.holdingValue, { color: colors.text }]}>
                {formatCurrency(holding.current_value ?? 0)}
              </Text>
              <Text
                style={[
                  styles.holdingReturn,
                  {
                    color:
                      (holding.unrealized_gain_loss_percent ?? 0) >= 0 ? colors.success : colors.danger,
                  },
                ]}
              >
                {formatPercent(holding.unrealized_gain_loss_percent ?? 0)}
              </Text>
            </Surface>
          ))}
        </View>
      </View>

      <Surface style={styles.analyticsCard}>
        <Text style={[styles.formTitle, { color: colors.text }]}>Analytics snapshot</Text>
        <View style={styles.grid}>
          <View style={styles.summaryCard}>
            <Text style={[styles.summaryLabel, { color: colors.textMuted }]}>Sharpe</Text>
            <Text style={[styles.summaryValue, { color: colors.text }]}>
              {String(analytics.risk_metrics.sharpe_ratio ?? "--")}
            </Text>
          </View>
          <View style={styles.summaryCard}>
            <Text style={[styles.summaryLabel, { color: colors.textMuted }]}>Volatility</Text>
            <Text style={[styles.summaryValue, { color: colors.text }]}>
              {String(analytics.risk_metrics.volatility ?? "--")}
            </Text>
          </View>
        </View>
      </Surface>

      <PrimaryButton label="Back to portfolios" variant="secondary" onPress={() => router.back()} />
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
    fontSize: 30,
    lineHeight: 34,
    fontWeight: "900",
    letterSpacing: -0.8,
  },
  body: {
    fontSize: 15,
    lineHeight: 24,
  },
  grid: {
    flexDirection: "row",
    gap: 12,
  },
  summaryCard: {
    flex: 1,
    gap: 8,
  },
  summaryLabel: {
    fontSize: 12,
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: 1.1,
  },
  summaryValue: {
    fontSize: 23,
    fontWeight: "900",
  },
  formCard: {
    gap: 14,
  },
  formTitle: {
    fontSize: 18,
    fontWeight: "800",
  },
  chipWrap: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  row: {
    flexDirection: "row",
    gap: 12,
  },
  flexField: {
    flex: 1,
  },
  errorText: {
    fontSize: 13,
    fontWeight: "700",
  },
  list: {
    gap: 12,
  },
  holdingCard: {
    gap: 8,
  },
  holdingSymbol: {
    fontSize: 17,
    fontWeight: "800",
  },
  holdingMeta: {
    fontSize: 13,
  },
  holdingValue: {
    fontSize: 20,
    fontWeight: "800",
  },
  holdingReturn: {
    fontSize: 15,
    fontWeight: "800",
  },
  analyticsCard: {
    gap: 12,
  },
});
