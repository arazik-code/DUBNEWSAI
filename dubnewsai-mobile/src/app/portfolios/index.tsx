import { useMemo, useState } from "react";

import { useMutation, useQuery } from "@tanstack/react-query";
import { router } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { AccessGate } from "@/components/access-gate";
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
import { useAuthStore } from "@/lib/state/auth-store";
import { useAppTheme } from "@/lib/theme";

const PORTFOLIO_TYPES = ["mixed", "stocks", "real_estate"];

export default function PortfoliosScreen() {
  const { colors } = useAppTheme();
  const user = useAuthStore((state) => state.user);
  const [portfolioName, setPortfolioName] = useState("");
  const [portfolioDescription, setPortfolioDescription] = useState("");
  const [portfolioType, setPortfolioType] = useState("mixed");
  const [watchlistName, setWatchlistName] = useState("");
  const [watchlistDescription, setWatchlistDescription] = useState("");
  const [threshold, setThreshold] = useState("5");

  const featureAccessQuery = useQuery({
    queryKey: ["mobile-feature-access-portfolios"],
    queryFn: mobileApi.getFeatureAccess,
    enabled: Boolean(user),
  });

  const hasAccess =
    featureAccessQuery.data?.find((item) => item.feature_key === "portfolios")?.has_access ??
    false;

  const portfoliosQuery = useQuery({
    queryKey: ["mobile-portfolios"],
    queryFn: mobileApi.getPortfolios,
    enabled: Boolean(user && hasAccess),
  });

  const watchlistsQuery = useQuery({
    queryKey: ["mobile-watchlists"],
    queryFn: mobileApi.getWatchlists,
    enabled: Boolean(user && hasAccess),
  });

  const assetCatalogQuery = useQuery({
    queryKey: ["mobile-asset-catalog"],
    queryFn: mobileApi.getAssetCatalog,
    enabled: Boolean(user && hasAccess),
  });

  const createPortfolioMutation = useMutation({
    mutationFn: () =>
      mobileApi.createPortfolio({
        name: portfolioName.trim(),
        description: portfolioDescription.trim() || undefined,
        portfolio_type: portfolioType,
        base_currency: "AED",
      }),
    onSuccess: async (portfolio) => {
      setPortfolioName("");
      setPortfolioDescription("");
      await queryClient.invalidateQueries({ queryKey: ["mobile-portfolios"] });
      router.push(`/portfolios/${portfolio.id}`);
    },
  });

  const createWatchlistMutation = useMutation({
    mutationFn: () =>
      mobileApi.createWatchlist({
        name: watchlistName.trim(),
        description: watchlistDescription.trim() || undefined,
        alert_on_change: true,
        change_threshold_percent: Number(threshold || "5"),
      }),
    onSuccess: async () => {
      setWatchlistName("");
      setWatchlistDescription("");
      await queryClient.invalidateQueries({ queryKey: ["mobile-watchlists"] });
    },
  });

  const totalValue = useMemo(
    () => (portfoliosQuery.data ?? []).reduce((sum, portfolio) => sum + portfolio.total_value_aed, 0),
    [portfoliosQuery.data],
  );

  if (!user) {
    return (
      <ScreenShell>
        <AccessGate
          title="Investor suite requires sign-in"
          body="Create portfolios, track watchlists, and manage transactions after signing in."
        />
      </ScreenShell>
    );
  }

  if (featureAccessQuery.isLoading) {
    return (
      <ScreenShell>
        <StatePanel title="Loading access" body="Checking your investor suite permissions." loading />
      </ScreenShell>
    );
  }

  if (featureAccessQuery.isError) {
    return (
      <ScreenShell>
        <StatePanel title="Access check unavailable" body="Portfolio permissions could not be verified right now." />
      </ScreenShell>
    );
  }

  if (!hasAccess) {
    return (
      <ScreenShell>
        <AccessGate
          title="Investor suite is admin-granted"
          body="Your admin needs to grant portfolios access before mobile portfolio tools can open."
        />
      </ScreenShell>
    );
  }

  if (portfoliosQuery.isLoading || watchlistsQuery.isLoading || assetCatalogQuery.isLoading) {
    return (
      <ScreenShell>
        <StatePanel title="Loading investor suite" body="Syncing portfolios, watchlists, and asset catalog." loading />
      </ScreenShell>
    );
  }

  if (portfoliosQuery.isError || watchlistsQuery.isError || assetCatalogQuery.isError) {
    return (
      <ScreenShell>
        <StatePanel title="Investor suite unavailable" body="Portfolio data could not be loaded right now." />
      </ScreenShell>
    );
  }

  return (
    <ScreenShell>
      <View style={styles.header}>
        <Text style={[styles.kicker, { color: colors.accent }]}>Investor suite</Text>
        <Text style={[styles.title, { color: colors.text }]}>Portfolios and watchlists built for mobile.</Text>
        <Text style={[styles.body, { color: colors.textMuted }]}>
          Create a portfolio, spin up a watchlist, and move straight into holding-level detail without going back to desktop.
        </Text>
      </View>

      <View style={styles.grid}>
        <Surface style={styles.summaryCard}>
          <Text style={[styles.summaryLabel, { color: colors.textMuted }]}>Total value</Text>
          <Text style={[styles.summaryValue, { color: colors.text }]}>{formatCurrency(totalValue)}</Text>
        </Surface>
        <Surface style={styles.summaryCard}>
          <Text style={[styles.summaryLabel, { color: colors.textMuted }]}>Watchlists</Text>
          <Text style={[styles.summaryValue, { color: colors.text }]}>{watchlistsQuery.data?.length ?? 0}</Text>
        </Surface>
      </View>

      <Surface style={styles.formCard}>
        <Text style={[styles.formTitle, { color: colors.text }]}>Create portfolio</Text>
        <TextField label="Portfolio name" value={portfolioName} onChangeText={setPortfolioName} />
        <TextField
          label="Description"
          value={portfolioDescription}
          onChangeText={setPortfolioDescription}
          placeholder="Dubai income sleeve, growth basket, long-term holdings..."
        />
        <View style={styles.chipWrap}>
          {PORTFOLIO_TYPES.map((type) => (
            <ChoiceChip
              key={type}
              label={sentenceCase(type)}
              selected={portfolioType === type}
              onPress={() => setPortfolioType(type)}
            />
          ))}
        </View>
        {createPortfolioMutation.error ? (
          <Text style={[styles.errorText, { color: colors.danger }]}>{createPortfolioMutation.error.message}</Text>
        ) : null}
        <PrimaryButton
          label={createPortfolioMutation.isPending ? "Creating portfolio..." : "Create portfolio"}
          onPress={() => createPortfolioMutation.mutate()}
          loading={createPortfolioMutation.isPending}
        />
      </Surface>

      <Surface style={styles.formCard}>
        <Text style={[styles.formTitle, { color: colors.text }]}>Create watchlist</Text>
        <TextField label="Watchlist name" value={watchlistName} onChangeText={setWatchlistName} />
        <TextField
          label="Description"
          value={watchlistDescription}
          onChangeText={setWatchlistDescription}
          placeholder="Momentum names, developer watchlist, entry candidates..."
        />
        <TextField
          label="Alert threshold %"
          value={threshold}
          onChangeText={setThreshold}
          keyboardType="numeric"
        />
        {createWatchlistMutation.error ? (
          <Text style={[styles.errorText, { color: colors.danger }]}>{createWatchlistMutation.error.message}</Text>
        ) : null}
        <PrimaryButton
          label={createWatchlistMutation.isPending ? "Creating watchlist..." : "Create watchlist"}
          onPress={() => createWatchlistMutation.mutate()}
          loading={createWatchlistMutation.isPending}
          variant="secondary"
        />
      </Surface>

      <View>
        <SectionHeader
          eyebrow="Portfolios"
          title="Your live books"
          description="Tap into any portfolio to add transactions or inspect holdings."
        />
        <View style={styles.list}>
          {(portfoliosQuery.data ?? []).map((portfolio) => (
            <Surface key={portfolio.id} style={styles.portfolioCard}>
              <Text style={[styles.portfolioTitle, { color: colors.text }]}>{portfolio.name}</Text>
              <Text style={[styles.portfolioMeta, { color: colors.textMuted }]}>
                {sentenceCase(portfolio.portfolio_type)} · {portfolio.holdings.length} holdings
              </Text>
              <Text style={[styles.portfolioValue, { color: colors.text }]}>
                {formatCurrency(portfolio.total_value_aed)}
              </Text>
              <Text
                style={[
                  styles.portfolioReturn,
                  { color: portfolio.total_return_percent >= 0 ? colors.success : colors.danger },
                ]}
              >
                {formatPercent(portfolio.total_return_percent)}
              </Text>
              <PrimaryButton
                label="Open portfolio"
                variant="secondary"
                onPress={() => router.push(`/portfolios/${portfolio.id}`)}
              />
            </Surface>
          ))}
        </View>
      </View>

      <View>
        <SectionHeader
          eyebrow="Watchlists"
          title="Your tracking queues"
          description="Mobile summary of the lists monitoring price moves and entry levels."
        />
        <View style={styles.list}>
          {(watchlistsQuery.data ?? []).map((watchlist) => (
            <Surface key={watchlist.id} style={styles.watchlistCard}>
              <Text style={[styles.watchlistTitle, { color: colors.text }]}>{watchlist.name}</Text>
              <Text style={[styles.portfolioMeta, { color: colors.textMuted }]}>
                {watchlist.items.length} items · threshold {watchlist.change_threshold_percent.toFixed(1)}%
              </Text>
            </Surface>
          ))}
        </View>
      </View>

      <View>
        <SectionHeader
          eyebrow="Catalog"
          title="Quick-pick assets"
          description="A curated asset list to speed up mobile transaction entry."
        />
        <View style={styles.list}>
          {(assetCatalogQuery.data ?? []).slice(0, 8).map((asset) => (
            <Surface key={asset.canonical_symbol} style={styles.assetCard}>
              <Text style={[styles.assetSymbol, { color: colors.text }]}>{asset.symbol}</Text>
              <Text style={[styles.assetName, { color: colors.textMuted }]} numberOfLines={1}>
                {asset.name}
              </Text>
              <Text style={[styles.assetPrice, { color: colors.text }]}>
                {formatCurrency(asset.price, asset.currency)}
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
    fontSize: 32,
    lineHeight: 36,
    fontWeight: "900",
    letterSpacing: -0.9,
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
    letterSpacing: 1.2,
  },
  summaryValue: {
    fontSize: 24,
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
  errorText: {
    fontSize: 13,
    fontWeight: "700",
  },
  list: {
    gap: 12,
  },
  portfolioCard: {
    gap: 10,
  },
  portfolioTitle: {
    fontSize: 18,
    fontWeight: "800",
  },
  portfolioMeta: {
    fontSize: 13,
    lineHeight: 20,
  },
  portfolioValue: {
    fontSize: 24,
    fontWeight: "900",
  },
  portfolioReturn: {
    fontSize: 16,
    fontWeight: "800",
  },
  watchlistCard: {
    gap: 6,
  },
  watchlistTitle: {
    fontSize: 17,
    fontWeight: "800",
  },
  assetCard: {
    gap: 8,
  },
  assetSymbol: {
    fontSize: 16,
    fontWeight: "800",
  },
  assetName: {
    fontSize: 13,
  },
  assetPrice: {
    fontSize: 17,
    fontWeight: "800",
  },
});
