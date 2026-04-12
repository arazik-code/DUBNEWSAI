import { useMutation, useQuery } from "@tanstack/react-query";
import { StyleSheet, Text, View } from "react-native";

import { AccessGate } from "@/components/access-gate";
import { PrimaryButton } from "@/components/primary-button";
import { ScreenShell } from "@/components/screen-shell";
import { StatePanel } from "@/components/state-panel";
import { Surface } from "@/components/surface";
import { mobileApi } from "@/lib/api/queries";
import { formatDateLabel, sentenceCase } from "@/lib/formatters";
import { queryClient } from "@/lib/providers/app-providers";
import { useAuthStore } from "@/lib/state/auth-store";
import { useAppTheme } from "@/lib/theme";

export default function NotificationsScreen() {
  const { colors } = useAppTheme();
  const user = useAuthStore((state) => state.user);

  const notificationsQuery = useQuery({
    queryKey: ["mobile-notifications"],
    queryFn: mobileApi.getNotifications,
    enabled: Boolean(user),
  });

  const markReadMutation = useMutation({
    mutationFn: (notificationId: number) => mobileApi.markNotificationRead(notificationId),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["mobile-notifications"] }),
        queryClient.invalidateQueries({ queryKey: ["mobile-workspace"] }),
        queryClient.invalidateQueries({ queryKey: ["mobile-bootstrap"] }),
      ]);
    },
  });

  if (!user) {
    return (
      <ScreenShell>
        <AccessGate
          title="Notifications require sign-in"
          body="Your workspace notification queue appears after authentication."
        />
      </ScreenShell>
    );
  }

  if (notificationsQuery.isLoading) {
    return (
      <ScreenShell>
        <StatePanel title="Loading notifications" body="Pulling your latest workspace events." loading />
      </ScreenShell>
    );
  }

  if (notificationsQuery.isError) {
    return (
      <ScreenShell>
        <StatePanel title="Notifications unavailable" body="The notification queue could not be loaded right now." />
      </ScreenShell>
    );
  }

  return (
    <ScreenShell>
      <View style={styles.header}>
        <Text style={[styles.kicker, { color: colors.accent }]}>Notifications</Text>
        <Text style={[styles.title, { color: colors.text }]}>Your mobile notification queue.</Text>
        <Text style={[styles.body, { color: colors.textMuted }]}>
          Mark items read as you clear the signal load throughout the day.
        </Text>
      </View>

      <View style={styles.list}>
        {(notificationsQuery.data ?? []).map((notification) => (
          <Surface key={notification.id} style={styles.card}>
            <Text style={[styles.cardTitle, { color: colors.text }]}>{notification.title}</Text>
            <Text style={[styles.cardMeta, { color: colors.textMuted }]}>
              {sentenceCase(notification.priority)} · {formatDateLabel(notification.created_at)}
            </Text>
            <Text style={[styles.cardBody, { color: colors.textSoft }]}>{notification.message}</Text>
            {!notification.is_read ? (
              <PrimaryButton
                label="Mark as read"
                variant="secondary"
                onPress={() => markReadMutation.mutate(notification.id)}
                loading={markReadMutation.isPending}
              />
            ) : null}
          </Surface>
        ))}
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
