import { Pressable, StyleSheet, Text, View } from "react-native";

import { useAppTheme } from "@/lib/theme";

type SectionHeaderProps = {
  eyebrow?: string;
  title: string;
  description?: string;
  actionLabel?: string;
  onActionPress?: () => void;
};

export function SectionHeader({
  eyebrow,
  title,
  description,
  actionLabel,
  onActionPress,
}: SectionHeaderProps) {
  const { colors } = useAppTheme();

  return (
    <View style={styles.row}>
      <View style={styles.copy}>
        {eyebrow ? <Text style={[styles.eyebrow, { color: colors.accent }]}>{eyebrow}</Text> : null}
        <Text style={[styles.title, { color: colors.text }]}>{title}</Text>
        {description ? <Text style={[styles.description, { color: colors.textMuted }]}>{description}</Text> : null}
      </View>
      {actionLabel && onActionPress ? (
        <Pressable onPress={onActionPress}>
          <Text style={[styles.action, { color: colors.textSoft }]}>{actionLabel}</Text>
        </Pressable>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    gap: 16,
  },
  copy: {
    flex: 1,
    gap: 6,
  },
  eyebrow: {
    fontSize: 11,
    fontWeight: "700",
    letterSpacing: 1.6,
    textTransform: "uppercase",
  },
  title: {
    fontSize: 24,
    fontWeight: "800",
    lineHeight: 29,
  },
  description: {
    fontSize: 14,
    lineHeight: 21,
  },
  action: {
    fontSize: 13,
    fontWeight: "700",
    paddingTop: 6,
  },
});
