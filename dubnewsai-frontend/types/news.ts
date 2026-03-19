export interface NewsArticle {
  id: number
  title: string
  description: string | null
  content?: string | null
  url?: string
  image_url?: string | null
  published_at: string
  sentiment: string
  sentiment_score: number
  source_name: string | null
  source?: string
  author?: string | null
  category: string
  primary_provider?: string | null
  duplicate_count?: number
  quality_score?: number
  view_count: number
  relevance_score: number
  keywords?: string[] | null
  entities?: Record<string, string[]> | null
  is_featured?: boolean
  is_published?: boolean
  enrichment_status?: string | null
  enriched_at?: string | null
  created_at?: string
  updated_at?: string
}

export interface NewsListResponse {
  total: number
  page: number
  page_size: number
  articles: NewsArticle[]
}
