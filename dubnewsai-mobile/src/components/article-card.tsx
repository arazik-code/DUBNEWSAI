import { Image } from "expo-image";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { Surface } from "./surface";

import { formatRelativeTime, sentenceCase } from "@/lib/formatters";
import { radii, useAppTheme } from "@/lib/theme";
import type { MobileArticleCard } from "@/lib/api/types";

type ArticleCardProps = {
  article: MobileArticleCard;
  onPress: () => void;
  featured?: boolean;
};

export function ArticleCard({ article, onPress, featured = false }: ArticleCardProps) {
  const { colors } = useAppTheme();

  return (
    <Pressable onPress={onPress}>
      <Surface style={featured ? styles.featuredSurface : undefined}>
        <View style={styles.container}>
          {article.image_url ? (
            <Image source={article.image_url} style={featured ? styles.heroImage : styles.thumb} contentFit="cover" />
          ) : null}
          <View style={styles.copy}>
            <View style={styles.metaRow}>
              <Text style={[styles.source, { color: colors.accent }]}>
                {article.source_name || sentenceCase(article.category)}
              </Text>
              <Text style={[styles.timestamp, { color: colors.textMuted }]}>
                {formatRelativeTime(article.published_at)}
              </Text>
            </View>
            <Text style={[featured ? styles.featuredTitle : styles.title, { color: colors.text }]}>
              {article.title}
            </Text>
            {article.description ? (
              <Text style={[styles.description, { color: colors.textMuted }]} numberOfLines={featured ? 4 : 3}>
                {article.description}
              </Text>
            ) : null}
          </View>
        </View>
      </Surface>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 14,
  },
  featuredSurface: {
    padding: 14,
  },
  heroImage: {
    width: "100%",
    height: 220,
    borderRadius: radii.lg,
  },
  thumb: {
    width: "100%",
    height: 130,
    borderRadius: radii.lg,
  },
  copy: {
    gap: 8,
  },
  metaRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 12,
  },
  source: {
    fontSize: 11,
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: 1.4,
  },
  timestamp: {
    fontSize: 11,
    fontWeight: "600",
  },
  featuredTitle: {
    fontSize: 22,
    fontWeight: "800",
    lineHeight: 28,
  },
  title: {
    fontSize: 16,
    fontWeight: "700",
    lineHeight: 22,
  },
  description: {
    fontSize: 14,
    lineHeight: 21,
  },
});
