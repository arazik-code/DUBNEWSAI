import { useMemo } from "react";

import { Ionicons } from "@expo/vector-icons";
import { useMutation, useQuery } from "@tanstack/react-query";
import { router } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { PrimaryButton } from "@/components/primary-button";
import { ScreenShell } from "@/components/screen-shell";
import { SectionHeader } from "@/components/section-header";
import { StatePanel } from "@/components/state-panel";
import { Surface } from "@/components/surface";
import { logout } from "@/lib/auth/actions";
import { mobileApi } from "@/lib/api/queries";
import { appConfig } from "@/lib/config";
import { queryClient } from "@/lib/providers/app-providers";
import { useAuthStore } from "@/lib/state/auth-store";
import { useAppTheme } from "@/lib/theme";

export default function ProfileScreen() {
  const { colors } = useAppTheme();
  const user = useAuthStore((state) => state.user);

  const featureAccessQuery = useQuery({
    queryKey: ["mobile-profile-feature-access"],
    queryFn: mobileApi.getFeatureAccess,
    enabled: Boolean(user),
  });

  const logoutMutation = useMutation({
    mutationFn: async () => {
      await logout();
      await queryClient.clear();
    },
    onSuccess: () => {
      router.replace("/");
    },
  });

  const accessibleLabels = useMemo(() => {
    return (featureAccessQuery.data ?? [])
      .filter((item) => item.has_access)
      .map((item) => item.label);
  }, [featureAccessQuery.data]);

  if (!user) {
    return (
      <ScreenShell>
        <View style={styles.header}>
          <Text style={[styles.kicker, { color: colors.accent }]}>Profile</Text>
          <Text style={[styles.title, { color: colors.text }]}>
            A clean mobile gateway into DUBNEWSAI.
          </Text>
          <Text style={[styles.body, { color: colors.textMuted }]}>
            Sign in to unlock analytics, alerts, settings, and any enterprise modules your admin grants.
          </Text>
        </View>

        <Surface style={styles.guestPanel}>
          <Text style={[styles.guestTitle, { color: colors.text }]}>
            You are browsing as a guest
          </Text>
          <Text style={[styles.guestBody, { color: colors.textMuted }]}>
            News and Market stay available without authentication. Everything else lights up after sign-in.
          </Text>
          <PrimaryButton label="Sign in" onPress={() => router.push("/login")} />
          <PrimaryButton
            label="Create account"
            variant="secondary"
            onPress={() => router.push("/register")}
          />
        </Surface>

        <Surface style={styles.infoCard}>
          <Text style={[styles.infoTitle, { color: colors.text }]}>App configuration</Text>
          <Text style={[styles.infoBody, { color: colors.textMuted }]}>
            {appConfig.appName} mobile is pointed at {appConfig.apiUrl}
          </Text>
        </Surface>
      </ScreenShell>
    );
  }

  if (featureAccessQuery.isLoading) {
    return (
      <ScreenShell>
        <StatePanel
          title="Loading profile"
          body="Syncing feature access and account context."
          loading
        />
      </ScreenShell>
    );
  }

  return (
    <ScreenShell>
      <View style={styles.header}>
        <Text style={[styles.kicker, { color: colors.accent }]}>Profile</Text>
        <Text style={[styles.title, { color: colors.text }]}>
          {user.full_name || "Your DUBNEWSAI account"}
        </Text>
        <Text style={[styles.body, { color: colors.textMuted }]}>
          Keep session state, module access, and app identity visible without digging through nested settings.
        </Text>
      </View>

      <Surface style={styles.accountCard}>
        <View style={styles.accountRow}>
          <View style={styles.accountBadge}>
            <Ionicons name="person-circle" size={34} color={colors.accent} />
          </View>
          <View style={styles.accountCopy}>
            <Text style={[styles.accountName, { color: colors.text }]}>
              {user.full_name || user.email}
            </Text>
            <Text style={[styles.accountMeta, { color: colors.textMuted }]}>{user.email}</Text>
            <Text style={[styles.accountMeta, { color: colors.textMuted }]}>Role: {user.role}</Text>
          </View>
        </View>
        <PrimaryButton
          label={logoutMutation.isPending ? "Signing out..." : "Sign out"}
          variant="secondary"
          loading={logoutMutation.isPending}
          onPress={() => logoutMutation.mutate()}
        />
      </Surface>

      <View>
        <SectionHeader
          eyebrow="Access"
          title="Features available on this account"
          description="The mobile app mirrors the same permissions model as the web platform."
        />
        <View style={styles.featureWrap}>
          {accessibleLabels.map((label) => (
            <View
              key={label}
              style={[
                styles.featureChip,
                { backgroundColor: colors.surfaceMuted, borderColor: colors.border },
              ]}
            >
              <Text style={[styles.featureChipText, { color: colors.textSoft }]}>{label}</Text>
            </View>
          ))}
        </View>
      </View>

      <View>
        <SectionHeader
          eyebrow="Quick paths"
          title="Open the surfaces you use most"
          description="A compact set of high-value actions so profile never feels like dead space."
        />
        <View style={styles.quickList}>
          <PrimaryButton label="Open workspace" onPress={() => router.push("/workspace")} />
          <PrimaryButton
            label="Open alerts"
            variant="secondary"
            onPress={() => router.push("/alerts")}
          />
          <PrimaryButton
            label="Open portfolios"
            variant="secondary"
            onPress={() => router.push("/portfolios")}
          />
        </View>
      </View>

      <Surface style={styles.infoCard}>
        <Text style={[styles.infoTitle, { color: colors.text }]}>App identity</Text>
        <Text style={[styles.infoBody, { color: colors.textMuted }]}>
          {appConfig.appName} v{appConfig.appVersion}
        </Text>
        <Text style={[styles.infoBody, { color: colors.textMuted }]}>
          Backend: {appConfig.apiUrl}
        </Text>
      </Surface>
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
  guestPanel: {
    gap: 14,
  },
  guestTitle: {
    fontSize: 22,
    fontWeight: "800",
  },
  guestBody: {
    fontSize: 14,
    lineHeight: 22,
  },
  accountCard: {
    gap: 16,
  },
  accountRow: {
    flexDirection: "row",
    gap: 14,
    alignItems: "center",
  },
  accountBadge: {
    width: 54,
    height: 54,
    borderRadius: 999,
    alignItems: "center",
    justifyContent: "center",
  },
  accountCopy: {
    flex: 1,
    gap: 4,
  },
  accountName: {
    fontSize: 20,
    fontWeight: "800",
  },
  accountMeta: {
    fontSize: 13,
    lineHeight: 19,
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
  quickList: {
    gap: 12,
  },
  infoCard: {
    gap: 10,
  },
  infoTitle: {
    fontSize: 17,
    fontWeight: "800",
  },
  infoBody: {
    fontSize: 14,
    lineHeight: 21,
  },
});
