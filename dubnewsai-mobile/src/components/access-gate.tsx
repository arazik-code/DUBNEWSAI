import { router } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { StyleSheet, Text, View } from "react-native";

import { PrimaryButton } from "./primary-button";
import { Surface } from "./surface";

import { useAppTheme } from "@/lib/theme";

type AccessGateProps = {
  title: string;
  body: string;
};

export function AccessGate({ title, body }: AccessGateProps) {
  const { colors } = useAppTheme();

  return (
    <Surface>
      <View style={styles.container}>
        <View style={[styles.iconWrap, { backgroundColor: colors.accentSoft }]}>
          <Ionicons name="lock-closed" size={18} color={colors.accent} />
        </View>
        <Text style={[styles.title, { color: colors.text }]}>{title}</Text>
        <Text style={[styles.body, { color: colors.textMuted }]}>{body}</Text>
        <PrimaryButton label="Sign in to continue" onPress={() => router.push("/login")} />
      </View>
    </Surface>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 14,
  },
  iconWrap: {
    width: 42,
    height: 42,
    borderRadius: 999,
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    fontSize: 20,
    fontWeight: "800",
  },
  body: {
    fontSize: 14,
    lineHeight: 21,
  },
});
