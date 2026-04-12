import { useMemo, useState } from "react";

import { useMutation, useQuery } from "@tanstack/react-query";
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
import { formatCompactNumber, sentenceCase } from "@/lib/formatters";
import { queryClient } from "@/lib/providers/app-providers";
import { useAuthStore } from "@/lib/state/auth-store";
import { useAppTheme } from "@/lib/theme";

const ALERT_TYPES = ["price_above", "price_below", "keyword_match"];
const ALERT_FREQUENCIES = ["instant", "hourly", "daily"];

export default function AlertsScreen() {
  const { colors } = useAppTheme();
  const user = useAuthStore((state) => state.user);
  const [name, setName] = useState("");
  const [alertType, setAlertType] = useState("price_above");
  const [frequency, setFrequency] = useState("instant");
  const [symbol, setSymbol] = useState("");
  const [threshold, setThreshold] = useState("0");
  const [keywords, setKeywords] = useState("");

  const alertsQuery = useQuery({
    queryKey: ["mobile-alerts"],
    queryFn: mobileApi.getAlerts,
    enabled: Boolean(user),
  });

  const intelligenceQuery = useQuery({
    queryKey: ["mobile-alert-intelligence"],
    queryFn: mobileApi.getAlertIntelligence,
    enabled: Boolean(user),
  });

  const optionsQuery = useQuery({
    queryKey: ["mobile-alert-options"],
    queryFn: mobileApi.getPredictionOptions,
    enabled: Boolean(user),
  });

  const summary = intelligenceQuery.data?.summary ?? {};
  const quickSymbols = useMemo(() => (optionsQuery.data?.symbols ?? []).slice(0, 8), [optionsQuery.data]);

  const createAlertMutation = useMutation({
    mutationFn: () =>
      mobileApi.createAlert({
        name: name.trim(),
        alert_type: alertType,
        symbol: alertType === "keyword_match" ? null : symbol || undefined,
        threshold_value: alertType === "keyword_match" ? null : Number(threshold || "0"),
        keywords:
          alertType === "keyword_match"
            ? keywords
                .split(",")
                .map((entry) => entry.trim())
                .filter(Boolean)
            : null,
        frequency: frequency,
        email_enabled: false,
        notification_enabled: true,
      }),
    onSuccess: async () => {
      setName("");
      setThreshold("0");
      setKeywords("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["mobile-alerts"] }),
        queryClient.invalidateQueries({ queryKey: ["mobile-alert-intelligence"] }),
      ]);
    },
  });

  const toggleAlertMutation = useMutation({
    mutationFn: (alertId: number) => mobileApi.toggleAlert(alertId),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["mobile-alerts"] }),
        queryClient.invalidateQueries({ queryKey: ["mobile-alert-intelligence"] }),
      ]);
    },
  });

  if (!user) {
    return (
      <ScreenShell>
        <AccessGate
          title="Alerts require sign-in"
          body="Create signal rules and review alert intelligence after authentication."
        />
      </ScreenShell>
    );
  }

  if (alertsQuery.isLoading || intelligenceQuery.isLoading || optionsQuery.isLoading) {
    return (
      <ScreenShell>
        <StatePanel title="Loading alerts" body="Syncing rules, triggers, and mobile templates." loading />
      </ScreenShell>
    );
  }

  if (alertsQuery.isError || intelligenceQuery.isError || optionsQuery.isError) {
    return (
      <ScreenShell>
        <StatePanel title="Alerts unavailable" body="The alerts module could not be loaded right now." />
      </ScreenShell>
    );
  }

  return (
    <ScreenShell>
      <View style={styles.header}>
        <Text style={[styles.kicker, { color: colors.accent }]}>Alerts</Text>
        <Text style={[styles.title, { color: colors.text }]}>Signal rules that work from your phone.</Text>
        <Text style={[styles.body, { color: colors.textMuted }]}>
          Build price or keyword alerts, monitor active rules, and keep the queue under control while moving.
        </Text>
      </View>

      <View style={styles.grid}>
        <Surface style={styles.summaryCard}>
          <Text style={[styles.summaryLabel, { color: colors.textMuted }]}>Active</Text>
          <Text style={[styles.summaryValue, { color: colors.text }]}>
            {formatCompactNumber(Number(summary.active ?? 0))}
          </Text>
        </Surface>
        <Surface style={styles.summaryCard}>
          <Text style={[styles.summaryLabel, { color: colors.textMuted }]}>Triggered</Text>
          <Text style={[styles.summaryValue, { color: colors.text }]}>
            {formatCompactNumber(Number(summary.triggered ?? 0))}
          </Text>
        </Surface>
      </View>

      <Surface style={styles.formCard}>
        <Text style={[styles.formTitle, { color: colors.text }]}>Create alert</Text>
        <TextField label="Alert name" value={name} onChangeText={setName} />
        <View style={styles.chipWrap}>
          {ALERT_TYPES.map((type) => (
            <ChoiceChip
              key={type}
              label={sentenceCase(type)}
              selected={alertType === type}
              onPress={() => setAlertType(type)}
            />
          ))}
        </View>
        <View style={styles.chipWrap}>
          {ALERT_FREQUENCIES.map((value) => (
            <ChoiceChip
              key={value}
              label={sentenceCase(value)}
              selected={frequency === value}
              onPress={() => setFrequency(value)}
            />
          ))}
        </View>
        {alertType === "keyword_match" ? (
          <TextField
            label="Keywords"
            value={keywords}
            onChangeText={setKeywords}
            placeholder="mortgage, waterfront, developer..."
            hint="Separate multiple keywords with commas."
          />
        ) : (
          <>
            <View style={styles.chipWrap}>
              {quickSymbols.map((item) => (
                <ChoiceChip
                  key={item.canonical_symbol}
                  label={item.symbol}
                  selected={symbol === item.symbol}
                  onPress={() => setSymbol(item.symbol)}
                />
              ))}
            </View>
            <TextField label="Symbol" value={symbol} onChangeText={setSymbol} autoCapitalize="characters" />
            <TextField label="Threshold value" value={threshold} onChangeText={setThreshold} keyboardType="numeric" />
          </>
        )}
        {createAlertMutation.error ? (
          <Text style={[styles.errorText, { color: colors.danger }]}>{createAlertMutation.error.message}</Text>
        ) : null}
        <PrimaryButton
          label={createAlertMutation.isPending ? "Creating alert..." : "Create alert"}
          onPress={() => createAlertMutation.mutate()}
          loading={createAlertMutation.isPending}
        />
      </Surface>

      <View>
        <SectionHeader
          eyebrow="Rules"
          title="Current alert stack"
          description="Review status, trigger count, and pause or resume without leaving the screen."
        />
        <View style={styles.list}>
          {(alertsQuery.data ?? []).map((alert) => (
            <Surface key={alert.id} style={styles.alertCard}>
              <Text style={[styles.alertTitle, { color: colors.text }]}>{alert.name}</Text>
              <Text style={[styles.alertMeta, { color: colors.textMuted }]}>
                {sentenceCase(alert.alert_type)} · {sentenceCase(alert.status)} · {alert.trigger_count} triggers
              </Text>
              <PrimaryButton
                label={alert.is_active ? "Pause / resume" : "Reactivate"}
                variant="secondary"
                onPress={() => toggleAlertMutation.mutate(alert.id)}
                loading={toggleAlertMutation.isPending}
              />
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
  alertCard: {
    gap: 10,
  },
  alertTitle: {
    fontSize: 17,
    fontWeight: "800",
  },
  alertMeta: {
    fontSize: 13,
    lineHeight: 20,
  },
});
