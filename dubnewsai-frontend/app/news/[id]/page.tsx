import type { Metadata } from "next"
import Image from "next/image"
import Link from "next/link"
import { notFound } from "next/navigation"
import { ArrowLeft, ArrowUpRight, Eye, Layers3, Link2, ScanSearch } from "lucide-react"

import { ContainerScroll } from "@/components/ui/container-scroll-animation"
import { SentimentBadge } from "@/components/news/SentimentBadge"
import { getDefaultAppUrl, normalizeApiBaseUrl } from "@/lib/config/api"
import type { NewsArticle } from "@/types"
import { formatDateTime, titleCase } from "@/lib/utils/formatters"

interface ArticlePageProps {
  params: {
    id: string
  }
}

const API_URL = normalizeApiBaseUrl(process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL)

const APP_URL = getDefaultAppUrl(process.env.NEXT_PUBLIC_APP_URL)

async function getArticle(id: string): Promise<NewsArticle | null> {
  try {
    const response = await fetch(`${API_URL}/news/${id}`, {
      next: { revalidate: 60 }
    })

    if (!response.ok) {
      return null
    }

    return (await response.json()) as NewsArticle
  } catch {
    return null
  }
}

function normalizeArticleBody(article: NewsArticle) {
  const stripTruncationMarker = (value: string) =>
    value
      .replace(/\.\.\.\s*\[\d+\s+chars\]\s*$/i, "")
      .replace(/\[\+\d+\s+chars\]\s*$/i, "")
      .trim()

  const compactLead = (value: string) => {
    const normalized = stripTruncationMarker(value).trim().replace(/\s+/g, " ")
    if (!normalized) {
      return ""
    }

    const sentences = normalized
      .split(/(?<=[.!?])\s+(?=[A-Z0-9"'])/g)
      .map((sentence) => sentence.trim())
      .filter(Boolean)

    let summary = ""
    for (const sentence of sentences.slice(0, 3)) {
      const candidate = summary ? `${summary} ${sentence}` : sentence
      if (summary && candidate.length > 380) {
        break
      }
      summary = candidate
    }

    const fallback = summary || normalized.slice(0, 380)
    return fallback.trim()
  }

  const description = compactLead(article.description || "")
  let content = stripTruncationMarker(article.content || "")

  if (description && content.toLowerCase().startsWith(description.toLowerCase())) {
    content = content.slice(description.length).trim()
  }

  const blocks =
    content && content.includes("\n\n")
      ? content
          .split(/\n{2,}/)
          .map((block) => block.trim())
          .filter(Boolean)
      : content
          .split(/(?<=[.!?])\s+(?=[A-Z0-9"'])/g)
          .map((sentence) => sentence.trim())
          .filter(Boolean)
          .reduce<string[]>((acc, sentence) => {
            const current = acc[acc.length - 1]
            if (!current) {
              acc.push(sentence)
              return acc
            }
            if (current.length < 320) {
              acc[acc.length - 1] = `${current} ${sentence}`
            } else {
              acc.push(sentence)
            }
            return acc
          }, [])

  const filteredBlocks = blocks.filter((block) => block.toLowerCase() !== description.toLowerCase())
  return {
    lead: description || compactLead(filteredBlocks[0] || "") || article.title,
    blocks: filteredBlocks.length ? filteredBlocks : description ? [description] : []
  }
}

function estimateReadTime(article: NewsArticle) {
  const text = article.content || article.description || article.title
  const words = text.split(/\s+/).filter(Boolean).length
  return Math.max(2, Math.ceil(words / 220))
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

  const normalizedBody = normalizeArticleBody(article)
  const contentBlocks = normalizedBody.blocks
  const entityGroups = Object.entries(article.entities || {}).filter(([, values]) => values?.length)
  const readTime = estimateReadTime(article)
  const leadSummary = normalizedBody.lead
  const storyFacts = [
    { label: "Source", value: article.source_name || "DUBNEWSAI" },
    {
      label: "Coverage",
      value: article.duplicate_count && article.duplicate_count > 1 ? `${article.duplicate_count} sources` : "Single source"
    },
    { label: "Read time", value: `${readTime} min` },
    {
      label: "Quality",
      value: article.quality_score !== undefined ? `${Math.round(article.quality_score)}%` : "N/A"
    }
  ]

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
    <div className="min-h-screen bg-[#050506] text-white">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />

      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-8 sm:px-6 lg:px-8">
        <Link href="/news" className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm font-medium text-white/78 transition hover:text-white">
          <ArrowLeft className="h-4 w-4" />
          Back to news
        </Link>
        {article.url ? (
          <Link
            href={article.url}
            target="_blank"
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm font-medium text-white/78 transition hover:text-white"
          >
            Original source
            <ArrowUpRight className="h-4 w-4" />
          </Link>
        ) : null}
      </div>

      <ContainerScroll
        titleComponent={
          <div className="px-4 sm:px-0">
            <div className="mx-auto max-w-4xl">
              <div className="flex flex-wrap items-center justify-center gap-2">
                <span className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-[10px] uppercase tracking-[0.28em] text-white/62">
                  {titleCase(article.category)}
                </span>
                <SentimentBadge sentiment={article.sentiment} score={article.sentiment_score} />
                {article.primary_provider ? (
                  <span className="rounded-full border border-cyan-300/15 bg-cyan-300/10 px-3 py-1 text-[10px] uppercase tracking-[0.24em] text-cyan-100/80">
                    {titleCase(article.primary_provider)}
                  </span>
                ) : null}
              </div>
              <h1 className="mt-8 text-balance font-editorial text-5xl font-semibold leading-[0.98] text-white sm:text-6xl lg:text-7xl">
                {article.title}
              </h1>
              <p className="mx-auto mt-6 max-w-3xl text-base leading-8 text-white/58 sm:text-lg">
                {leadSummary || "A full on-platform article view with source context, enrichment metadata, and readable long-form formatting."}
              </p>
              <div className="mt-8 flex flex-wrap items-center justify-center gap-4 text-xs uppercase tracking-[0.22em] text-white/42">
                <span>{article.source_name || "DUBNEWSAI"}</span>
                <span>{formatDateTime(article.published_at)}</span>
                <span>{readTime} min read</span>
                <span>{article.view_count} views</span>
              </div>
            </div>
          </div>
        }
      >
        {article.image_url ? (
          <Image
            src={article.image_url}
            alt={article.title}
            height={1200}
            width={1600}
            className="mx-auto h-full w-full rounded-2xl object-cover object-center"
            priority
          />
        ) : (
          <div className="relative flex h-full w-full items-end overflow-hidden rounded-2xl bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.24),transparent_26%),radial-gradient(circle_at_bottom_right,rgba(245,158,11,0.2),transparent_22%),linear-gradient(135deg,#090d14,#06080c)] p-8 md:p-10">
            <div className="absolute inset-0 opacity-25 [background-image:linear-gradient(rgba(255,255,255,0.06)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.06)_1px,transparent_1px)] [background-size:32px_32px]" />
            <div className="relative max-w-2xl">
              <div className="story-kicker">On-platform brief</div>
              <h2 className="mt-4 text-3xl font-semibold leading-tight text-white md:text-4xl">
                Read the story here first, then decide if you need the original publisher.
              </h2>
              <p className="mt-4 text-base leading-8 text-white/62">
                {leadSummary || article.content || "This article is available in DUBNEWSAI with full metadata, source provenance, and enrichment context."}
              </p>
            </div>
          </div>
        )}
      </ContainerScroll>

      <div className="mx-auto max-w-7xl px-4 pb-20 sm:px-6 lg:px-8">
        <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_320px]">
          <article className="panel-deep p-8 lg:p-10">
            {leadSummary ? (
              <div className="rounded-[1.8rem] border border-white/10 bg-white/[0.04] p-6">
                <div className="story-kicker">Executive take</div>
                <p className="mt-4 font-editorial text-[1.3rem] leading-9 text-white/86">{leadSummary}</p>
              </div>
            ) : null}

            <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {storyFacts.map((fact) => (
                <StoryFact key={fact.label} label={fact.label} value={fact.value} />
              ))}
            </div>

            <div className="mt-8 space-y-6">
              {contentBlocks.length ? (
                contentBlocks.map((block, index) => (
                  <p key={`${article.id}-block-${index}`} className="reading-body">
                    {block}
                  </p>
                ))
              ) : (
                <p className="reading-body">
                  No long-form content is available for this article yet.
                </p>
              )}
            </div>

            {article.keywords?.length ? (
              <div className="mt-10">
                <div className="story-kicker">Keywords</div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {article.keywords.map((keyword) => (
                    <span key={keyword} className="rounded-full border border-white/10 bg-white/[0.04] px-3 py-2 text-xs text-white/68">
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}

            {entityGroups.length ? (
              <div className="mt-10 grid gap-4 md:grid-cols-2">
                {entityGroups.map(([group, values]) => (
                  <div key={group} className="rounded-[1.6rem] border border-white/10 bg-white/[0.04] p-5">
                    <div className="story-kicker">{titleCase(group)}</div>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {values.map((value) => (
                        <span key={`${group}-${value}`} className="rounded-full border border-white/10 px-3 py-1.5 text-xs text-white/72">
                          {value}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
          </article>

          <aside className="space-y-4 xl:sticky xl:top-28 xl:self-start">
            <div className="panel-deep p-5">
              <div className="story-kicker">Story signal</div>
              <div className="mt-5 space-y-4 text-sm text-white/72">
                <InfoRow label="Source" value={article.source_name || "DUBNEWSAI"} />
                <InfoRow label="Author" value={article.author || "Not provided"} />
                <InfoRow label="Published" value={formatDateTime(article.published_at)} />
                <InfoRow label="Views" value={`${article.view_count}`} />
                <InfoRow label="Read time" value={`${readTime} min`} />
              </div>
            </div>

            <div className="panel-deep p-5">
              <div className="story-kicker">Enrichment</div>
              <div className="mt-5 space-y-4 text-sm text-white/72">
                <InfoRow label="Quality" value={article.quality_score !== undefined ? `${Math.round(article.quality_score)}%` : "N/A"} />
                <InfoRow label="Relevance" value={article.relevance_score !== undefined ? `${Math.round(article.relevance_score)}%` : "N/A"} />
                <InfoRow label="Coverage" value={article.duplicate_count && article.duplicate_count > 1 ? `${article.duplicate_count} sources` : "Single source"} />
                <InfoRow label="Status" value={article.enrichment_status ? titleCase(article.enrichment_status) : "Completed"} />
              </div>
            </div>

            <div className="panel-deep p-5">
              <div className="story-kicker">Why this page exists</div>
              <p className="mt-4 text-sm leading-7 text-white/58">
                The user should understand the story, the source strength, and the reason it matters before leaving DUBNEWSAI.
              </p>
              <div className="mt-5 flex flex-wrap gap-2">
                <div className="inline-flex items-center gap-2 rounded-full border border-white/10 px-3 py-2 text-xs text-white/68">
                  <ScanSearch className="h-3.5 w-3.5 text-cyan-200" />
                  Source context
                </div>
                <div className="inline-flex items-center gap-2 rounded-full border border-white/10 px-3 py-2 text-xs text-white/68">
                  <Layers3 className="h-3.5 w-3.5 text-amber-200" />
                  Match coverage
                </div>
                <div className="inline-flex items-center gap-2 rounded-full border border-white/10 px-3 py-2 text-xs text-white/68">
                  <Eye className="h-3.5 w-3.5 text-emerald-200" />
                  Readable on-platform
                </div>
              </div>
              {article.url ? (
                <Link
                  href={article.url}
                  target="_blank"
                  className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-full bg-white px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-white/92"
                >
                  Open original source
                  <Link2 className="h-4 w-4" />
                </Link>
              ) : null}
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}

function StoryFact({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1.4rem] border border-white/10 bg-white/[0.03] p-4">
      <div className="text-[10px] uppercase tracking-[0.28em] text-white/38">{label}</div>
      <div className="mt-3 text-sm font-medium text-white/84">{value}</div>
    </div>
  )
}
function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-white/8 pb-3 last:border-b-0 last:pb-0">
      <span className="text-[10px] uppercase tracking-[0.28em] text-white/38">{label}</span>
      <span className="max-w-[60%] text-right text-sm text-white/82">{value}</span>
    </div>
  )
}




