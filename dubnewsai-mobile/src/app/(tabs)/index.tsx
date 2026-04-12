import { Ionicons } from "@expo/vector-icons";
import { useQuery } from "@tanstack/react-query";
import { router } from "expo-router";
import { ScrollView, StyleSheet, Text, View } from "react-native";

import { ArticleCard } from "@/components/article-card";
import { ModuleCard } from "@/components/module-card";
import { PrimaryButton } from "@/components/primary-button";
import { ScreenShell } from "@/components/screen-shell";
import { SectionHeader } from "@/components/section-header";
import { StatePanel } from "@/components/state-panel";
import { Surface } from "@/components/surface";
import { formatCompactNumber, formatCurrency, sentenceCase } from "@/lib/formatters";
import { mobileApi } from "@/lib/api/queries";
import { useAuthStore } from "@/lib/state/auth-store";
import { useAppTheme } from "@/lib/theme";

export default function HomeScreen() {
  const { colors } = useAppTheme();
  const user = useAuthStore((state) => state.user);
  const bootstrap = useQuery({
    queryKey: ["mobile-bootstrap", user?.id ?? "guest"],
    queryFn: mobileApi.getBootstrap,
  });

  if (bootstrap.isLoading) {
    return (
      <ScreenShell>
        <StatePanel title="Loading your brief" body="Pulling market pulse, feature access, and the latest Dubai news." loading />
      </ScreenShell>
    );
  }

  if (bootstrap.isError || !bootstrap.data) {
    return (
      <ScreenShell>
        <StatePanel title="Home feed unavailable" body="The mobile command surface could not be loaded right now." />
      </ScreenShell>
    );
  }

  const data = bootstrap.data;
  const accessible = data.feature_access.filter((item) => item.has_access).slice(0, 6);
  const unreadCount = data.workspace_summary?.notifications.unread_count ?? 0;
  const topTrend = data.market_pulse.trend_prediction;

  return (
    <ScreenShell>
      <View style={styles.hero}>
        <Text style={[styles.kicker, { color: colors.accent }]}>Mobile command center</Text>
        <Text style={[styles.heroTitle, { color: colors.text }]}>DUBNEWSAI in your pocket.</Text>
        <Text style={[styles.heroBody, { color: colors.textMuted }]}>
          News intelligence, market pulse, property valuation, and enterprise signal in one native workspace.
        </Text>

        <Surface style={styles.heroPanel}>
          <View style={styles.heroTop}>
            <View style={styles.heroStat}>
              <Text style={[styles.heroValue, { color: colors.text }]}>
                {data.feature_access.filter((item) => item.has_access).length}
              </Text>
              <Text style={[styles.heroLabel, { color: colors.textMuted }]}>enabled surfaces</Text>
            </View>
            <View style={styles.heroStat}>
              <Text style={[styles.heroValue, { color: colors.text }]}>
                {formatCompactNumber(data.trending_articles.length)}
              </Text>
              <Text style={[styles.heroLabel, { color: colors.textMuted }]}>trending stories</Text>
            </View>
            <View style={styles.heroStat}>
              <Text style={[styles.heroValue, { color: colors.text }]}>
                {topTrend?.prediction ? sentenceCase(String(topTrend.prediction)) : "Live"}
              </Text>
              <Text style={[styles.heroLabel, { color: colors.textMuted }]}>market signal</Text>
            </View>
          </View>
          <View style={styles.heroActions}>
            <PrimaryButton
              label={user ? "Open workspace" : "Sign in for more"}
              onPress={() => router.push(user ? "/workspace" : "/login")}
            />
            {unreadCount > 0 ? (
              <PrimaryButton
                label={`${unreadCount} unread alerts`}
                variant="secondary"
                onPress={() => router.push("/notifications")}
              />
            ) : null}
          </View>
        </Surface>
      </View>

      {data.hero_article ? (
        <View>
          <SectionHeader
            eyebrow="Lead story"
            title="The story shaping the day"
            description="One clean briefing card before you go deeper into the feed."
          />
          <ArticleCard
            article={data.hero_article}
            featured
            onPress={() => {
              if (data.hero_article) {
                router.push(`/news/${data.hero_article.id}`);
              }
            }}
          />
        </View>
      ) : null}

      <View>
        <SectionHeader
          eyebrow="Access"
          title="What you can use right now"
          description="The mobile app adapts to your workspace grants automatically."
        />
        <View style={styles.featureWrap}>
          {accessible.map((feature) => (
            <View key={feature.feature_key} style={[styles.featureChip, { backgroundColor: colors.surfaceMuted, borderColor: colors.border }]}>
              <Text style={[styles.featureChipText, { color: colors.textSoft }]}>{feature.label}</Text>
            </View>
          ))}
        </View>
      </View>

      <View>
        <SectionHeader
          eyebrow="Market pulse"
          title="Live movers and real-estate leaders"
          description="Fast signal on the names most likely to matter before you open the detail views."
          actionLabel="Open market"
          onActionPress={() => router.push("/market")}
        />
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.horizontalRail}>
          {data.market_pulse.movers.map((item) => (
            <ModuleCard
              key={item.symbol}
              title={item.symbol}
              description={`${item.name}\n${formatCurrency(item.price, item.currency)}`}
              badge={`${item.change_percent >= 0 ? "+" : ""}${item.change_percent.toFixed(2)}%`}
              icon={<Ionicons name="trending-up" size={18} color={colors.accent} />}
              onPress={() => router.push(`/market/${encodeURIComponent(item.symbol)}`)}
            />
          ))}
        </ScrollView>
      </View>

      {data.workspace_summary ? (
        <View>
          <SectionHeader
            eyebrow="Workspace"
            title={`Morning brief for ${data.workspace_summary.user.full_name || "your workspace"}`}
            description="A compressed view of the areas that need attention before you go into the full modules."
            actionLabel="Open workspace"
            onActionPress={() => router.push("/workspace")}
          />
          <View style={styles.workspaceGrid}>
            <Surface style={styles.summaryCard}>
              <Text style={[styles.summaryLabel, { color: colors.textMuted }]}>Portfolio value</Text>
              <Text style={[styles.summaryValue, { color: colors.text }]}>
                {formatCurrency(data.workspace_summary.portfolios?.total_value_aed || 0)}
              </Text>
              <Text style={[styles.summarySubtext, { color: colors.textSoft }]}>
                {data.workspace_summary.portfolios?.portfolio_count || 0} portfolios
              </Text>
            </Surface>
            <Surface style={styles.summaryCard}>
              <Text style={[styles.summaryLabel, { color: colors.textMuted }]}>Unread notifications</Text>
              <Text style={[styles.summaryValue, { color: colors.text }]}>
                {formatCompactNumber(data.workspace_summary.notifications.unread_count)}
              </Text>
              <Text style={[styles.summarySubtext, { color: colors.textSoft }]}>
                {data.workspace_summary.teams_count} teams connected
              </Text>
            </Surface>
          </View>
        </View>
      ) : (
        <Surface>
          <Text style={[styles.authTitle, { color: colors.text }]}>Unlock the full workspace after sign-in</Text>
          <Text style={[styles.authBody, { color: colors.textMuted }]}>
            Guests can explore news and market intelligence. Sign in to unlock analytics, alerts, settings, and admin-granted enterprise surfaces.
          </Text>
          <PrimaryButton label="Sign in" onPress={() => router.push("/login")} />
        </Surface>
      )}

      <View>
        <SectionHeader
          eyebrow="Now trending"
          title="Continue reading"
          description="A tighter editorial feed designed for quick mobile scanning."
          actionLabel="All news"
          onActionPress={() => router.push("/news")}
        />
        <View style={styles.articleList}>
          {data.trending_articles.map((article) => (
            <ArticleCard
              key={article.id}
              article={article}
              onPress={() => router.push(`/news/${article.id}`)}
            />
          ))}
        </View>
      </View>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  hero: {
    gap: 12,
    paddingTop: 12,
  },
  kicker: {
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1.8,
    textTransform: "uppercase",
  },
  heroTitle: {
    fontSize: 38,
    lineHeight: 42,
    fontWeight: "900",
    letterSpacing: -1.2,
  },
  heroBody: {
    fontSize: 15,
    lineHeight: 24,
    maxWidth: 320,
  },
  heroPanel: {
    gap: 18,
  },
  heroTop: {
    flexDirection: "row",
    gap: 12,
  },
  heroStat: {
    flex: 1,
    gap: 6,
  },
  heroValue: {
    fontSize: 20,
    fontWeight: "800",
  },
  heroLabel: {
    fontSize: 12,
    lineHeight: 18,
  },
  heroActions: {
    gap: 10,
  },
  featureWrap: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  featureChip: {
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 999,
  },
  featureChipText: {
    fontSize: 13,
    fontWeight: "700",
  },
  horizontalRail: {
    gap: 14,
    paddingRight: 20,
  },
  workspaceGrid: {
    flexDirection: "row",
    gap: 14,
  },
  summaryCard: {
    flex: 1,
    gap: 8,
  },
  summaryLabel: {
    fontSize: 12,
    textTransform: "uppercase",
    letterSpacing: 1.2,
    fontWeight: "700",
  },
  summaryValue: {
    fontSize: 24,
    fontWeight: "900",
  },
  summarySubtext: {
    fontSize: 13,
  },
  authTitle: {
    fontSize: 20,
    fontWeight: "800",
    marginBottom: 8,
  },
  authBody: {
    fontSize: 14,
    lineHeight: 22,
    marginBottom: 16,
  },
  articleList: {
    gap: 14,
  },
});
