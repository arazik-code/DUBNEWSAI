"""Restructure market data for financial integration."""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260318_0004"
down_revision = "20260318_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    market_type_enum = sa.Enum("stock", "index", "currency", "commodity", "crypto", name="market_type")
    stock_exchange_enum = sa.Enum("dfm", "adx", "nasdaq", "nyse", name="stock_exchange")

    if connection.dialect.name == "postgresql":
        market_type_enum.create(connection, checkfirst=True)
        stock_exchange_enum.create(connection, checkfirst=True)

    op.drop_index(op.f("ix_market_data_metric_name"), table_name="market_data")
    op.drop_index(op.f("ix_market_data_id"), table_name="market_data")
    op.drop_index(op.f("ix_market_data_area_name"), table_name="market_data")
    op.rename_table("market_data", "market_data_legacy")

    if connection.dialect.name == "postgresql":
        op.execute("ALTER TABLE market_data_legacy RENAME CONSTRAINT pk_market_data TO pk_market_data_legacy")
        op.execute("ALTER SEQUENCE IF EXISTS market_data_id_seq RENAME TO market_data_legacy_id_seq")

    op.create_table(
        "market_data",
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("market_type", market_type_enum, nullable=False),
        sa.Column("exchange", stock_exchange_enum, nullable=True),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("open_price", sa.Float(), nullable=True),
        sa.Column("high_price", sa.Float(), nullable=True),
        sa.Column("low_price", sa.Float(), nullable=True),
        sa.Column("close_price", sa.Float(), nullable=True),
        sa.Column("previous_close", sa.Float(), nullable=True),
        sa.Column("volume", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("market_cap", sa.Float(), nullable=True),
        sa.Column("change", sa.Float(), nullable=False, server_default="0"),
        sa.Column("change_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="AED"),
        sa.Column("data_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("pe_ratio", sa.Float(), nullable=True),
        sa.Column("dividend_yield", sa.Float(), nullable=True),
        sa.Column("week_52_high", sa.Float(), nullable=True),
        sa.Column("week_52_low", sa.Float(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_market_data")),
    )
    op.create_index(op.f("ix_market_data_id"), "market_data", ["id"], unique=False)
    op.create_index(op.f("ix_market_data_symbol"), "market_data", ["symbol"], unique=False)
    op.create_index(op.f("ix_market_data_market_type"), "market_data", ["market_type"], unique=False)
    op.create_index(op.f("ix_market_data_data_timestamp"), "market_data", ["data_timestamp"], unique=False)
    op.create_index("idx_symbol_timestamp", "market_data", ["symbol", "data_timestamp"], unique=False)
    op.create_index("idx_type_timestamp", "market_data", ["market_type", "data_timestamp"], unique=False)

    op.create_table(
        "currency_rates",
        sa.Column("from_currency", sa.String(length=3), nullable=False),
        sa.Column("to_currency", sa.String(length=3), nullable=False),
        sa.Column("rate", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_currency_rates")),
    )
    op.create_index(op.f("ix_currency_rates_id"), "currency_rates", ["id"], unique=False)
    op.create_index(op.f("ix_currency_rates_from_currency"), "currency_rates", ["from_currency"], unique=False)
    op.create_index(op.f("ix_currency_rates_to_currency"), "currency_rates", ["to_currency"], unique=False)
    op.create_index(op.f("ix_currency_rates_timestamp"), "currency_rates", ["timestamp"], unique=False)
    op.create_index("idx_currency_pair", "currency_rates", ["from_currency", "to_currency", "timestamp"], unique=False)

    op.create_table(
        "economic_indicators",
        sa.Column("indicator_name", sa.String(length=200), nullable=False),
        sa.Column("indicator_code", sa.String(length=50), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("country", sa.String(length=3), nullable=False, server_default="UAE"),
        sa.Column("period", sa.String(length=20), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_economic_indicators")),
    )
    op.create_index(op.f("ix_economic_indicators_id"), "economic_indicators", ["id"], unique=False)
    op.create_index(op.f("ix_economic_indicators_indicator_name"), "economic_indicators", ["indicator_name"], unique=False)
    op.create_index(op.f("ix_economic_indicators_indicator_code"), "economic_indicators", ["indicator_code"], unique=False)
    op.create_index(op.f("ix_economic_indicators_timestamp"), "economic_indicators", ["timestamp"], unique=False)

    op.create_table(
        "watchlist_symbols",
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("market_type", market_type_enum, nullable=False),
        sa.Column("exchange", stock_exchange_enum, nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_real_estate_company", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_watchlist_symbols")),
    )
    op.create_index(op.f("ix_watchlist_symbols_id"), "watchlist_symbols", ["id"], unique=False)
    op.create_index(op.f("ix_watchlist_symbols_symbol"), "watchlist_symbols", ["symbol"], unique=False)

    legacy_rows = connection.execute(
        sa.text(
            """
            SELECT metric_name, metric_value, unit, source_name, recorded_at, extra_data, created_at, updated_at
            FROM market_data_legacy
            """
        )
    ).mappings().all()

    if legacy_rows:
        indicator_table = sa.table(
            "economic_indicators",
            sa.column("indicator_name", sa.String),
            sa.column("indicator_code", sa.String),
            sa.column("value", sa.Float),
            sa.column("unit", sa.String),
            sa.column("country", sa.String),
            sa.column("period", sa.String),
            sa.column("timestamp", sa.DateTime(timezone=True)),
            sa.column("source", sa.String),
            sa.column("description", sa.String),
            sa.column("created_at", sa.DateTime(timezone=True)),
            sa.column("updated_at", sa.DateTime(timezone=True)),
        )
        op.bulk_insert(
            indicator_table,
            [
                {
                    "indicator_name": row["metric_name"],
                    "indicator_code": row["metric_name"].lower().replace(" ", "_"),
                    "value": row["metric_value"],
                    "unit": row["unit"],
                    "country": "UAE",
                    "period": None,
                    "timestamp": row["recorded_at"],
                    "source": row["source_name"],
                    "description": str(row["extra_data"])[:500] if row["extra_data"] is not None else None,
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }
                for row in legacy_rows
            ],
        )

    op.drop_table("market_data_legacy")


def downgrade() -> None:
    op.drop_index(op.f("ix_watchlist_symbols_symbol"), table_name="watchlist_symbols")
    op.drop_index(op.f("ix_watchlist_symbols_id"), table_name="watchlist_symbols")
    op.drop_table("watchlist_symbols")

    op.drop_index(op.f("ix_economic_indicators_timestamp"), table_name="economic_indicators")
    op.drop_index(op.f("ix_economic_indicators_indicator_code"), table_name="economic_indicators")
    op.drop_index(op.f("ix_economic_indicators_indicator_name"), table_name="economic_indicators")
    op.drop_index(op.f("ix_economic_indicators_id"), table_name="economic_indicators")
    op.drop_table("economic_indicators")

    op.drop_index("idx_currency_pair", table_name="currency_rates")
    op.drop_index(op.f("ix_currency_rates_timestamp"), table_name="currency_rates")
    op.drop_index(op.f("ix_currency_rates_to_currency"), table_name="currency_rates")
    op.drop_index(op.f("ix_currency_rates_from_currency"), table_name="currency_rates")
    op.drop_index(op.f("ix_currency_rates_id"), table_name="currency_rates")
    op.drop_table("currency_rates")

    op.drop_index("idx_type_timestamp", table_name="market_data")
    op.drop_index("idx_symbol_timestamp", table_name="market_data")
    op.drop_index(op.f("ix_market_data_data_timestamp"), table_name="market_data")
    op.drop_index(op.f("ix_market_data_market_type"), table_name="market_data")
    op.drop_index(op.f("ix_market_data_symbol"), table_name="market_data")
    op.drop_index(op.f("ix_market_data_id"), table_name="market_data")
    op.drop_table("market_data")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        sa.Enum("dfm", "adx", "nasdaq", "nyse", name="stock_exchange").drop(bind, checkfirst=True)
        sa.Enum("stock", "index", "currency", "commodity", "crypto", name="market_type").drop(bind, checkfirst=True)
