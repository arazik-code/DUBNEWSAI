import type { ReactNode } from "react";

import { LinearGradient } from "expo-linear-gradient";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { radii, useAppTheme } from "@/lib/theme";

type PrimaryButtonProps = {
  label: string;
  onPress: () => void;
  icon?: ReactNode;
  variant?: "primary" | "secondary" | "ghost";
  loading?: boolean;
  disabled?: boolean;
  fullWidth?: boolean;
};

export function PrimaryButton({
  label,
  onPress,
  icon,
  variant = "primary",
  loading = false,
  disabled = false,
  fullWidth = true,
}: PrimaryButtonProps) {
  const { colors, isDark } = useAppTheme();
  const blocked = loading || disabled;

  return (
    <Pressable
      disabled={blocked}
      onPress={onPress}
      style={({ pressed }) => [
        styles.pressable,
        fullWidth && styles.fullWidth,
        pressed && !blocked ? styles.pressed : null,
      ]}
    >
      {variant === "primary" ? (
        <LinearGradient
          colors={isDark ? ["#FFD36B", "#F5B83D"] : ["#D89C1D", "#B97B10"]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.primary}
        >
          {loading ? (
            <ActivityIndicator color="#0B1020" />
          ) : (
            <View style={styles.row}>
              {icon}
              <Text style={styles.primaryLabel}>{label}</Text>
            </View>
          )}
        </LinearGradient>
      ) : (
        <View
          style={[
            styles.secondary,
            {
              backgroundColor: variant === "ghost" ? "transparent" : colors.surfaceMuted,
              borderColor: colors.border,
            },
          ]}
        >
          {loading ? (
            <ActivityIndicator color={colors.text} />
          ) : (
            <View style={styles.row}>
              {icon}
              <Text style={[styles.secondaryLabel, { color: colors.text }]}>{label}</Text>
            </View>
          )}
        </View>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  pressable: {
    borderRadius: radii.pill,
  },
  fullWidth: {
    alignSelf: "stretch",
  },
  pressed: {
    opacity: 0.84,
  },
  primary: {
    minHeight: 54,
    borderRadius: radii.pill,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 20,
  },
  secondary: {
    minHeight: 54,
    borderRadius: radii.pill,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 20,
  },
  primaryLabel: {
    color: "#0B1020",
    fontSize: 15,
    fontWeight: "700",
  },
  secondaryLabel: {
    fontSize: 15,
    fontWeight: "700",
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
});
