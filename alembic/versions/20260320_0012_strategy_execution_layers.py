"""Add competitive intelligence, predictions, collaboration, and white-label tables."""

from alembic import op
import sqlalchemy as sa


revision = "20260320_0012"
down_revision = "20260320_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "competitors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("official_name", sa.String(length=300), nullable=True),
        sa.Column("industry", sa.String(length=100), nullable=True),
        sa.Column("sector", sa.String(length=100), nullable=True),
        sa.Column("headquarters", sa.String(length=200), nullable=True),
        sa.Column("ticker_symbol", sa.String(length=20), nullable=True),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("founded_year", sa.Integer(), nullable=True),
        sa.Column("employee_count", sa.Integer(), nullable=True),
        sa.Column("market_cap", sa.Float(), nullable=True),
        sa.Column("revenue_annual", sa.Float(), nullable=True),
        sa.Column("revenue_growth_rate", sa.Float(), nullable=True),
        sa.Column("profit_margin", sa.Float(), nullable=True),
        sa.Column("market_share_percent", sa.Float(), nullable=True),
        sa.Column("competitive_strength_score", sa.Float(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_analyzed", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("custom_fields", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_competitors_name", "competitors", ["name"], unique=False)
    op.create_index("ix_competitors_ticker_symbol", "competitors", ["ticker_symbol"], unique=False)

    op.create_table(
        "competitor_products",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("competitor_id", sa.Integer(), nullable=False),
        sa.Column("product_name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("pricing_model", sa.String(length=50), nullable=True),
        sa.Column("key_features", sa.JSON(), nullable=True),
        sa.Column("unique_selling_points", sa.JSON(), nullable=True),
        sa.Column("launch_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("market_reception", sa.String(length=50), nullable=True),
        sa.Column("estimated_users", sa.Integer(), nullable=True),
        sa.Column("strengths", sa.JSON(), nullable=True),
        sa.Column("weaknesses", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["competitor_id"], ["competitors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_competitor_products_competitor_id", "competitor_products", ["competitor_id"], unique=False)

    op.create_table(
        "competitor_news_mentions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("competitor_id", sa.Integer(), nullable=False),
        sa.Column("article_title", sa.String(length=500), nullable=True),
        sa.Column("article_url", sa.String(length=1000), nullable=True),
        sa.Column("source", sa.String(length=200), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("full_content", sa.Text(), nullable=True),
        sa.Column("mention_type", sa.String(length=50), nullable=True),
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("importance_score", sa.Float(), nullable=True),
        sa.Column("keywords", sa.JSON(), nullable=True),
        sa.Column("entities_mentioned", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["competitor_id"], ["competitors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_competitor_news_mentions_competitor_id", "competitor_news_mentions", ["competitor_id"], unique=False)
    op.create_index("ix_competitor_news_mentions_article_url", "competitor_news_mentions", ["article_url"], unique=False)
    op.create_index("ix_competitor_news_mentions_published_at", "competitor_news_mentions", ["published_at"], unique=False)

    op.create_table(
        "competitor_price_changes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("competitor_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("open_price", sa.Float(), nullable=True),
        sa.Column("close_price", sa.Float(), nullable=True),
        sa.Column("high_price", sa.Float(), nullable=True),
        sa.Column("low_price", sa.Float(), nullable=True),
        sa.Column("volume", sa.Integer(), nullable=True),
        sa.Column("daily_change_percent", sa.Float(), nullable=True),
        sa.Column("daily_change_amount", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["competitor_id"], ["competitors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_competitor_price_changes_competitor_id", "competitor_price_changes", ["competitor_id"], unique=False)
    op.create_index("ix_competitor_price_changes_date", "competitor_price_changes", ["date"], unique=False)

    op.create_table(
        "competitor_swot_analyses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("competitor_id", sa.Integer(), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=True),
        sa.Column("weaknesses", sa.JSON(), nullable=True),
        sa.Column("opportunities", sa.JSON(), nullable=True),
        sa.Column("threats", sa.JSON(), nullable=True),
        sa.Column("analysis_date", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("analyst_notes", sa.Text(), nullable=True),
        sa.Column("data_sources", sa.JSON(), nullable=True),
        sa.Column("competitive_position", sa.String(length=50), nullable=True),
        sa.Column("threat_level", sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(["competitor_id"], ["competitors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_competitor_swot_analyses_competitor_id", "competitor_swot_analyses", ["competitor_id"], unique=False)

    op.create_table(
        "competitive_benchmarks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("competitor_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("metric_name", sa.String(length=200), nullable=False),
        sa.Column("competitor_value", sa.Float(), nullable=True),
        sa.Column("our_value", sa.Float(), nullable=True),
        sa.Column("industry_average", sa.Float(), nullable=True),
        sa.Column("performance_vs_competitor", sa.String(length=20), nullable=True),
        sa.Column("gap_percentage", sa.Float(), nullable=True),
        sa.Column("benchmark_date", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("data_source", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(["competitor_id"], ["competitors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_competitive_benchmarks_competitor_id", "competitive_benchmarks", ["competitor_id"], unique=False)

    op.create_table(
        "market_intelligence_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("report_title", sa.String(length=300), nullable=False),
        sa.Column("report_type", sa.String(length=50), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("key_findings", sa.JSON(), nullable=True),
        sa.Column("recommendations", sa.JSON(), nullable=True),
        sa.Column("market_size", sa.Float(), nullable=True),
        sa.Column("market_growth_rate", sa.Float(), nullable=True),
        sa.Column("market_trends", sa.JSON(), nullable=True),
        sa.Column("top_players", sa.JSON(), nullable=True),
        sa.Column("market_concentration", sa.Float(), nullable=True),
        sa.Column("reporting_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reporting_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data_sources", sa.JSON(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("max_members", sa.Integer(), server_default="10", nullable=False),
        sa.Column("shared_portfolios", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("shared_watchlists", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("shared_insights", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_teams_owner_id", "teams", ["owner_id"], unique=False)

    op.create_table(
        "team_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=50), server_default="member", nullable=False),
        sa.Column("can_edit", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("can_share", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("can_delete", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("team_id", "user_id", name="uq_team_user"),
    )
    op.create_index("ix_team_members_team_id", "team_members", ["team_id"], unique=False)
    op.create_index("ix_team_members_user_id", "team_members", ["user_id"], unique=False)

    op.create_table(
        "shared_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("shared_by_user_id", sa.Integer(), nullable=False),
        sa.Column("item_type", sa.String(length=50), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("item_name", sa.String(length=200), nullable=True),
        sa.Column("can_edit", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("can_comment", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("shared_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["shared_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_shared_items_team_id", "shared_items", ["team_id"], unique=False)
    op.create_index("ix_shared_items_shared_by_user_id", "shared_items", ["shared_by_user_id"], unique=False)

    op.create_table(
        "item_comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("shared_item_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("comment_text", sa.Text(), nullable=False),
        sa.Column("parent_comment_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["parent_comment_id"], ["item_comments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shared_item_id"], ["shared_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_item_comments_shared_item_id", "item_comments", ["shared_item_id"], unique=False)
    op.create_index("ix_item_comments_user_id", "item_comments", ["user_id"], unique=False)

    op.create_table(
        "team_activity",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("activity_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_team_activity_team_id", "team_activity", ["team_id"], unique=False)
    op.create_index("ix_team_activity_user_id", "team_activity", ["user_id"], unique=False)

    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("rate_limit_per_hour", sa.Integer(), server_default="100", nullable=False),
        sa.Column("total_requests", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scopes", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash"),
    )
    op.create_index("ix_api_keys_user_id", "api_keys", ["user_id"], unique=False)
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"], unique=False)

    op.create_table(
        "webhooks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("api_key_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("events", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.ForeignKeyConstraint(["api_key_id"], ["api_keys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_webhooks_api_key_id", "webhooks", ["api_key_id"], unique=False)

    op.create_table(
        "white_label_configs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(length=200), nullable=False),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("primary_color", sa.String(length=7), nullable=True),
        sa.Column("secondary_color", sa.String(length=7), nullable=True),
        sa.Column("custom_domain", sa.String(length=200), nullable=True),
        sa.Column("subdomain", sa.String(length=100), nullable=True),
        sa.Column("enabled_features", sa.JSON(), nullable=True),
        sa.Column("api_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("api_rate_limit", sa.Integer(), server_default="100", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("custom_domain"),
        sa.UniqueConstraint("subdomain"),
    )
    op.create_index("ix_white_label_configs_user_id", "white_label_configs", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_white_label_configs_user_id", table_name="white_label_configs")
    op.drop_table("white_label_configs")
    op.drop_index("ix_webhooks_api_key_id", table_name="webhooks")
    op.drop_table("webhooks")
    op.drop_index("ix_api_keys_key_hash", table_name="api_keys")
    op.drop_index("ix_api_keys_user_id", table_name="api_keys")
    op.drop_table("api_keys")
    op.drop_index("ix_team_activity_user_id", table_name="team_activity")
    op.drop_index("ix_team_activity_team_id", table_name="team_activity")
    op.drop_table("team_activity")
    op.drop_index("ix_item_comments_user_id", table_name="item_comments")
    op.drop_index("ix_item_comments_shared_item_id", table_name="item_comments")
    op.drop_table("item_comments")
    op.drop_index("ix_shared_items_shared_by_user_id", table_name="shared_items")
    op.drop_index("ix_shared_items_team_id", table_name="shared_items")
    op.drop_table("shared_items")
    op.drop_index("ix_team_members_user_id", table_name="team_members")
    op.drop_index("ix_team_members_team_id", table_name="team_members")
    op.drop_table("team_members")
    op.drop_index("ix_teams_owner_id", table_name="teams")
    op.drop_table("teams")
    op.drop_table("market_intelligence_reports")
    op.drop_index("ix_competitive_benchmarks_competitor_id", table_name="competitive_benchmarks")
    op.drop_table("competitive_benchmarks")
    op.drop_index("ix_competitor_swot_analyses_competitor_id", table_name="competitor_swot_analyses")
    op.drop_table("competitor_swot_analyses")
    op.drop_index("ix_competitor_price_changes_date", table_name="competitor_price_changes")
    op.drop_index("ix_competitor_price_changes_competitor_id", table_name="competitor_price_changes")
    op.drop_table("competitor_price_changes")
    op.drop_index("ix_competitor_news_mentions_published_at", table_name="competitor_news_mentions")
    op.drop_index("ix_competitor_news_mentions_article_url", table_name="competitor_news_mentions")
    op.drop_index("ix_competitor_news_mentions_competitor_id", table_name="competitor_news_mentions")
    op.drop_table("competitor_news_mentions")
    op.drop_index("ix_competitor_products_competitor_id", table_name="competitor_products")
    op.drop_table("competitor_products")
    op.drop_index("ix_competitors_ticker_symbol", table_name="competitors")
    op.drop_index("ix_competitors_name", table_name="competitors")
    op.drop_table("competitors")
