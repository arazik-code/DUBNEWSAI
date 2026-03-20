"""Add portfolio and investor intelligence tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260320_0011"
down_revision = "20260319_0010"
branch_labels = None
depends_on = None


portfolio_type = postgresql.ENUM("stocks", "real_estate", "mixed", "watchlist", name="portfolio_type", create_type=False)
transaction_type = postgresql.ENUM("buy", "sell", "dividend", "split", name="transaction_type", create_type=False)


def upgrade() -> None:
    portfolio_type.create(op.get_bind(), checkfirst=True)
    transaction_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "portfolios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("portfolio_type", portfolio_type, server_default="mixed", nullable=False),
        sa.Column("base_currency", sa.String(length=3), server_default="AED", nullable=False),
        sa.Column("is_public", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("auto_update", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("total_value_aed", sa.Float(), server_default="0", nullable=False),
        sa.Column("total_cost_aed", sa.Float(), server_default="0", nullable=False),
        sa.Column("total_return_aed", sa.Float(), server_default="0", nullable=False),
        sa.Column("total_return_percent", sa.Float(), server_default="0", nullable=False),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_portfolios_user_id", "portfolios", ["user_id"], unique=False)

    op.create_table(
        "portfolio_holdings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=50), nullable=False),
        sa.Column("asset_type", sa.String(length=50), nullable=True),
        sa.Column("asset_name", sa.String(length=200), nullable=True),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("average_cost", sa.Float(), nullable=False),
        sa.Column("current_price", sa.Float(), nullable=True),
        sa.Column("current_value", sa.Float(), nullable=True),
        sa.Column("unrealized_gain_loss", sa.Float(), nullable=True),
        sa.Column("unrealized_gain_loss_percent", sa.Float(), nullable=True),
        sa.Column("realized_gain_loss", sa.Float(), nullable=True),
        sa.Column("total_dividends", sa.Float(), server_default="0", nullable=False),
        sa.Column("purchase_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("portfolio_id", "symbol", name="uq_portfolio_holding_symbol"),
    )
    op.create_index("ix_portfolio_holdings_portfolio_id", "portfolio_holdings", ["portfolio_id"], unique=False)
    op.create_index("ix_portfolio_holdings_symbol", "portfolio_holdings", ["symbol"], unique=False)

    op.create_table(
        "portfolio_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("holding_id", sa.Integer(), nullable=True),
        sa.Column("transaction_type", transaction_type, nullable=False),
        sa.Column("symbol", sa.String(length=50), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("fees", sa.Float(), server_default="0", nullable=False),
        sa.Column("tax", sa.Float(), server_default="0", nullable=False),
        sa.Column("transaction_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(["holding_id"], ["portfolio_holdings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_portfolio_transactions_portfolio_id", "portfolio_transactions", ["portfolio_id"], unique=False)
    op.create_index("ix_portfolio_transactions_symbol", "portfolio_transactions", ["symbol"], unique=False)

    op.create_table(
        "portfolio_performance",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("portfolio_id", sa.Integer(), nullable=False),
        sa.Column("snapshot_date", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("total_value", sa.Float(), nullable=False),
        sa.Column("total_cost", sa.Float(), nullable=False),
        sa.Column("total_return", sa.Float(), nullable=True),
        sa.Column("total_return_percent", sa.Float(), nullable=True),
        sa.Column("daily_change", sa.Float(), nullable=True),
        sa.Column("daily_change_percent", sa.Float(), nullable=True),
        sa.Column("holdings_snapshot", sa.JSON(), nullable=True),
        sa.Column("sector_allocation", sa.JSON(), nullable=True),
        sa.Column("asset_allocation", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_portfolio_performance_portfolio_id", "portfolio_performance", ["portfolio_id"], unique=False)
    op.create_index("ix_portfolio_performance_snapshot_date", "portfolio_performance", ["snapshot_date"], unique=False)
    op.create_index("idx_portfolio_snapshot", "portfolio_performance", ["portfolio_id", "snapshot_date"], unique=False)

    op.create_table(
        "watchlists",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("alert_on_change", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("change_threshold_percent", sa.Float(), server_default="5", nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_watchlists_user_id", "watchlists", ["user_id"], unique=False)

    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("watchlist_id", sa.Integer(), nullable=False),
        sa.Column("symbol", sa.String(length=50), nullable=False),
        sa.Column("asset_type", sa.String(length=50), nullable=True),
        sa.Column("asset_name", sa.String(length=200), nullable=True),
        sa.Column("target_buy_price", sa.Float(), nullable=True),
        sa.Column("target_sell_price", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("added_price", sa.Float(), nullable=True),
        sa.Column("current_price", sa.Float(), nullable=True),
        sa.Column("price_change_percent", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["watchlist_id"], ["watchlists.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("watchlist_id", "symbol", name="uq_watchlist_symbol"),
    )
    op.create_index("ix_watchlist_items_watchlist_id", "watchlist_items", ["watchlist_id"], unique=False)
    op.create_index("ix_watchlist_items_symbol", "watchlist_items", ["symbol"], unique=False)

    op.create_table(
        "investment_recommendations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("symbol", sa.String(length=50), nullable=False),
        sa.Column("asset_name", sa.String(length=200), nullable=True),
        sa.Column("recommendation_type", sa.String(length=20), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("investment_score", sa.Float(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("key_factors", sa.JSON(), nullable=True),
        sa.Column("risks", sa.JSON(), nullable=True),
        sa.Column("target_price", sa.Float(), nullable=True),
        sa.Column("stop_loss_price", sa.Float(), nullable=True),
        sa.Column("time_horizon_days", sa.Integer(), nullable=True),
        sa.Column("recommendation_date", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("price_at_recommendation", sa.Float(), nullable=True),
        sa.Column("current_price", sa.Float(), nullable=True),
        sa.Column("recommendation_return", sa.Float(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("closed_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("generated_by", sa.String(length=50), nullable=True),
        sa.Column("model_version", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_investment_recommendations_user_id", "investment_recommendations", ["user_id"], unique=False)
    op.create_index("ix_investment_recommendations_symbol", "investment_recommendations", ["symbol"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_investment_recommendations_symbol", table_name="investment_recommendations")
    op.drop_index("ix_investment_recommendations_user_id", table_name="investment_recommendations")
    op.drop_table("investment_recommendations")

    op.drop_index("ix_watchlist_items_symbol", table_name="watchlist_items")
    op.drop_index("ix_watchlist_items_watchlist_id", table_name="watchlist_items")
    op.drop_table("watchlist_items")

    op.drop_index("ix_watchlists_user_id", table_name="watchlists")
    op.drop_table("watchlists")

    op.drop_index("idx_portfolio_snapshot", table_name="portfolio_performance")
    op.drop_index("ix_portfolio_performance_snapshot_date", table_name="portfolio_performance")
    op.drop_index("ix_portfolio_performance_portfolio_id", table_name="portfolio_performance")
    op.drop_table("portfolio_performance")

    op.drop_index("ix_portfolio_transactions_symbol", table_name="portfolio_transactions")
    op.drop_index("ix_portfolio_transactions_portfolio_id", table_name="portfolio_transactions")
    op.drop_table("portfolio_transactions")

    op.drop_index("ix_portfolio_holdings_symbol", table_name="portfolio_holdings")
    op.drop_index("ix_portfolio_holdings_portfolio_id", table_name="portfolio_holdings")
    op.drop_table("portfolio_holdings")

    op.drop_index("ix_portfolios_user_id", table_name="portfolios")
    op.drop_table("portfolios")

    transaction_type.drop(op.get_bind(), checkfirst=True)
    portfolio_type.drop(op.get_bind(), checkfirst=True)
