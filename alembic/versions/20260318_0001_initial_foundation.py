"""Initial DUBNEWSAI foundation schema."""

from alembic import op
import sqlalchemy as sa

from app.models.news import SentimentLabel
from app.models.user import UserRole

# revision identifiers, used by Alembic.
revision = "20260318_0001"
down_revision = None
branch_labels = None
depends_on = None


user_role_enum = sa.Enum(
    UserRole,
    name="user_role",
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("role", user_role_enum, nullable=False, server_default="user"),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "alerts",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("alert_type", sa.String(length=50), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_alerts_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alerts")),
    )
    op.create_index(op.f("ix_alerts_id"), "alerts", ["id"], unique=False)

    op.create_table(
        "market_data",
        sa.Column("area_name", sa.String(length=150), nullable=False),
        sa.Column("metric_name", sa.String(length=150), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("source_name", sa.String(length=120), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("extra_data", sa.JSON(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_market_data")),
    )
    op.create_index(op.f("ix_market_data_area_name"), "market_data", ["area_name"], unique=False)
    op.create_index(op.f("ix_market_data_id"), "market_data", ["id"], unique=False)
    op.create_index(op.f("ix_market_data_metric_name"), "market_data", ["metric_name"], unique=False)

    op.create_table(
        "news_articles",
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("source_name", sa.String(length=120), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sentiment_score", sa.Float(), nullable=True),
        sa.Column("sentiment_label", sa.Enum(SentimentLabel, name="sentiment_label"), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("author_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], name=op.f("fk_news_articles_author_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_news_articles")),
        sa.UniqueConstraint("slug", name=op.f("uq_news_articles_slug")),
    )
    op.create_index(op.f("ix_news_articles_id"), "news_articles", ["id"], unique=False)
    op.create_index(op.f("ix_news_articles_slug"), "news_articles", ["slug"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_news_articles_slug"), table_name="news_articles")
    op.drop_index(op.f("ix_news_articles_id"), table_name="news_articles")
    op.drop_table("news_articles")

    op.drop_index(op.f("ix_market_data_metric_name"), table_name="market_data")
    op.drop_index(op.f("ix_market_data_id"), table_name="market_data")
    op.drop_index(op.f("ix_market_data_area_name"), table_name="market_data")
    op.drop_table("market_data")

    op.drop_index(op.f("ix_alerts_id"), table_name="alerts")
    op.drop_table("alerts")

    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
