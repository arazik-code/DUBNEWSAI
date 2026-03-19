import type { Metadata } from "next"
import Link from "next/link"
import { notFound } from "next/navigation"

import { SentimentBadge } from "@/components/news/SentimentBadge"
import type { NewsArticle } from "@/types"
import { formatDateTime, titleCase } from "@/lib/utils/formatters"

interface ArticlePageProps {
  params: {
    id: string
  }
}

const API_URL =
  process.env.INTERNAL_API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api/v1"

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000"

async function getArticle(id: string): Promise<NewsArticle | null> {
  try {
    const response = await fetch(`${API_URL}/news/${id}`, {
      next: { revalidate: 300 }
    })

    if (!response.ok) {
      return null
    }

    return (await response.json()) as NewsArticle
  } catch {
    return null
  }
}

export async function generateMetadata({ params }: ArticlePageProps): Promise<Metadata> {
  const article = await getArticle(params.id)
  if (!article) {
    return {
      title: "Article Not Found | DUBNEWSAI"
    }
  }

  return {
    title: `${article.title} | DUBNEWSAI`,
    description: article.description || article.title,
    keywords: article.keywords,
    authors: article.source_name ? [{ name: article.source_name }] : undefined,
    openGraph: {
      title: article.title,
      description: article.description || article.title,
      images: article.image_url ? [{ url: article.image_url }] : undefined,
      type: "article",
      publishedTime: article.published_at,
      authors: article.source_name ? [article.source_name] : undefined
    },
    twitter: {
      card: "summary_large_image",
      title: article.title,
      description: article.description || article.title,
      images: article.image_url ? [article.image_url] : undefined
    },
    alternates: {
      canonical: `${APP_URL}/news/${params.id}`
    }
  }
}

export default async function ArticlePage({ params }: ArticlePageProps) {
  const article = await getArticle(params.id)
  if (!article) {
    notFound()
  }
  const contentBlocks = (article.content || "")
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean)

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    headline: article.title,
    description: article.description || article.title,
    image: article.image_url,
    datePublished: article.published_at,
    dateModified: article.updated_at,
    author: {
      "@type": "Organization",
      name: article.source_name || "DUBNEWSAI"
    },
    publisher: {
      "@type": "Organization",
      name: "DUBNEWSAI",
      logo: {
        "@type": "ImageObject",
        url: `${APP_URL}/icons/logo.png`
      }
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <div className="container mx-auto max-w-4xl px-4 py-12">
        <div className="mb-8 flex items-center justify-between gap-4">
          <Link href="/news" className="text-sm font-medium text-cyber-500 transition hover:text-cyber-400">
            Back to news
          </Link>
          <Link href="/" className="text-sm font-medium text-gold-500 transition hover:text-gold-400">
            Open platform
          </Link>
        </div>

        <article className="panel space-y-8 p-8">
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-full bg-gold-500/10 px-3 py-1 text-xs font-medium text-gold-500">
              {titleCase(article.category)}
            </span>
            <SentimentBadge sentiment={article.sentiment} score={article.sentiment_score} />
            {article.primary_provider ? (
              <span className="rounded-full bg-cyber-500/10 px-3 py-1 text-xs font-medium text-cyber-500">
                {titleCase(article.primary_provider)}
              </span>
            ) : null}
            <span className="text-xs uppercase tracking-[0.2em] text-slate-500">
              {article.source_name || "DUBNEWSAI"}
            </span>
          </div>

          <div>
            <h1 className="text-4xl font-display font-semibold text-slate-950 dark:text-white">{article.title}</h1>
            <p className="mt-3 text-sm text-slate-500 dark:text-slate-400">
              Published {formatDateTime(article.published_at)} | {article.view_count} views
            </p>
          </div>

          {article.description ? (
            <p className="text-lg leading-8 text-slate-700 dark:text-slate-300">{article.description}</p>
          ) : null}

          <div className="grid gap-3 rounded-3xl border border-white/10 bg-slate-950/5 p-4 text-sm text-slate-600 dark:bg-white/5 dark:text-slate-300 md:grid-cols-3">
            <div>
              <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Quality</div>
              <div className="mt-1 font-semibold text-slate-950 dark:text-white">
                {article.quality_score !== undefined ? `${Math.round(article.quality_score)}%` : "N/A"}
              </div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Source Coverage</div>
              <div className="mt-1 font-semibold text-slate-950 dark:text-white">
                {article.duplicate_count && article.duplicate_count > 1 ? `${article.duplicate_count} matching sources` : "Single-source match"}
              </div>
            </div>
            <div>
              <div className="text-xs uppercase tracking-[0.18em] text-slate-500">Enrichment</div>
              <div className="mt-1 font-semibold text-slate-950 dark:text-white">
                {article.enrichment_status ? titleCase(article.enrichment_status) : "Completed"}
              </div>
            </div>
          </div>

          <div className="space-y-5 text-base leading-8 text-slate-700 dark:text-slate-300">
            {contentBlocks.length ? (
              contentBlocks.map((block, index) => (
                <p key={`${article.id}-block-${index}`}>{block}</p>
              ))
            ) : (
              <p>No long-form content is available for this article yet.</p>
            )}
          </div>

          {article.keywords?.length ? (
            <div className="flex flex-wrap gap-2">
              {article.keywords.map((keyword) => (
                <span key={keyword} className="rounded-full bg-cyber-500/10 px-3 py-1 text-xs font-medium text-cyber-500">
                  {keyword}
                </span>
              ))}
            </div>
          ) : null}

          {article.url ? (
            <Link
              href={article.url}
              target="_blank"
              className="inline-flex rounded-2xl border border-white/10 px-4 py-3 text-sm font-medium text-slate-700 transition hover:border-gold-400 hover:text-gold-500 dark:text-slate-200"
            >
              Open original source
            </Link>
          ) : null}
        </article>
      </div>
    </div>
  )
}
