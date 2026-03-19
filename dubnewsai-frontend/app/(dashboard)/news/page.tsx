import { NewsFeed } from "@/components/news/NewsFeed"

export default function NewsPage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.3em] text-cyber-500">News</p>
        <h1 className="text-3xl font-display font-semibold text-slate-950 dark:text-white">Market News Feed</h1>
        <p className="mt-2 max-w-3xl text-sm text-slate-500 dark:text-slate-400">
          Cross-provider Dubai, UAE, market, and property coverage with full article detail available on-platform.
        </p>
      </div>
      <NewsFeed pageSize={18} showBrowseLink={false} />
    </div>
  )
}
