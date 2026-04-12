import { useState } from "react";

import { useMutation } from "@tanstack/react-query";
import { router } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { PrimaryButton } from "@/components/primary-button";
import { ScreenShell } from "@/components/screen-shell";
import { TextField } from "@/components/text-field";
import { loginWithPassword } from "@/lib/auth/actions";
import { queryClient } from "@/lib/providers/app-providers";
import { useAppTheme } from "@/lib/theme";

export default function LoginScreen() {
  const { colors } = useAppTheme();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const loginMutation = useMutation({
    mutationFn: () => loginWithPassword(email.trim(), password),
    onSuccess: async () => {
      await queryClient.invalidateQueries();
      router.replace("/");
    },
  });

  return (
    <ScreenShell>
      <View style={styles.header}>
        <Text style={[styles.kicker, { color: colors.accent }]}>Authentication</Text>
        <Text style={[styles.title, { color: colors.text }]}>Sign in to unlock your workspace</Text>
        <Text style={[styles.body, { color: colors.textMuted }]}>
          Analytics, alerts, settings, and admin-granted enterprise modules activate after authentication.
        </Text>
      </View>

      <View style={styles.form}>
        <TextField
          label="Email"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          keyboardType="email-address"
        />
        <TextField label="Password" value={password} onChangeText={setPassword} secureTextEntry />
        {loginMutation.error ? (
          <Text style={[styles.error, { color: colors.danger }]}>{loginMutation.error.message}</Text>
        ) : null}
        <PrimaryButton
          label={loginMutation.isPending ? "Signing in..." : "Sign in"}
          onPress={() => loginMutation.mutate()}
          loading={loginMutation.isPending}
        />
        <PrimaryButton label="Create account" variant="secondary" onPress={() => router.push("/register")} />
      </View>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  header: {
    gap: 10,
    paddingTop: 20,
  },
  kicker: {
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1.6,
    textTransform: "uppercase",
  },
  title: {
    fontSize: 34,
    lineHeight: 38,
    fontWeight: "900",
    letterSpacing: -0.8,
  },
  body: {
    fontSize: 15,
    lineHeight: 24,
  },
  form: {
    gap: 14,
  },
  error: {
    fontSize: 13,
    fontWeight: "700",
  },
});
