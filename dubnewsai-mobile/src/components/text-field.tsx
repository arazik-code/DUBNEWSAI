import type { TextInputProps } from "react-native";

import { StyleSheet, Text, TextInput, View } from "react-native";

import { radii, useAppTheme } from "@/lib/theme";

type TextFieldProps = TextInputProps & {
  label: string;
  hint?: string;
};

export function TextField({ label, hint, style, ...props }: TextFieldProps) {
  const { colors } = useAppTheme();

  return (
    <View style={styles.wrapper}>
      <Text style={[styles.label, { color: colors.textSoft }]}>{label}</Text>
      <TextInput
        placeholderTextColor={colors.textMuted}
        style={[
          styles.input,
          {
            color: colors.text,
            backgroundColor: colors.surfaceMuted,
            borderColor: colors.border,
          },
          style,
        ]}
        {...props}
      />
      {hint ? <Text style={[styles.hint, { color: colors.textMuted }]}>{hint}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    gap: 8,
  },
  label: {
    fontSize: 13,
    fontWeight: "600",
    letterSpacing: 0.2,
  },
  input: {
    minHeight: 54,
    borderRadius: radii.lg,
    borderWidth: 1,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 15,
  },
  hint: {
    fontSize: 12,
    lineHeight: 18,
  },
});
