import type { PropsWithChildren } from "react";

import { StyleSheet, View, type StyleProp, type ViewStyle } from "react-native";

import { radii, useAppTheme } from "@/lib/theme";

type SurfaceProps = PropsWithChildren<{
  style?: StyleProp<ViewStyle>;
}>;

export function Surface({ children, style }: SurfaceProps) {
  const { colors, isDark } = useAppTheme();

  return (
    <View
      style={[
        styles.surface,
        {
          backgroundColor: colors.surface,
          borderColor: colors.border,
          shadowColor: colors.shadow,
          shadowOpacity: isDark ? 0.24 : 0.08,
        },
        style,
      ]}
    >
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  surface: {
    borderWidth: 1,
    borderRadius: radii.xl,
    padding: 18,
    shadowOffset: { width: 0, height: 12 },
    shadowRadius: 28,
    elevation: 4,
  },
});
