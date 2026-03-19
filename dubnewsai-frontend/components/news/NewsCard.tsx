"use client"

import { motion } from "framer-motion"
import { Clock, Eye, Layers3 } from "lucide-react"
import { formatDistanceToNow } from "date-fns"
import Image from "next/image"
import Link from "next/link"

import { SentimentBadge } from "./SentimentBadge"
import type { NewsArticle } from "@/types"
import { titleCase } from "@/lib/utils/formatters"

export function NewsCard({
  article,
  featured = false
}: {
  article: NewsArticle
  featured?: boolean
}) {
  return (
    <motion.article
      whileHover={{ y: -4 }}
      className={`group relative overflow-hidden rounded-3xl border border-white/10 bg-white shadow-xl shadow-slate-950/5 dark:bg-slate-900 ${
        featured ? "min-h-[420px]" : ""
      }`}
    >
      <Link href={`/news/${article.id}`} className="flex h-full flex-col">
        {article.image_url ? (
          <div className={`relative w-full overflow-hidden ${featured ? "h-64" : "h-48"}`}>
            <Image
              src={article.image_url}
              alt={article.title}
              fill
              className="object-cover transition-transform duration-300 group-hover:scale-105"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-slate-950/70 via-slate-950/10 to-transparent" />
            <div className="absolute left-4 top-4 flex flex-wrap gap-2">
              <span className="rounded-full bg-gold-500 px-3 py-1 text-xs font-medium text-white shadow-lg">
                {titleCase(article.category)}
              </span>
              {article.primary_provider ? (
                <span className="rounded-full bg-cyber-500/90 px-3 py-1 text-xs font-medium text-white shadow-lg">
                  {titleCase(article.primary_provider)}
                </span>
              ) : null}
            </div>
            <div className="absolute right-4 top-4">
              <SentimentBadge sentiment={article.sentiment} score={article.sentiment_score} />
            </div>
          </div>
        ) : null}

        <div className="flex flex-1 flex-col p-6">
          {!article.image_url ? (
            <div className="mb-4 flex flex-wrap gap-2">
              <span className="rounded-full bg-gold-500/10 px-3 py-1 text-xs font-medium text-gold-600 dark:text-gold-400">
                {titleCase(article.category)}
              </span>
              {article.primary_provider ? (
                <span className="rounded-full bg-cyber-500/10 px-3 py-1 text-xs font-medium text-cyber-600 dark:text-cyber-400">
                  {titleCase(article.primary_provider)}
                </span>
              ) : null}
              <SentimentBadge sentiment={article.sentiment} score={article.sentiment_score} />
            </div>
          ) : null}

          <h3
            className={`mb-3 font-semibold text-slate-900 transition-colors group-hover:text-gold-600 dark:text-white dark:group-hover:text-gold-400 ${
              featured ? "text-2xl leading-tight" : "text-lg"
            }`}
          >
            {article.title}
          </h3>

          <p className={`text-slate-600 dark:text-slate-400 ${featured ? "line-clamp-4 text-base" : "line-clamp-3 text-sm"}`}>
            {article.description || article.content || "No description available for this article yet."}
          </p>

          <div className="mt-5 flex flex-wrap gap-2">
            {article.quality_score !== undefined ? (
              <span className="rounded-full bg-slate-950/5 px-3 py-1 text-xs font-medium text-slate-600 dark:bg-white/5 dark:text-slate-300">
                Quality {Math.round(article.quality_score)}%
              </span>
            ) : null}
            {article.duplicate_count && article.duplicate_count > 1 ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-600 dark:text-emerald-400">
                <Layers3 className="h-3 w-3" />
                {article.duplicate_count} sources
              </span>
            ) : null}
            {article.source_name ? (
              <span className="rounded-full bg-slate-950/5 px-3 py-1 text-xs font-medium text-slate-600 dark:bg-white/5 dark:text-slate-300">
                {article.source_name}
              </span>
            ) : null}
          </div>

          <div className="mt-auto pt-5 text-xs text-slate-500 dark:text-slate-500">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {formatDistanceToNow(new Date(article.published_at), { addSuffix: true })}
                </span>
                <span className="flex items-center gap-1">
                  <Eye className="h-3 w-3" />
                  {article.view_count}
                </span>
              </div>
              {article.author ? <span className="font-medium text-slate-600 dark:text-slate-300">{article.author}</span> : null}
            </div>
          </div>
        </div>

        <div className="pointer-events-none absolute inset-0 rounded-3xl ring-2 ring-gold-500/0 transition-all duration-300 group-hover:ring-gold-500/40" />
      </Link>
    </motion.article>
  )
}
