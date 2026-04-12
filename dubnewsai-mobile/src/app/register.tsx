import { useState } from "react";

import { useMutation } from "@tanstack/react-query";
import { router } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { PrimaryButton } from "@/components/primary-button";
import { ScreenShell } from "@/components/screen-shell";
import { TextField } from "@/components/text-field";
import { registerWithPassword } from "@/lib/auth/actions";
import { queryClient } from "@/lib/providers/app-providers";
import { useAppTheme } from "@/lib/theme";

export default function RegisterScreen() {
  const { colors } = useAppTheme();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const registerMutation = useMutation({
    mutationFn: () => registerWithPassword(fullName.trim(), email.trim(), password),
    onSuccess: async () => {
      await queryClient.invalidateQueries();
      router.replace("/");
    },
  });

  return (
    <ScreenShell>
      <View style={styles.header}>
        <Text style={[styles.kicker, { color: colors.accent }]}>Create account</Text>
        <Text style={[styles.title, { color: colors.text }]}>Start your DUBNEWSAI mobile workspace</Text>
        <Text style={[styles.body, { color: colors.textMuted }]}>
          New accounts get news and market access as guests, then analytics, alerts, and settings after sign-in.
        </Text>
      </View>

      <View style={styles.form}>
        <TextField label="Full name" value={fullName} onChangeText={setFullName} />
        <TextField
          label="Email"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          keyboardType="email-address"
        />
        <TextField
          label="Password"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          hint="Use at least 8 characters."
        />
        {registerMutation.error ? (
          <Text style={[styles.error, { color: colors.danger }]}>{registerMutation.error.message}</Text>
        ) : null}
        <PrimaryButton
          label={registerMutation.isPending ? "Creating account..." : "Create account"}
          onPress={() => registerMutation.mutate()}
          loading={registerMutation.isPending}
        />
        <PrimaryButton label="Back to sign in" variant="secondary" onPress={() => router.replace("/login")} />
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
