import { useMemo } from "react";

import { Ionicons } from "@expo/vector-icons";
import { useQuery } from "@tanstack/react-query";
import { router } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { AccessGate } from "@/components/access-gate";
import { ModuleCard } from "@/components/module-card";
import { PrimaryButton } from "@/components/primary-button";
import { ScreenShell } from "@/components/screen-shell";
import { SectionHeader } from "@/components/section-header";
import { StatePanel } from "@/components/state-panel";
import { Surface } from "@/components/surface";
import { mobileApi } from "@/lib/api/queries";
import { formatCompactNumber, formatCurrency, formatPercent } from "@/lib/formatters";
import { useAuthStore } from "@/lib/state/auth-store";
import { useAppTheme } from "@/lib/theme";

const MODULES: Record<
  string,
  { route: string; description: string; icon: keyof typeof Ionicons.glyphMap }
> = {
  analytics: {
    route: "/market",
    description: "Forecasts, opportunity signals, and market movement.",
    icon: "analytics",
  },
  alerts: {
    route: "/alerts",
    description: "Rules, recent triggers, and high-priority monitoring.",
    icon: "notifications",
  },
  settings: {
    route: "/profile",
    description: "Account state, access grants, and workspace controls.",
    icon: "settings",
  },
  portfolios: {
    route: "/portfolios",
    description: "Portfolio creation, watchlists, analytics, and transactions.",
    icon: "briefcase",
  },
  competitors: {
    route: "/competitors",
    description: "Tracked competitors, SWOT, and threat-level analysis.",
    icon: "git-compare",
  },
  executive: {
    route: "/executive",
    description: "Leadership summary, priorities, and strategic risk view.",
    icon: "ribbon",
  },
  teams: {
    route: "/teams",
    description: "Team spaces, shared access, and activity trails.",
    icon: "people",
  },
};

export default function WorkspaceScreen() {
  const { colors } = useAppTheme();
  const user = useAuthStore((state) => state.user);

  const workspaceQuery = useQuery({
    queryKey: ["mobile-workspace"],
    queryFn: mobileApi.getWorkspace,
    enabled: Boolean(user),
  });

  const featureAccessQuery = useQuery({
    queryKey: ["mobile-feature-access"],
    queryFn: mobileApi.getFeatureAccess,
    enabled: Boolean(user),
  });

  const enabledModules = useMemo(() => {
    if (!featureAccessQuery.data) {
      return [];
    }

    return featureAccessQuery.data
      .filter((item) => item.has_access && MODULES[item.feature_key])
      .map((item) => ({
        ...item,
        ...MODULES[item.feature_key],
      }));
  }, [featureAccessQuery.data]);

  if (!user) {
    return (
      <ScreenShell>
        <AccessGate
          title="Your workspace activates after sign-in"
          body="Guests can explore news and market intelligence. Sign in to unlock analytics, alerts, and the modules your admin has granted."
        />
      </ScreenShell>
    );
  }

  if (workspaceQuery.isLoading || featureAccessQuery.isLoading) {
    return (
      <ScreenShell>
        <StatePanel
          title="Loading your workspace"
          body="Bringing in portfolio signal, alert load, and team context."
          loading
        />
      </ScreenShell>
    );
  }

  if (workspaceQuery.isError || featureAccessQuery.isError || !workspaceQuery.data) {
    return (
      <ScreenShell>
        <StatePanel
          title="Workspace unavailable"
          body="The mobile workspace could not be loaded right now."
        />
      </ScreenShell>
    );
  }

  const data = workspaceQuery.data;

  return (
    <ScreenShell>
      <View style={styles.header}>
        <Text style={[styles.kicker, { color: colors.accent }]}>Workspace</Text>
        <Text style={[styles.title, { color: colors.text }]}>
          Your operational command layer.
        </Text>
        <Text style={[styles.body, { color: colors.textMuted }]}>
          Fast access to the modules you can actually use, with a compact morning brief at the top.
        </Text>
      </View>

      <Surface style={styles.briefPanel}>
        <Text style={[styles.briefTitle, { color: colors.text }]}>
          {data.user.full_name || data.user.email}
        </Text>
        <Text style={[styles.briefBody, { color: colors.textMuted }]}>
          {enabledModules.length} active modules. {data.notifications.unread_count} unread notifications.{" "}
          {data.teams_count} connected teams.
        </Text>
        <View style={styles.statGrid}>
          <View style={styles.statItem}>
            <Text style={[styles.statValue, { color: colors.text }]}>
              {formatCurrency(data.portfolios?.total_value_aed ?? 0)}
            </Text>
            <Text style={[styles.statLabel, { color: colors.textMuted }]}>portfolio value</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={[styles.statValue, { color: colors.text }]}>
              {formatPercent(data.portfolios?.total_return_percent ?? 0)}
            </Text>
            <Text style={[styles.statLabel, { color: colors.textMuted }]}>portfolio return</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={[styles.statValue, { color: colors.text }]}>
              {formatCompactNumber(data.alerts?.summary.active ?? 0)}
            </Text>
            <Text style={[styles.statLabel, { color: colors.textMuted }]}>active alerts</Text>
          </View>
        </View>
      </Surface>

      <View>
        <SectionHeader
          eyebrow="Modules"
          title="Your accessible surfaces"
          description="The mobile app respects the same access model as the main platform."
        />
        <View style={styles.moduleList}>
          {enabledModules.map((module) => (
            <ModuleCard
              key={module.feature_key}
              title={module.label}
              description={module.description}
              badge={module.category}
              icon={<Ionicons name={module.icon} size={18} color={colors.accent} />}
              onPress={() => router.push(module.route as never)}
            />
          ))}
        </View>
      </View>

      {data.portfolios ? (
        <View>
          <SectionHeader
            eyebrow="Investor suite"
            title="Portfolio snapshot"
            description="Compressed mobile readout of current capital, watchlists, and best ideas."
            actionLabel="Open portfolios"
            onActionPress={() => router.push("/portfolios")}
          />
          <View style={styles.grid}>
            <Surface style={styles.summaryCard}>
              <Text style={[styles.summaryLabel, { color: colors.textMuted }]}>Portfolios</Text>
              <Text style={[styles.summaryValue, { color: colors.text }]}>
                {data.portfolios.portfolio_count}
              </Text>
              <Text style={[styles.summarySubtext, { color: colors.textSoft }]}>
                {data.portfolios.watchlist_count} watchlists
              </Text>
            </Surface>
            <Surface style={styles.summaryCard}>
              <Text style={[styles.summaryLabel, { color: colors.textMuted }]}>Watch items</Text>
              <Text style={[styles.summaryValue, { color: colors.text }]}>
                {data.portfolios.watch_items}
              </Text>
              <Text style={[styles.summarySubtext, { color: colors.textSoft }]}>
                Across your current workspace
              </Text>
            </Surface>
          </View>
          <View style={styles.topHoldingList}>
            {data.portfolios.top_holdings.map((holding) => (
              <Surface key={holding.symbol} style={styles.holdingCard}>
                <Text style={[styles.holdingSymbol, { color: colors.text }]}>{holding.symbol}</Text>
                <Text style={[styles.holdingName, { color: colors.textMuted }]} numberOfLines={1}>
                  {holding.asset_name || "Tracked holding"}
                </Text>
                <Text style={[styles.holdingValue, { color: colors.text }]}>
                  {formatCurrency(holding.current_value)}
                </Text>
              </Surface>
            ))}
          </View>
        </View>
      ) : null}

      <View>
        <SectionHeader
          eyebrow="Signal queue"
          title="Notifications and competitor signal"
          description="The smallest set of information you should not miss while away from the full dashboard."
        />
        {data.competitor_spotlight ? (
          <Surface style={styles.competitorCard}>
            <Text style={[styles.competitorName, { color: colors.text }]}>
              {data.competitor_spotlight.name}
            </Text>
            <Text style={[styles.competitorMeta, { color: colors.textMuted }]}>
              {data.competitor_spotlight.ticker_symbol || "Private"} · threat level{" "}
              {data.competitor_spotlight.threat_level || "monitoring"}
            </Text>
            <Text style={[styles.competitorBody, { color: colors.textSoft }]}>
              {data.competitor_spotlight.strategic_note || "Tracked in the competitive intelligence layer."}
            </Text>
          </Surface>
        ) : null}
        <View style={styles.notificationList}>
          {data.notifications.latest.map((notification) => (
            <Surface key={notification.id} style={styles.notificationCard}>
              <Text style={[styles.notificationTitle, { color: colors.text }]}>
                {notification.title}
              </Text>
              <Text style={[styles.notificationBody, { color: colors.textMuted }]} numberOfLines={2}>
                {notification.message}
              </Text>
            </Surface>
          ))}
        </View>
        <PrimaryButton
          label="Open notifications"
          variant="secondary"
          onPress={() => router.push("/notifications")}
        />
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
  briefPanel: {
    gap: 16,
  },
  briefTitle: {
    fontSize: 24,
    fontWeight: "900",
  },
  briefBody: {
    fontSize: 14,
    lineHeight: 22,
  },
  statGrid: {
    flexDirection: "row",
    gap: 12,
  },
  statItem: {
    flex: 1,
    gap: 6,
  },
  statValue: {
    fontSize: 18,
    fontWeight: "800",
  },
  statLabel: {
    fontSize: 12,
    lineHeight: 18,
  },
  moduleList: {
    gap: 14,
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
  summarySubtext: {
    fontSize: 13,
    lineHeight: 19,
  },
  topHoldingList: {
    gap: 12,
    marginTop: 12,
  },
  holdingCard: {
    gap: 8,
  },
  holdingSymbol: {
    fontSize: 16,
    fontWeight: "800",
  },
  holdingName: {
    fontSize: 13,
  },
  holdingValue: {
    fontSize: 18,
    fontWeight: "800",
  },
  competitorCard: {
    gap: 10,
  },
  competitorName: {
    fontSize: 18,
    fontWeight: "800",
  },
  competitorMeta: {
    fontSize: 13,
    lineHeight: 20,
  },
  competitorBody: {
    fontSize: 14,
    lineHeight: 22,
  },
  notificationList: {
    gap: 12,
    marginBottom: 12,
  },
  notificationCard: {
    gap: 6,
  },
  notificationTitle: {
    fontSize: 15,
    fontWeight: "700",
  },
  notificationBody: {
    fontSize: 13,
    lineHeight: 20,
  },
});
