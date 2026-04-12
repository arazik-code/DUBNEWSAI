import { Pressable, StyleSheet, Text } from "react-native";

import { radii, useAppTheme } from "@/lib/theme";

type ChoiceChipProps = {
  label: string;
  selected: boolean;
  onPress: () => void;
};

export function ChoiceChip({ label, selected, onPress }: ChoiceChipProps) {
  const { colors, isDark } = useAppTheme();

  return (
    <Pressable
      onPress={onPress}
      style={[
        styles.chip,
        {
          backgroundColor: selected ? colors.accentSoft : colors.surfaceMuted,
          borderColor: selected ? colors.accent : colors.border,
          shadowOpacity: selected && isDark ? 0.2 : 0,
        },
      ]}
    >
      <Text
        style={[
          styles.label,
          {
            color: selected ? colors.text : colors.textSoft,
          },
        ]}
      >
        {label}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  chip: {
    borderRadius: radii.pill,
    borderWidth: 1,
    paddingHorizontal: 14,
    paddingVertical: 10,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 8 },
    shadowRadius: 16,
  },
  label: {
    fontSize: 13,
    fontWeight: "700",
  },
});
