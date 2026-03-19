"""Upgrade alerts for advanced automation workflows."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260318_0007"
down_revision = "20260318_0006"
branch_labels = None
depends_on = None


alert_type_enum = sa.Enum(
    "price_above",
    "price_below",
    "price_change_percent",
    "keyword_match",
    "sentiment_threshold",
    "volume_spike",
    "new_article_category",
    "trend_detected",
    name="alert_type",
)
alert_frequency_enum = sa.Enum("instant", "hourly", "daily", "weekly", name="alert_frequency")
alert_status_enum = sa.Enum("active", "triggered", "expired", "paused", name="alert_status")


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        alert_type_enum.create(bind, checkfirst=True)
        alert_frequency_enum.create(bind, checkfirst=True)
        alert_status_enum.create(bind, checkfirst=True)

    with op.batch_alter_table("alerts") as batch_op:
        batch_op.add_column(sa.Column("name", sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column("status", alert_status_enum, nullable=False, server_default="active"))
        batch_op.add_column(sa.Column("keywords", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("category", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("frequency", alert_frequency_enum, nullable=False, server_default="instant"))
        batch_op.add_column(sa.Column("email_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("webhook_url", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("trigger_count", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.create_index(op.f("ix_alerts_alert_type"), ["alert_type"], unique=False)
        batch_op.create_index(op.f("ix_alerts_status"), ["status"], unique=False)
        batch_op.create_index(op.f("ix_alerts_symbol"), ["symbol"], unique=False)

    alerts_table = sa.table(
        "alerts",
        sa.column("id", sa.Integer),
        sa.column("alert_type", sa.String),
        sa.column("symbol", sa.String),
        sa.column("keyword", sa.String),
        sa.column("name", sa.String),
        sa.column("keywords", sa.JSON),
    )

    valid_types = {
        "price_above",
        "price_below",
        "price_change_percent",
        "keyword_match",
        "sentiment_threshold",
        "volume_spike",
        "new_article_category",
        "trend_detected",
    }

    rows = bind.execute(
        sa.select(
            alerts_table.c.id,
            alerts_table.c.alert_type,
            alerts_table.c.symbol,
            alerts_table.c.keyword,
        )
    ).mappings().all()

    for row in rows:
        raw_type = row["alert_type"] or "keyword_match"
        mapped_type = raw_type if raw_type in valid_types else "keyword_match"
        derived_name = row["keyword"] or row["symbol"] or mapped_type.replace("_", " ").title()
        derived_keywords = [row["keyword"]] if row["keyword"] else None

        bind.execute(
            alerts_table.update()
            .where(alerts_table.c.id == row["id"])
            .values(
                alert_type=mapped_type,
                name=derived_name,
                keywords=derived_keywords,
            )
        )

    with op.batch_alter_table("alerts") as batch_op:
        batch_op.alter_column("name", existing_type=sa.String(length=200), nullable=False)
        batch_op.alter_column(
            "alert_type",
            existing_type=sa.String(length=50),
            type_=alert_type_enum,
            existing_nullable=False,
        )
        batch_op.drop_column("keyword")

    op.create_table(
        "alert_triggers",
        sa.Column("alert_id", sa.Integer(), nullable=False),
        sa.Column("trigger_data", sa.JSON(), nullable=True),
        sa.Column("message", sa.String(length=500), nullable=True),
        sa.Column("notification_sent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("email_sent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("webhook_sent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alert_triggers")),
    )
    op.create_index(op.f("ix_alert_triggers_id"), "alert_triggers", ["id"], unique=False)
    op.create_index(op.f("ix_alert_triggers_alert_id"), "alert_triggers", ["alert_id"], unique=False)

    op.create_table(
        "automations",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("trigger_type", sa.String(length=50), nullable=False),
        sa.Column("trigger_conditions", sa.JSON(), nullable=True),
        sa.Column("actions", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("execution_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_automations")),
    )
    op.create_index(op.f("ix_automations_id"), "automations", ["id"], unique=False)
    op.create_index(op.f("ix_automations_user_id"), "automations", ["user_id"], unique=False)
    op.create_index(op.f("ix_automations_is_active"), "automations", ["is_active"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_automations_is_active"), table_name="automations")
    op.drop_index(op.f("ix_automations_user_id"), table_name="automations")
    op.drop_index(op.f("ix_automations_id"), table_name="automations")
    op.drop_table("automations")

    op.drop_index(op.f("ix_alert_triggers_alert_id"), table_name="alert_triggers")
    op.drop_index(op.f("ix_alert_triggers_id"), table_name="alert_triggers")
    op.drop_table("alert_triggers")

    with op.batch_alter_table("alerts") as batch_op:
        batch_op.add_column(sa.Column("keyword", sa.String(length=200), nullable=True))

    alerts_table = sa.table(
        "alerts",
        sa.column("id", sa.Integer),
        sa.column("keywords", sa.JSON),
        sa.column("keyword", sa.String),
    )
    bind = op.get_bind()
    rows = bind.execute(sa.select(alerts_table.c.id, alerts_table.c.keywords)).mappings().all()
    for row in rows:
        keywords = row["keywords"] or []
        first_keyword = keywords[0] if isinstance(keywords, list) and keywords else None
        bind.execute(
            alerts_table.update()
            .where(alerts_table.c.id == row["id"])
            .values(keyword=first_keyword)
        )

    with op.batch_alter_table("alerts") as batch_op:
        batch_op.alter_column(
            "alert_type",
            existing_type=alert_type_enum,
            type_=sa.String(length=50),
            existing_nullable=False,
        )
        batch_op.drop_index(op.f("ix_alerts_symbol"))
        batch_op.drop_index(op.f("ix_alerts_status"))
        batch_op.drop_index(op.f("ix_alerts_alert_type"))
        batch_op.drop_column("expires_at")
        batch_op.drop_column("last_triggered_at")
        batch_op.drop_column("trigger_count")
        batch_op.drop_column("webhook_url")
        batch_op.drop_column("email_enabled")
        batch_op.drop_column("frequency")
        batch_op.drop_column("category")
        batch_op.drop_column("keywords")
        batch_op.drop_column("status")
        batch_op.drop_column("name")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        alert_status_enum.drop(bind, checkfirst=True)
        alert_frequency_enum.drop(bind, checkfirst=True)
        alert_type_enum.drop(bind, checkfirst=True)
