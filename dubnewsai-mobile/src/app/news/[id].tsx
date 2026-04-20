import { useMemo } from "react";

import { Image } from "expo-image";
import { router, useLocalSearchParams } from "expo-router";
import { Linking, StyleSheet, Text, View } from "react-native";
import { useQuery } from "@tanstack/react-query";

import { PrimaryButton } from "@/components/primary-button";
import { ScreenShell } from "@/components/screen-shell";
import { StatePanel } from "@/components/state-panel";
import { Surface } from "@/components/surface";
import { mobileApi } from "@/lib/api/queries";
import { formatDateLabel, sentenceCase } from "@/lib/formatters";
import { radii, useAppTheme } from "@/lib/theme";

export default function NewsDetailScreen() {
  const { colors } = useAppTheme();
  const params = useLocalSearchParams<{ id?: string }>();
  const articleId = Number(params.id);

  const articleQuery = useQuery({
    queryKey: ["mobile-article", articleId],
    queryFn: () => mobileApi.getArticle(articleId),
    enabled: Number.isFinite(articleId),
  });

  const paragraphs = useMemo(() => {
    const text = articleQuery.data?.content || articleQuery.data?.description || "";
    return text
      .split(/\n{2,}/)
      .map((paragraph) => paragraph.trim())
      .filter(Boolean);
  }, [articleQuery.data]);

  if (articleQuery.isLoading) {
    return (
      <ScreenShell>
        <StatePanel
          title="Opening article"
          body="Loading the full news detail view."
          loading
        />
      </ScreenShell>
    );
  }

  if (articleQuery.isError || !articleQuery.data) {
    return (
      <ScreenShell>
        <StatePanel
          title="Article unavailable"
          body="This story could not be loaded right now."
        />
      </ScreenShell>
    );
  }

  const article = articleQuery.data;

  return (
    <ScreenShell>
      <View style={styles.hero}>
        <Text style={[styles.kicker, { color: colors.accent }]}>
          {article.source_name || sentenceCase(article.category)}
        </Text>
        <Text style={[styles.title, { color: colors.text }]}>{article.title}</Text>
        <Text style={[styles.meta, { color: colors.textMuted }]}>
          {formatDateLabel(article.published_at)} | {sentenceCase(article.sentiment)}
        </Text>
      </View>

      {article.image_url ? (
        <Image source={article.image_url} style={styles.image} contentFit="cover" />
      ) : null}

      <Surface style={styles.summaryCard}>
        <Text style={[styles.summaryTitle, { color: colors.text }]}>Story summary</Text>
        <Text style={[styles.summaryBody, { color: colors.textMuted }]}>
          {article.description || "This article is available in the detailed reading view below."}
        </Text>
      </Surface>

      <View style={styles.bodyWrap}>
        {paragraphs.length > 0 ? (
          paragraphs.map((paragraph, index) => (
            <Text key={`${article.id}-${index}`} style={[styles.paragraph, { color: colors.textSoft }]}>
              {paragraph}
            </Text>
          ))
        ) : (
          <Surface>
            <Text style={[styles.summaryBody, { color: colors.textMuted }]}>
              Full article text is not available for this story right now, but the source link is still available below.
            </Text>
          </Surface>
        )}
      </View>

      <View style={styles.actions}>
        <PrimaryButton label="Back to news" variant="secondary" onPress={() => router.back()} />
        <PrimaryButton label="Open source" onPress={() => Linking.openURL(article.url)} />
      </View>
    </ScreenShell>
  );
}

const styles = StyleSheet.create({
  hero: {
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
    fontSize: 30,
    lineHeight: 36,
    fontWeight: "900",
    letterSpacing: -0.8,
  },
  meta: {
    fontSize: 13,
    lineHeight: 20,
  },
  image: {
    width: "100%",
    height: 260,
    borderRadius: radii.xl,
  },
  summaryCard: {
    gap: 8,
  },
  summaryTitle: {
    fontSize: 18,
    fontWeight: "800",
  },
  summaryBody: {
    fontSize: 14,
    lineHeight: 22,
  },
  bodyWrap: {
    gap: 14,
  },
  paragraph: {
    fontSize: 15,
    lineHeight: 26,
  },
  actions: {
    gap: 12,
  },
});
