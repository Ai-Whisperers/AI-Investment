"""Add asset classification fields

Revision ID: 004
Revises: 003
Create Date: 2025-01-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """Add classification fields to assets table."""
    # Add sector column
    op.add_column('assets', sa.Column('sector', sa.String(50), nullable=True))
    
    # Add industry column
    op.add_column('assets', sa.Column('industry', sa.String(100), nullable=True))
    
    # Add market cap category
    op.add_column('assets', sa.Column('market_cap_category', sa.String(20), nullable=True))
    
    # Add tags as JSON field
    op.add_column('assets', sa.Column('tags', sa.JSON(), nullable=True, default=list))
    
    # Add ESG scores
    op.add_column('assets', sa.Column('esg_score', sa.Float(), nullable=True))
    op.add_column('assets', sa.Column('environmental_score', sa.Float(), nullable=True))
    op.add_column('assets', sa.Column('social_score', sa.Float(), nullable=True))
    op.add_column('assets', sa.Column('governance_score', sa.Float(), nullable=True))
    
    # Add supply chain and patent info
    op.add_column('assets', sa.Column('supply_chain_dependencies', sa.JSON(), nullable=True))
    op.add_column('assets', sa.Column('patent_portfolio_size', sa.Integer(), nullable=True))
    
    # Add fundamental data
    op.add_column('assets', sa.Column('pe_ratio', sa.Float(), nullable=True))
    op.add_column('assets', sa.Column('dividend_yield', sa.Float(), nullable=True))
    op.add_column('assets', sa.Column('market_cap', sa.BigInteger(), nullable=True))
    
    # Add volatility metrics
    op.add_column('assets', sa.Column('volatility_30d', sa.Float(), nullable=True))
    op.add_column('assets', sa.Column('volatility_90d', sa.Float(), nullable=True))
    
    # Create indexes for faster filtering
    op.create_index('ix_assets_sector', 'assets', ['sector'])
    op.create_index('ix_assets_industry', 'assets', ['industry'])
    op.create_index('ix_assets_market_cap_category', 'assets', ['market_cap_category'])
    op.create_index('ix_assets_esg_score', 'assets', ['esg_score'])


def downgrade():
    """Remove classification fields from assets table."""
    # Drop indexes
    op.drop_index('ix_assets_esg_score', 'assets')
    op.drop_index('ix_assets_market_cap_category', 'assets')
    op.drop_index('ix_assets_industry', 'assets')
    op.drop_index('ix_assets_sector', 'assets')
    
    # Drop columns
    op.drop_column('assets', 'volatility_90d')
    op.drop_column('assets', 'volatility_30d')
    op.drop_column('assets', 'market_cap')
    op.drop_column('assets', 'dividend_yield')
    op.drop_column('assets', 'pe_ratio')
    op.drop_column('assets', 'patent_portfolio_size')
    op.drop_column('assets', 'supply_chain_dependencies')
    op.drop_column('assets', 'governance_score')
    op.drop_column('assets', 'social_score')
    op.drop_column('assets', 'environmental_score')
    op.drop_column('assets', 'esg_score')
    op.drop_column('assets', 'tags')
    op.drop_column('assets', 'market_cap_category')
    op.drop_column('assets', 'industry')
    op.drop_column('assets', 'sector')