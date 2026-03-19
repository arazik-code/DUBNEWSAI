"""Restructure news schema for aggregation workflows."""

import hashlib
import json
from collections import OrderedDict

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260318_0003"
down_revision = "20260318_0002"
branch_labels = None
depends_on = None


def _deserialize_tags(raw_value) -> list[str]:
    if raw_value is None:
        return []
    if isinstance(raw_value, list):
        return [str(item).strip().lower() for item in raw_value if str(item).strip()]
    if isinstance(raw_value, str):
        try:
            parsed = json.loads(raw_value)
            if isinstance(parsed, list):
                return [str(item).strip().lower() for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            pass
    return []


def upgrade() -> None:
    connection = op.get_bind()
    news_source_enum = sa.Enum(
        "newsapi",
        "rss_gulf_news",
        "rss_the_national",
        "rss_khaleej_times",
        "rss_arabian_business",
        "rapid_api",
        "twitter",
        "manual",
        name="news_source",
    )
    news_category_enum = sa.Enum(
        "real_estate",
        "market",
        "economy",
        "regulation",
        "development",
        "infrastructure",
        "general",
        name="news_category",
    )
    news_sentiment_enum = sa.Enum("positive", "neutral", "negative", name="news_sentiment")

    if connection.dialect.name == "postgresql":
        news_source_enum.create(connection, checkfirst=True)
        news_category_enum.create(connection, checkfirst=True)
        news_sentiment_enum.create(connection, checkfirst=True)

    op.drop_index(op.f("ix_news_articles_slug"), table_name="news_articles")
    op.drop_index(op.f("ix_news_articles_id"), table_name="news_articles")
    op.rename_table("news_articles", "news_articles_legacy")

    # PostgreSQL keeps underlying constraint/index names after a table rename.
    # Rename legacy objects out of the way so the rebuilt table can reuse the
    # canonical names expected by later migrations and the ORM metadata.
    if connection.dialect.name == "postgresql":
        op.execute("ALTER TABLE news_articles_legacy RENAME CONSTRAINT pk_news_articles TO pk_news_articles_legacy")
        op.execute(
            "ALTER TABLE news_articles_legacy RENAME CONSTRAINT uq_news_articles_slug TO uq_news_articles_slug_legacy"
        )
        op.execute(
            "ALTER TABLE news_articles_legacy RENAME CONSTRAINT fk_news_articles_author_id_users "
            "TO fk_news_articles_author_id_users_legacy"
        )
        op.execute("ALTER SEQUENCE IF EXISTS news_articles_id_seq RENAME TO news_articles_legacy_id_seq")

    op.create_table(
        "news_articles",
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("url_hash", sa.String(length=64), nullable=False),
        sa.Column("source", news_source_enum, nullable=False),
        sa.Column("source_name", sa.String(length=200), nullable=True),
        sa.Column("author", sa.String(length=200), nullable=True),
        sa.Column("category", news_category_enum, nullable=False, server_default="general"),
        sa.Column("sentiment", news_sentiment_enum, nullable=False, server_default="neutral"),
        sa.Column("sentiment_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("keywords", sa.JSON(), nullable=True),
        sa.Column("entities", sa.JSON(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("relevance_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("image_url", sa.String(length=1000), nullable=True),
        sa.Column("video_url", sa.String(length=1000), nullable=True),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_news_articles")),
        sa.UniqueConstraint("url", name=op.f("uq_news_articles_url")),
        sa.UniqueConstraint("url_hash", name=op.f("uq_news_articles_url_hash")),
    )
    op.create_index(op.f("ix_news_articles_id"), "news_articles", ["id"], unique=False)
    op.create_index(op.f("ix_news_articles_title"), "news_articles", ["title"], unique=False)
    op.create_index(op.f("ix_news_articles_url"), "news_articles", ["url"], unique=False)
    op.create_index(op.f("ix_news_articles_url_hash"), "news_articles", ["url_hash"], unique=False)
    op.create_index(op.f("ix_news_articles_source"), "news_articles", ["source"], unique=False)
    op.create_index(op.f("ix_news_articles_category"), "news_articles", ["category"], unique=False)
    op.create_index(op.f("ix_news_articles_sentiment"), "news_articles", ["sentiment"], unique=False)
    op.create_index(op.f("ix_news_articles_published_at"), "news_articles", ["published_at"], unique=False)
    op.create_index(op.f("ix_news_articles_is_published"), "news_articles", ["is_published"], unique=False)
    op.create_index("idx_published_category", "news_articles", ["published_at", "category"], unique=False)
    op.create_index("idx_source_published", "news_articles", ["source", "published_at"], unique=False)

    op.create_table(
        "news_tags",
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_news_tags")),
        sa.UniqueConstraint("name", name=op.f("uq_news_tags_name")),
        sa.UniqueConstraint("slug", name=op.f("uq_news_tags_slug")),
    )
    op.create_index(op.f("ix_news_tags_id"), "news_tags", ["id"], unique=False)
    op.create_index(op.f("ix_news_tags_name"), "news_tags", ["name"], unique=False)

    op.create_table(
        "news_article_tags",
        sa.Column("article_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["article_id"], ["news_articles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["news_tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("article_id", "tag_id", name="pk_news_article_tags"),
    )

    legacy_rows = connection.execute(
        sa.text(
            """
            SELECT id, title, summary, content, source_name, source_url, published_at,
                   sentiment_score, sentiment_label, tags, raw_payload, created_at, updated_at
            FROM news_articles_legacy
            """
        )
    ).mappings().all()

    article_table = sa.table(
        "news_articles",
        sa.column("id", sa.Integer),
        sa.column("title", sa.String),
        sa.column("description", sa.Text),
        sa.column("content", sa.Text),
        sa.column("url", sa.String),
        sa.column("url_hash", sa.String),
        sa.column("source", sa.String),
        sa.column("source_name", sa.String),
        sa.column("author", sa.String),
        sa.column("category", sa.String),
        sa.column("sentiment", sa.String),
        sa.column("sentiment_score", sa.Integer),
        sa.column("keywords", sa.JSON),
        sa.column("entities", sa.JSON),
        sa.column("published_at", sa.DateTime(timezone=True)),
        sa.column("view_count", sa.Integer),
        sa.column("relevance_score", sa.Integer),
        sa.column("image_url", sa.String),
        sa.column("video_url", sa.String),
        sa.column("is_featured", sa.Boolean),
        sa.column("is_published", sa.Boolean),
        sa.column("raw_payload", sa.JSON),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    tag_table = sa.table(
        "news_tags",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("slug", sa.String),
        sa.column("count", sa.Integer),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    association_table = sa.table(
        "news_article_tags",
        sa.column("article_id", sa.Integer),
        sa.column("tag_id", sa.Integer),
    )

    article_rows = []
    tag_lookup: OrderedDict[str, dict] = OrderedDict()
    association_rows = []

    for legacy_row in legacy_rows:
        url = legacy_row["source_url"]
        if not url:
            continue

        keywords = _deserialize_tags(legacy_row["tags"])
        sentiment = legacy_row["sentiment_label"] or "neutral"
        article_rows.append(
            {
                "id": legacy_row["id"],
                "title": legacy_row["title"],
                "description": legacy_row["summary"],
                "content": legacy_row["content"],
                "url": url,
                "url_hash": hashlib.sha256(url.encode("utf-8")).hexdigest(),
                "source": "manual",
                "source_name": legacy_row["source_name"],
                "author": None,
                "category": "general",
                "sentiment": sentiment,
                "sentiment_score": int(legacy_row["sentiment_score"] or 0),
                "keywords": keywords or None,
                "entities": None,
                "published_at": legacy_row["published_at"],
                "view_count": 0,
                "relevance_score": 0,
                "image_url": None,
                "video_url": None,
                "is_featured": False,
                "is_published": True,
                "raw_payload": legacy_row["raw_payload"],
                "created_at": legacy_row["created_at"],
                "updated_at": legacy_row["updated_at"],
            }
        )

        for keyword in keywords:
            if keyword not in tag_lookup:
                tag_lookup[keyword] = {
                    "id": len(tag_lookup) + 1,
                    "name": keyword,
                    "slug": keyword.replace(" ", "-"),
                    "count": 0,
                    "created_at": legacy_row["created_at"],
                    "updated_at": legacy_row["updated_at"],
                }
            tag_lookup[keyword]["count"] += 1
            association_rows.append({"article_id": legacy_row["id"], "tag_id": tag_lookup[keyword]["id"]})

    if article_rows:
        op.bulk_insert(article_table, article_rows)
    if tag_lookup:
        op.bulk_insert(tag_table, list(tag_lookup.values()))
    if association_rows:
        op.bulk_insert(association_table, association_rows)

    op.drop_table("news_articles_legacy")


def downgrade() -> None:
    op.drop_table("news_article_tags")
    op.drop_index(op.f("ix_news_tags_name"), table_name="news_tags")
    op.drop_index(op.f("ix_news_tags_id"), table_name="news_tags")
    op.drop_table("news_tags")
    op.drop_index("idx_source_published", table_name="news_articles")
    op.drop_index("idx_published_category", table_name="news_articles")
    op.drop_index(op.f("ix_news_articles_is_published"), table_name="news_articles")
    op.drop_index(op.f("ix_news_articles_published_at"), table_name="news_articles")
    op.drop_index(op.f("ix_news_articles_sentiment"), table_name="news_articles")
    op.drop_index(op.f("ix_news_articles_category"), table_name="news_articles")
    op.drop_index(op.f("ix_news_articles_source"), table_name="news_articles")
    op.drop_index(op.f("ix_news_articles_url_hash"), table_name="news_articles")
    op.drop_index(op.f("ix_news_articles_url"), table_name="news_articles")
    op.drop_index(op.f("ix_news_articles_title"), table_name="news_articles")
    op.drop_index(op.f("ix_news_articles_id"), table_name="news_articles")
    op.drop_table("news_articles")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        sa.Enum("positive", "neutral", "negative", name="news_sentiment").drop(bind, checkfirst=True)
        sa.Enum(
            "real_estate",
            "market",
            "economy",
            "regulation",
            "development",
            "infrastructure",
            "general",
            name="news_category",
        ).drop(bind, checkfirst=True)
        sa.Enum(
            "newsapi",
            "rss_gulf_news",
            "rss_the_national",
            "rss_khaleej_times",
            "rss_arabian_business",
            "rapid_api",
            "twitter",
            "manual",
            name="news_source",
        ).drop(bind, checkfirst=True)
