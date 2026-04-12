import { useEffect, useState } from "react";

import { useMutation, useQuery } from "@tanstack/react-query";
import { StyleSheet, Text, View } from "react-native";

import { AccessGate } from "@/components/access-gate";
import { ChoiceChip } from "@/components/choice-chip";
import { PrimaryButton } from "@/components/primary-button";
import { ScreenShell } from "@/components/screen-shell";
import { SectionHeader } from "@/components/section-header";
import { StatePanel } from "@/components/state-panel";
import { Surface } from "@/components/surface";
import { TextField } from "@/components/text-field";
import { mobileApi } from "@/lib/api/queries";
import { queryClient } from "@/lib/providers/app-providers";
import { useAuthStore } from "@/lib/state/auth-store";
import { useAppTheme } from "@/lib/theme";

export default function TeamsScreen() {
  const { colors } = useAppTheme();
  const user = useAuthStore((state) => state.user);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [maxMembers, setMaxMembers] = useState("10");
  const [selectedTeamId, setSelectedTeamId] = useState<number | null>(null);

  const featureAccessQuery = useQuery({
    queryKey: ["mobile-feature-access-teams"],
    queryFn: mobileApi.getFeatureAccess,
    enabled: Boolean(user),
  });

  const hasAccess =
    featureAccessQuery.data?.find((item) => item.feature_key === "teams")?.has_access ?? false;

  const teamsQuery = useQuery({
    queryKey: ["mobile-teams"],
    queryFn: mobileApi.getTeams,
    enabled: Boolean(user && hasAccess),
  });

  useEffect(() => {
    if (!selectedTeamId && teamsQuery.data?.[0]?.id) {
      setSelectedTeamId(teamsQuery.data[0].id);
    }
  }, [selectedTeamId, teamsQuery.data]);

  const activityQuery = useQuery({
    queryKey: ["mobile-team-activity", selectedTeamId],
    queryFn: () => mobileApi.getTeamActivity(selectedTeamId as number),
    enabled: Boolean(selectedTeamId),
  });

  const createTeamMutation = useMutation({
    mutationFn: () =>
      mobileApi.createTeam({
        name: name.trim(),
        description: description.trim() || undefined,
        max_members: Number(maxMembers || "10"),
        shared_portfolios: true,
        shared_watchlists: true,
        shared_insights: true,
      }),
    onSuccess: async (team) => {
      setName("");
      setDescription("");
      await queryClient.invalidateQueries({ queryKey: ["mobile-teams"] });
      setSelectedTeamId(team.id);
    },
  });

  if (!user) {
    return (
      <ScreenShell>
        <AccessGate
          title="Teams requires sign-in"
          body="Team collaboration opens only after authentication and admin access."
        />
      </ScreenShell>
    );
  }

  if (featureAccessQuery.isLoading) {
    return (
      <ScreenShell>
        <StatePanel title="Loading access" body="Checking team collaboration permissions." loading />
      </ScreenShell>
    );
  }

  if (featureAccessQuery.isError) {
    return (
      <ScreenShell>
        <StatePanel title="Access check unavailable" body="Team permissions could not be verified right now." />
      </ScreenShell>
    );
  }

  if (!hasAccess) {
    return (
      <ScreenShell>
        <AccessGate
          title="Teams is admin-granted"
          body="Your admin needs to grant team access before collaboration tools can open."
        />
      </ScreenShell>
    );
  }

  if (teamsQuery.isLoading) {
    return (
      <ScreenShell>
        <StatePanel title="Loading teams" body="Syncing your collaboration spaces." loading />
      </ScreenShell>
    );
  }

  if (teamsQuery.isError) {
    return (
      <ScreenShell>
        <StatePanel title="Teams unavailable" body="The teams workspace could not be loaded right now." />
      </ScreenShell>
    );
  }

  return (
    <ScreenShell>
      <View style={styles.header}>
        <Text style={[styles.kicker, { color: colors.accent }]}>Teams</Text>
        <Text style={[styles.title, { color: colors.text }]}>Collaboration spaces built for motion.</Text>
        <Text style={[styles.body, { color: colors.textMuted }]}>
          Create a team, pick the active space, and keep an eye on recent activity from one screen.
        </Text>
      </View>

      <Surface style={styles.formCard}>
        <Text style={[styles.formTitle, { color: colors.text }]}>Create team</Text>
        <TextField label="Team name" value={name} onChangeText={setName} />
        <TextField
          label="Description"
          value={description}
          onChangeText={setDescription}
          placeholder="Leadership, research, acquisitions..."
        />
        <TextField
          label="Max members"
          value={maxMembers}
          onChangeText={setMaxMembers}
          keyboardType="numeric"
        />
        {createTeamMutation.error ? (
          <Text style={[styles.errorText, { color: colors.danger }]}>{createTeamMutation.error.message}</Text>
        ) : null}
        <PrimaryButton
          label={createTeamMutation.isPending ? "Creating team..." : "Create team"}
          onPress={() => createTeamMutation.mutate()}
          loading={createTeamMutation.isPending}
        />
      </Surface>

      <View>
        <SectionHeader
          eyebrow="Spaces"
          title="Your teams"
          description="Switch the active team below to inspect collaboration activity."
        />
        <View style={styles.chipWrap}>
          {(teamsQuery.data ?? []).map((team) => (
            <ChoiceChip
              key={team.id}
              label={team.name}
              selected={selectedTeamId === team.id}
              onPress={() => setSelectedTeamId(team.id)}
            />
          ))}
        </View>
      </View>

      <View style={styles.list}>
        {(teamsQuery.data ?? []).map((team) => (
          <Surface key={team.id} style={styles.card}>
            <Text style={[styles.cardTitle, { color: colors.text }]}>{team.name}</Text>
            <Text style={[styles.cardMeta, { color: colors.textMuted }]}>
              Max {team.max_members} members · {team.shared_insights ? "Insights shared" : "Private insights"}
            </Text>
            <Text style={[styles.cardBody, { color: colors.textSoft }]}>
              {team.description || "Collaboration space ready for shared work."}
            </Text>
          </Surface>
        ))}
      </View>

      <View>
        <SectionHeader
          eyebrow="Activity"
          title="Selected team feed"
          description="A lightweight event feed for the currently active team."
        />
        {activityQuery.isLoading ? (
          <StatePanel title="Loading activity" body="Pulling the latest collaboration events." loading />
        ) : activityQuery.isError ? (
          <StatePanel title="Activity unavailable" body="This team activity feed could not be loaded right now." />
        ) : (
          <View style={styles.list}>
            {(activityQuery.data ?? []).slice(0, 8).map((entry, index) => (
              <Surface key={`activity-${index}`} style={styles.card}>
                <Text style={[styles.cardTitle, { color: colors.text }]}>
                  {String(entry.description ?? "Team activity")}
                </Text>
                <Text style={[styles.cardMeta, { color: colors.textMuted }]}>
                  {String(entry.activity_type ?? "update")}
                </Text>
              </Surface>
            ))}
          </View>
        )}
      </View>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  header: {
    gap: 10,
    paddingTop: 12,
  },
  kicker: {
    fontSize: 11,
    fontWeight: "800",
    letterSpacing: 1.6,
    textTransform: "uppercase",
  },
  title: {
    fontSize: 32,
    lineHeight: 36,
    fontWeight: "900",
    letterSpacing: -0.9,
  },
  body: {
    fontSize: 15,
    lineHeight: 24,
  },
  formCard: {
    gap: 14,
  },
  formTitle: {
    fontSize: 18,
    fontWeight: "800",
  },
  errorText: {
    fontSize: 13,
    fontWeight: "700",
  },
  chipWrap: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10,
  },
  list: {
    gap: 12,
  },
  card: {
    gap: 8,
  },
  cardTitle: {
    fontSize: 17,
    fontWeight: "800",
  },
  cardMeta: {
    fontSize: 13,
    lineHeight: 20,
  },
  cardBody: {
    fontSize: 14,
    lineHeight: 22,
  },
});
