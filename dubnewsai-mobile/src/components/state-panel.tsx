import { ActivityIndicator, StyleSheet, Text, View } from "react-native";

import { Surface } from "./surface";

import { useAppTheme } from "@/lib/theme";

type StatePanelProps = {
  title: string;
  body: string;
  loading?: boolean;
};

export function StatePanel({ title, body, loading = false }: StatePanelProps) {
  const { colors } = useAppTheme();

  return (
    <Surface>
      <View style={styles.container}>
        {loading ? <ActivityIndicator color={colors.accent} /> : null}
        <Text style={[styles.title, { color: colors.text }]}>{title}</Text>
        <Text style={[styles.body, { color: colors.textMuted }]}>{body}</Text>
      </View>
    </Surface>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 10,
    alignItems: "flex-start",
  },
  title: {
    fontSize: 18,
    fontWeight: "700",
  },
  body: {
    fontSize: 14,
    lineHeight: 21,
  },
});
