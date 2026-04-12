import { useEffect } from "react";

import * as SplashScreen from "expo-splash-screen";
import { Stack } from "expo-router";
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { hydrateSession } from "@/lib/auth/actions";
import { appConfig } from "@/lib/config";
import { AppProviders } from "@/lib/providers/app-providers";
import { useAuthStore } from "@/lib/state/auth-store";
import { useAppTheme } from "@/lib/theme";

SplashScreen.preventAutoHideAsync().catch(() => undefined);

function BootBoundary() {
  const isHydrated = useAuthStore((state) => state.isHydrated);
  const { colors } = useAppTheme();

  useEffect(() => {
    hydrateSession().finally(() => {
      SplashScreen.hideAsync().catch(() => undefined);
    });
  }, []);

  if (!isHydrated) {
    return (
      <View style={[styles.loader, { backgroundColor: colors.background }]}>
        <ActivityIndicator color={colors.accent} size="large" />
        <Text style={[styles.loaderTitle, { color: colors.text }]}>{appConfig.appName}</Text>
        <Text style={[styles.loaderBody, { color: colors.textMuted }]}>
          Syncing the mobile command center.
        </Text>
      </View>
    );
  }

  return (
    <Stack
      screenOptions={{
        headerShown: false,
        animation: "fade",
        contentStyle: {
          backgroundColor: "transparent",
        },
      }}
    />
  );
}

export default function RootLayout() {
  return (
    <GestureHandlerRootView style={styles.root}>
      <SafeAreaProvider>
        <AppProviders>
          <BootBoundary />
        </AppProviders>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
  loader: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    paddingHorizontal: 32,
  },
  loaderTitle: {
    fontSize: 22,
    fontWeight: "800",
    letterSpacing: 0.2,
  },
  loaderBody: {
    fontSize: 14,
    lineHeight: 21,
    textAlign: "center",
  },
});
