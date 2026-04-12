import { useMemo, useState } from "react";

import { useQuery } from "@tanstack/react-query";
import { router } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { ArticleCard } from "@/components/article-card";
import { PrimaryButton } from "@/components/primary-button";
import { ScreenShell } from "@/components/screen-shell";
import { SectionHeader } from "@/components/section-header";
import { StatePanel } from "@/components/state-panel";
import { TextField } from "@/components/text-field";
import { mobileApi } from "@/lib/api/queries";
import { useAppTheme } from "@/lib/theme";

export default function NewsScreen() {
  const { colors } = useAppTheme();
  const [draftSearch, setDraftSearch] = useState("");
  const [submittedSearch, setSubmittedSearch] = useState("");

  const newsQuery = useQuery({
    queryKey: ["news-feed", submittedSearch],
    queryFn: () =>
      mobileApi.getNews({
        page: 1,
        page_size: 20,
        search: submittedSearch || undefined,
      }),
  });

  const articles = useMemo(() => newsQuery.data?.articles ?? [], [newsQuery.data]);

  return (
    <ScreenShell>
      <View style={styles.header}>
        <Text style={[styles.kicker, { color: colors.accent }]}>Editorial feed</Text>
        <Text style={[styles.title, { color: colors.text }]}>News intelligence</Text>
        <Text style={[styles.body, { color: colors.textMuted }]}>
          Scan today&apos;s Dubai and UAE coverage, then open any story into the full on-platform detail view.
        </Text>
      </View>

      <View style={styles.searchBlock}>
        <TextField
          label="Search the feed"
          placeholder="Emaar, Dubai Marina, mortgage rates..."
          value={draftSearch}
          onChangeText={setDraftSearch}
          returnKeyType="search"
          onSubmitEditing={() => setSubmittedSearch(draftSearch.trim())}
        />
        <PrimaryButton label="Search" onPress={() => setSubmittedSearch(draftSearch.trim())} />
      </View>

      {newsQuery.isLoading ? (
        <StatePanel title="Loading the feed" body="Bringing in the latest editorial flow." loading />
      ) : newsQuery.isError ? (
        <StatePanel title="Feed unavailable" body="The mobile news feed could not be loaded right now." />
      ) : articles.length === 0 ? (
        <StatePanel
          title="No stories matched"
          body="Try a broader term or clear the search to return to the full feed."
        />
      ) : (
        <View style={styles.list}>
          <SectionHeader
            eyebrow={submittedSearch ? "Filtered results" : "Latest coverage"}
            title={submittedSearch ? `Results for "${submittedSearch}"` : "Top stories from the current cycle"}
            description="Cards stay compact for mobile, and the full article lives one tap away."
          />
          {articles.map((article) => (
            <ArticleCard
              key={article.id}
              article={{
                id: article.id,
                title: article.title,
                description: article.description,
                source_name: article.source_name,
                category: article.category,
                sentiment: article.sentiment,
                published_at: article.published_at,
                image_url: article.image_url,
                relevance_score: article.relevance_score,
              }}
              onPress={() => router.push(`/news/${article.id}`)}
            />
          ))}
        </View>
      )}
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
    fontSize: 34,
    lineHeight: 38,
    fontWeight: "900",
    letterSpacing: -0.9,
  },
  body: {
    fontSize: 15,
    lineHeight: 24,
  },
  searchBlock: {
    gap: 12,
  },
  list: {
    gap: 14,
  },
});

