import { useMemo } from "react";

import { useMutation, useQuery } from "@tanstack/react-query";
import { router } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { AccessGate } from "@/components/access-gate";
import { PrimaryButton } from "@/components/primary-button";
import { ScreenShell } from "@/components/screen-shell";
import { SectionHeader } from "@/components/section-header";
import { StatePanel } from "@/components/state-panel";
import { Surface } from "@/components/surface";
import { mobileApi } from "@/lib/api/queries";
import { formatCurrency } from "@/lib/formatters";
import { queryClient } from "@/lib/providers/app-providers";
import { useAuthStore } from "@/lib/state/auth-store";
import { useAppTheme } from "@/lib/theme";

export default function CompetitorsScreen() {
  const { colors } = useAppTheme();
  const user = useAuthStore((state) => state.user);

  const featureAccessQuery = useQuery({
    queryKey: ["mobile-feature-access-competitors"],
    queryFn: mobileApi.getFeatureAccess,
    enabled: Boolean(user),
  });

  const hasAccess =
    featureAccessQuery.data?.find((item) => item.feature_key === "competitors")?.has_access ??
    false;

  const trackedQuery = useQuery({
    queryKey: ["mobile-competitors"],
    queryFn: mobileApi.getCompetitors,
    enabled: Boolean(user && hasAccess),
  });

  const catalogQuery = useQuery({
    queryKey: ["mobile-competitor-catalog"],
    queryFn: mobileApi.getCompetitorCatalog,
    enabled: Boolean(user && hasAccess),
  });

  const trackedNames = useMemo(
    () => new Set((trackedQuery.data ?? []).map((item) => item.name.toLowerCase())),
    [trackedQuery.data],
  );

  const createMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => mobileApi.createCompetitor(payload),
    onSuccess: async (competitor) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["mobile-competitors"] }),
        queryClient.invalidateQueries({ queryKey: ["mobile-competitor-catalog"] }),
      ]);
      router.push(`/competitors/${competitor.id}`);
    },
  });

  if (!user) {
    return (
      <ScreenShell>
        <AccessGate
          title="Competitors requires sign-in"
          body="Track competitors and open intelligence analysis after authentication."
        />
      </ScreenShell>
    );
  }

  if (featureAccessQuery.isLoading) {
    return (
      <ScreenShell>
        <StatePanel title="Loading access" body="Checking competitor intelligence permissions." loading />
      </ScreenShell>
    );
  }

  if (featureAccessQuery.isError) {
    return (
      <ScreenShell>
        <StatePanel title="Access check unavailable" body="Competitor permissions could not be verified right now." />
      </ScreenShell>
    );
  }

  if (!hasAccess) {
    return (
      <ScreenShell>
        <AccessGate
          title="Competitors is admin-granted"
          body="Your admin needs to grant competitor access before this mobile surface can open."
        />
      </ScreenShell>
    );
  }

  if (trackedQuery.isLoading || catalogQuery.isLoading) {
    return (
      <ScreenShell>
        <StatePanel title="Loading competitors" body="Bringing in tracked companies and curated catalog." loading />
      </ScreenShell>
    );
  }

  if (trackedQuery.isError || catalogQuery.isError) {
    return (
      <ScreenShell>
        <StatePanel title="Competitors unavailable" body="Competitive intelligence could not be loaded right now." />
      </ScreenShell>
    );
  }

  return (
    <ScreenShell>
      <View style={styles.header}>
        <Text style={[styles.kicker, { color: colors.accent }]}>Competitors</Text>
        <Text style={[styles.title, { color: colors.text }]}>Track the names shaping your market.</Text>
        <Text style={[styles.body, { color: colors.textMuted }]}>
          Start from the curated catalog, then open deeper SWOT and threat-level analysis on demand.
        </Text>
      </View>

      <View>
        <SectionHeader
          eyebrow="Tracked"
          title="Your active competitor set"
          description="Tap a tracked company to open the full analysis stack."
        />
        <View style={styles.list}>
          {(trackedQuery.data ?? []).map((competitor) => (
            <Surface key={competitor.id} style={styles.card}>
              <Text style={[styles.cardTitle, { color: colors.text }]}>{competitor.name}</Text>
              <Text style={[styles.cardMeta, { color: colors.textMuted }]}>
                {competitor.ticker_symbol || "Private"} · {competitor.sector || competitor.industry || "Market intelligence"}
              </Text>
              <Text style={[styles.cardBody, { color: colors.textSoft }]}>
                Market share {competitor.market_share_percent?.toFixed(1) ?? "--"}% · revenue growth{" "}
                {competitor.revenue_growth_rate?.toFixed(1) ?? "--"}%
              </Text>
              <PrimaryButton
                label="Open analysis"
                variant="secondary"
                onPress={() => router.push(`/competitors/${competitor.id}`)}
              />
            </Surface>
          ))}
        </View>
      </View>

      <View>
        <SectionHeader
          eyebrow="Catalog"
          title="Curated companies ready to track"
          description="No manual junk entries. Track from the catalog so the analysis layer stays grounded."
        />
        <View style={styles.list}>
          {(catalogQuery.data ?? []).map((company) => {
            const alreadyTracked = trackedNames.has(company.name.toLowerCase()) || company.tracked;
            return (
              <Surface key={company.name} style={styles.card}>
                <Text style={[styles.cardTitle, { color: colors.text }]}>{company.name}</Text>
                <Text style={[styles.cardMeta, { color: colors.textMuted }]}>
                  {company.ticker_symbol || "Private"} · {company.headquarters || "Regional operator"}
                </Text>
                <Text style={[styles.cardBody, { color: colors.textSoft }]}>
                  {company.description || "Curated competitor profile for tracking and analysis."}
                </Text>
                <Text style={[styles.cardMeta, { color: colors.textMuted }]}>
                  {company.market_cap ? formatCurrency(company.market_cap, "USD") : "Market cap undisclosed"}
                </Text>
                <PrimaryButton
                  label={alreadyTracked ? "Already tracked" : createMutation.isPending ? "Tracking..." : "Track competitor"}
                  variant="secondary"
                  disabled={alreadyTracked}
                  loading={createMutation.isPending && !alreadyTracked}
                  onPress={() =>
                    createMutation.mutate({
                      name: company.name,
                      official_name: company.name,
                      industry: company.industry,
                      sector: company.sector,
                      headquarters: company.headquarters,
                      ticker_symbol: company.ticker_symbol,
                      description: company.description,
                      market_cap: company.market_cap,
                      revenue_growth_rate: company.revenue_growth_rate,
                      market_share_percent: company.market_share_percent,
                      tags: company.tags,
                    })
                  }
                />
              </Surface>
            );
          })}
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
  list: {
    gap: 12,
  },
  card: {
    gap: 10,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: "800",
  },
  cardMeta: {
    fontSize: 13,
    lineHeight: 20,
  },
  cardBody: {
    fontSize: 14,
    lineHeight: 22,
  },
});
