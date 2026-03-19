import { AuthGuard } from "@/components/auth/AuthGuard"
import { HeroSection } from "@/components/dashboard/HeroSection"
import { LiveTicker } from "@/components/dashboard/LiveTicker"
import { MarketOverview } from "@/components/dashboard/MarketOverview"
import { QuickStats } from "@/components/dashboard/QuickStats"
import { TrendingTopics } from "@/components/dashboard/TrendingTopics"
import { NewsFeed } from "@/components/news/NewsFeed"

export default function DashboardPage() {
  return (
    <AuthGuard>
      <div className="space-y-8">
        <HeroSection />
        <QuickStats />
        <LiveTicker />

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <NewsFeed pageSize={8} />
          </div>

          <div className="space-y-6">
            <MarketOverview />
            <TrendingTopics />
          </div>
        </div>
      </div>
    </AuthGuard>
  )
}
