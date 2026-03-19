"use client"

import Link from "next/link"
import { Newspaper } from "lucide-react"

import { NewsCard } from "@/components/news/NewsCard"
import { LoadingSpinner } from "@/components/shared/LoadingSpinner"
import { useNews } from "@/lib/hooks/useNews"

export function NewsFeed({
  pageSize = 8,
  showBrowseLink = true
}: {
  pageSize?: number
  showBrowseLink?: boolean
}) {
  const { data, isLoading, isError } = useNews({ page: 1, page_size: pageSize })

  if (isLoading) {
    return (
      <section className="panel p-6">
        <LoadingSpinner />
      </section>
    )
  }

  if (isError) {
    return (
      <section className="panel p-6">
        <p className="text-sm text-red-500">Unable to load the latest news right now.</p>
      </section>
    )
  }

  const articles = data?.articles || []
  const [featured, ...remaining] = articles

  return (
    <section className="space-y-5">
      <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="mb-1 flex items-center gap-2 text-sm uppercase tracking-[0.25em] text-cyber-500">
            <Newspaper className="h-4 w-4" />
            Multi-Source Feed
          </div>
          <h2 className="text-2xl font-display font-semibold text-slate-950 dark:text-white">News and Intelligence Stream</h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            {data?.total || 0} indexed stories with full article detail, deduped across providers.
          </p>
        </div>

        {showBrowseLink ? (
          <Link
            href="/news"
            className="inline-flex items-center rounded-2xl border border-white/10 px-4 py-3 text-sm font-medium text-slate-700 transition hover:border-gold-400 hover:text-gold-500 dark:text-slate-200"
          >
            Browse full feed
          </Link>
        ) : null}
      </div>

      {featured ? (
        <div className="grid gap-4 xl:grid-cols-[1.2fr_1fr]">
          <NewsCard article={featured} featured />

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-1">
            {remaining.slice(0, 3).map((article) => (
              <NewsCard key={article.id} article={article} />
            ))}
          </div>
        </div>
      ) : null}

      {remaining.length > 3 ? (
        <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
          {remaining.slice(3).map((article) => (
            <NewsCard key={article.id} article={article} />
          ))}
        </div>
      ) : null}
    </section>
  )
}
