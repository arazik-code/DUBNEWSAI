import type { PropsWithChildren, ReactNode } from "react";

import { LinearGradient } from "expo-linear-gradient";
import { StatusBar } from "expo-status-bar";
import { SafeAreaView } from "react-native-safe-area-context";
import { ScrollView, StyleSheet, View, type StyleProp, type ViewStyle } from "react-native";

import { spacing, useAppTheme } from "@/lib/theme";

type ScreenShellProps = PropsWithChildren<{
  scroll?: boolean;
  header?: ReactNode;
  contentStyle?: StyleProp<ViewStyle>;
}>;

export function ScreenShell({
  children,
  scroll = true,
  header,
  contentStyle,
}: ScreenShellProps) {
  const { colors, isDark, statusBarStyle } = useAppTheme();
  const Container = scroll ? ScrollView : View;

  return (
    <View style={[styles.root, { backgroundColor: colors.background }]}>
      <StatusBar style={statusBarStyle} />
      <LinearGradient
        colors={
          isDark
            ? ["#050816", "#0B1020", "#071322"]
            : ["#F8FAFC", "#EEF2FF", "#F6F7FB"]
        }
        style={StyleSheet.absoluteFill}
      />
      <View style={[styles.glow, styles.glowPrimary, { backgroundColor: colors.accentSoft }]} />
      <View style={[styles.glow, styles.glowSecondary, { backgroundColor: "rgba(66, 212, 255, 0.12)" }]} />
      <SafeAreaView style={styles.safeArea}>
        {header}
        <Container
          contentContainerStyle={[
            styles.content,
            scroll ? null : styles.flexContent,
            contentStyle,
          ]}
          showsVerticalScrollIndicator={false}
        >
          {children}
        </Container>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  content: {
    paddingHorizontal: spacing.page,
    paddingBottom: 140,
    gap: spacing.section,
  },
  flexContent: {
    flexGrow: 1,
    paddingTop: spacing.page,
  },
  glow: {
    position: "absolute",
    borderRadius: 999,
    opacity: 1,
  },
  glowPrimary: {
    width: 220,
    height: 220,
    top: 60,
    right: -60,
  },
  glowSecondary: {
    width: 280,
    height: 280,
    bottom: 180,
    left: -80,
  },
});
