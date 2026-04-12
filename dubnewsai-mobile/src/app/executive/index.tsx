import { useQuery } from "@tanstack/react-query";
import { StyleSheet, Text, View } from "react-native";

import { AccessGate } from "@/components/access-gate";
import { ScreenShell } from "@/components/screen-shell";
import { SectionHeader } from "@/components/section-header";
import { StatePanel } from "@/components/state-panel";
import { Surface } from "@/components/surface";
import { mobileApi } from "@/lib/api/queries";
import { sentenceCase } from "@/lib/formatters";
import { useAuthStore } from "@/lib/state/auth-store";
import { useAppTheme } from "@/lib/theme";

export default function ExecutiveScreen() {
  const { colors } = useAppTheme();
  const user = useAuthStore((state) => state.user);

  const featureAccessQuery = useQuery({
    queryKey: ["mobile-feature-access-executive"],
    queryFn: mobileApi.getFeatureAccess,
    enabled: Boolean(user),
  });

  const hasAccess =
    featureAccessQuery.data?.find((item) => item.feature_key === "executive")?.has_access ??
    false;

  const dashboardQuery = useQuery({
    queryKey: ["mobile-executive-dashboard"],
    queryFn: mobileApi.getExecutiveDashboard,
    enabled: Boolean(user && hasAccess),
  });

  if (!user) {
    return (
      <ScreenShell>
        <AccessGate
          title="Executive view requires sign-in"
          body="Executive dashboards open only after authentication and admin access."
        />
      </ScreenShell>
    );
  }

  if (featureAccessQuery.isLoading) {
    return (
      <ScreenShell>
        <StatePanel title="Loading access" body="Checking executive permissions." loading />
      </ScreenShell>
    );
  }

  if (featureAccessQuery.isError) {
    return (
      <ScreenShell>
        <StatePanel title="Access check unavailable" body="Executive permissions could not be verified right now." />
      </ScreenShell>
    );
  }

  if (!hasAccess) {
    return (
      <ScreenShell>
        <AccessGate
          title="Executive is admin-granted"
          body="Your admin needs to grant executive access before this surface can open."
        />
      </ScreenShell>
    );
  }

  if (dashboardQuery.isLoading) {
    return (
      <ScreenShell>
        <StatePanel title="Loading executive dashboard" body="Building a strategic mobile brief." loading />
      </ScreenShell>
    );
  }

  if (dashboardQuery.isError || !dashboardQuery.data) {
    return (
      <ScreenShell>
        <StatePanel title="Executive dashboard unavailable" body="This view could not be loaded right now." />
      </ScreenShell>
    );
  }

  const dashboard = dashboardQuery.data;
  const healthScore = Number((dashboard.kpis as Record<string, unknown>).market_health_score ?? 0);
  const priorities = dashboard.strategic_priorities.slice(0, 3);
  const risks =
    ((dashboard.risk_dashboard as Record<string, unknown>).top_risks as Record<string, unknown>[] | undefined) ??
    [];

  return (
    <ScreenShell>
      <View style={styles.header}>
        <Text style={[styles.kicker, { color: colors.accent }]}>Executive</Text>
        <Text style={[styles.title, { color: colors.text }]}>Leadership brief in a mobile format.</Text>
        <Text style={[styles.body, { color: colors.textMuted }]}>
          Strategic priorities, risk signal, and key points compressed into one scan-friendly layer.
        </Text>
      </View>

      <View style={styles.grid}>
        <Surface style={styles.summaryCard}>
          <Text style={[styles.summaryLabel, { color: colors.textMuted }]}>Sentiment</Text>
          <Text style={[styles.summaryValue, { color: colors.text }]}>
            {dashboard.summary.overall_sentiment}
          </Text>
        </Surface>
        <Surface style={styles.summaryCard}>
          <Text style={[styles.summaryLabel, { color: colors.textMuted }]}>Market health</Text>
          <Text style={[styles.summaryValue, { color: colors.text }]}>{healthScore}</Text>
        </Surface>
      </View>

      <View>
        <SectionHeader
          eyebrow="Summary"
          title="Key points"
          description="The most important executive observations from the current reporting window."
        />
        <View style={styles.list}>
          {dashboard.summary.key_points.map((point) => (
            <Surface key={point.message} style={styles.card}>
              <Text style={[styles.cardTitle, { color: colors.text }]}>{point.category}</Text>
              <Text style={[styles.cardMeta, { color: colors.textMuted }]}>
                {sentenceCase(point.status)}
              </Text>
              <Text style={[styles.cardBody, { color: colors.textSoft }]}>{point.message}</Text>
            </Surface>
          ))}
        </View>
      </View>

      <View>
        <SectionHeader
          eyebrow="Priorities"
          title="Top strategic moves"
          description="Priority-ranked execution items for the next cycle."
        />
        <View style={styles.list}>
          {priorities.map((priority) => {
            const record = priority as Record<string, unknown>;
            return (
              <Surface key={String(record.title)} style={styles.card}>
                <Text style={[styles.cardTitle, { color: colors.text }]}>{String(record.title)}</Text>
                <Text style={[styles.cardMeta, { color: colors.textMuted }]}>
                  {String(record.owner)} · {String(record.timeframe)}
                </Text>
                <Text style={[styles.cardBody, { color: colors.textSoft }]}>
                  {String(record.rationale)}
                </Text>
              </Surface>
            );
          })}
        </View>
      </View>

      <View>
        <SectionHeader
          eyebrow="Risk"
          title="Top risks in view"
          description="A tight risk stack for quick leadership scanning."
        />
        <View style={styles.list}>
          {risks.map((risk) => (
            <Surface key={String(risk.description)} style={styles.card}>
              <Text style={[styles.cardTitle, { color: colors.text }]}>{String(risk.category)}</Text>
              <Text style={[styles.cardMeta, { color: colors.textMuted }]}>
                {String(risk.severity)} severity · {String(risk.probability)} probability
              </Text>
              <Text style={[styles.cardBody, { color: colors.textSoft }]}>
                {String(risk.description)}
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
    letterSpacing: 1.1,
  },
  summaryValue: {
    fontSize: 24,
    fontWeight: "900",
  },
  list: {
    gap: 12,
  },
  card: {
    gap: 8,
  },
  cardTitle: {
    fontSize: 17,
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
