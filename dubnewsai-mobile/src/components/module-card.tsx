import type { ReactNode } from "react";

import { Pressable, StyleSheet, Text, View } from "react-native";

import { Surface } from "./surface";

import { useAppTheme } from "@/lib/theme";

type ModuleCardProps = {
  title: string;
  description: string;
  badge?: string;
  icon?: ReactNode;
  onPress?: () => void;
};

export function ModuleCard({ title, description, badge, icon, onPress }: ModuleCardProps) {
  const { colors } = useAppTheme();

  return (
    <Pressable onPress={onPress} disabled={!onPress}>
      <Surface style={styles.surface}>
        <View style={styles.container}>
          <View style={styles.topRow}>
            <View style={[styles.iconWrap, { backgroundColor: colors.surfaceMuted }]}>{icon}</View>
            {badge ? (
              <View style={[styles.badge, { backgroundColor: colors.accentSoft }]}>
                <Text style={[styles.badgeText, { color: colors.accent }]}>{badge}</Text>
              </View>
            ) : null}
          </View>
          <Text style={[styles.title, { color: colors.text }]}>{title}</Text>
          <Text style={[styles.description, { color: colors.textMuted }]}>{description}</Text>
        </View>
      </Surface>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  surface: {
    minHeight: 164,
  },
  container: {
    flex: 1,
    gap: 14,
  },
  topRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  iconWrap: {
    width: 42,
    height: 42,
    borderRadius: 999,
    alignItems: "center",
    justifyContent: "center",
  },
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  title: {
    fontSize: 17,
    fontWeight: "800",
  },
  description: {
    fontSize: 14,
    lineHeight: 20,
  },
});
