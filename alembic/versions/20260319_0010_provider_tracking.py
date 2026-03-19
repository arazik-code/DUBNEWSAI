"""Add provider tracking and source attribution tables."""

from alembic import op
import sqlalchemy as sa


revision = "20260319_0010"
down_revision = "20260318_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "data_providers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.Integer(), server_default="3", nullable=False),
        sa.Column("rate_limit_per_day", sa.Integer(), nullable=True),
        sa.Column("cost_per_call", sa.Float(), server_default="0", nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_healthy", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("reliability_score", sa.Float(), server_default="100", nullable=False),
        sa.Column("total_calls", sa.Integer(), server_default="0", nullable=False),
        sa.Column("successful_calls", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_calls", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_success_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_failure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("circuit_state", sa.String(length=20), server_default="closed", nullable=False),
        sa.Column("circuit_opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("base_url", sa.String(length=500), nullable=True),
        sa.Column("timeout_seconds", sa.Integer(), server_default="30", nullable=False),
        sa.Column("retry_attempts", sa.Integer(), server_default="2", nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_data_providers_type", "data_providers", ["type"], unique=False)
    op.create_index("ix_data_providers_is_enabled", "data_providers", ["is_enabled"], unique=False)

    op.create_table(
        "provider_fetch_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("query", sa.String(length=500), nullable=True),
        sa.Column("fetch_type", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("items_fetched", sa.Integer(), server_default="0", nullable=False),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_type", sa.String(length=100), nullable=True),
        sa.Column("triggered_by", sa.String(length=50), nullable=True),
        sa.Column("task_id", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["provider_id"], ["data_providers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_provider_fetch_logs_provider_id", "provider_fetch_logs", ["provider_id"], unique=False)
    op.create_index("ix_provider_fetch_logs_status", "provider_fetch_logs", ["status"], unique=False)

    op.create_table(
        "article_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("source_title", sa.String(length=500), nullable=True),
        sa.Column("source_description", sa.Text(), nullable=True),
        sa.Column("source_quality_score", sa.Float(), nullable=True),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["news_articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["provider_id"], ["data_providers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("article_id", "provider_id", name="uq_article_sources_article_provider"),
    )
    op.create_index("ix_article_sources_article_id", "article_sources", ["article_id"], unique=False)
    op.create_index("ix_article_sources_provider_id", "article_sources", ["provider_id"], unique=False)

    op.create_table(
        "market_data_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("market_data_id", sa.Integer(), nullable=False),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("response_time_ms", sa.Integer(), nullable=True),
        sa.Column("data_completeness", sa.Float(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["market_data_id"], ["market_data.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["provider_id"], ["data_providers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("market_data_id", "provider_id", name="uq_market_data_sources_market_provider"),
    )
    op.create_index("ix_market_data_sources_market_data_id", "market_data_sources", ["market_data_id"], unique=False)
    op.create_index("ix_market_data_sources_provider_id", "market_data_sources", ["provider_id"], unique=False)

    op.add_column("news_articles", sa.Column("primary_provider", sa.String(length=100), nullable=True))
    op.add_column("news_articles", sa.Column("duplicate_count", sa.Integer(), server_default="1", nullable=False))
    op.add_column("news_articles", sa.Column("quality_score", sa.Float(), server_default="50", nullable=False))
    op.add_column("news_articles", sa.Column("enrichment_status", sa.String(length=50), server_default="pending", nullable=False))
    op.add_column("news_articles", sa.Column("enriched_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_news_articles_primary_provider", "news_articles", ["primary_provider"], unique=False)

    op.add_column("market_data", sa.Column("primary_provider", sa.String(length=100), nullable=True))
    op.add_column("market_data", sa.Column("data_quality_score", sa.Float(), nullable=True))
    op.add_column("market_data", sa.Column("confidence_level", sa.String(length=20), nullable=True))
    op.add_column("market_data", sa.Column("asset_class", sa.String(length=50), nullable=True))
    op.add_column("market_data", sa.Column("region", sa.String(length=50), nullable=True))
    op.create_index("ix_market_data_primary_provider", "market_data", ["primary_provider"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_market_data_primary_provider", table_name="market_data")
    op.drop_column("market_data", "region")
    op.drop_column("market_data", "asset_class")
    op.drop_column("market_data", "confidence_level")
    op.drop_column("market_data", "data_quality_score")
    op.drop_column("market_data", "primary_provider")

    op.drop_index("ix_news_articles_primary_provider", table_name="news_articles")
    op.drop_column("news_articles", "enriched_at")
    op.drop_column("news_articles", "enrichment_status")
    op.drop_column("news_articles", "quality_score")
    op.drop_column("news_articles", "duplicate_count")
    op.drop_column("news_articles", "primary_provider")

    op.drop_index("ix_market_data_sources_provider_id", table_name="market_data_sources")
    op.drop_index("ix_market_data_sources_market_data_id", table_name="market_data_sources")
    op.drop_table("market_data_sources")

    op.drop_index("ix_article_sources_provider_id", table_name="article_sources")
    op.drop_index("ix_article_sources_article_id", table_name="article_sources")
    op.drop_table("article_sources")

    op.drop_index("ix_provider_fetch_logs_status", table_name="provider_fetch_logs")
    op.drop_index("ix_provider_fetch_logs_provider_id", table_name="provider_fetch_logs")
    op.drop_table("provider_fetch_logs")

    op.drop_index("ix_data_providers_is_enabled", table_name="data_providers")
    op.drop_index("ix_data_providers_type", table_name="data_providers")
    op.drop_table("data_providers")
