"""
Migration script to add news and sentiment tables.
Run this after the initial database setup.
"""

import logging

from sqlalchemy import text

from ..core.database import engine

logger = logging.getLogger(__name__)


def create_news_tables():
    """Create news-related tables if they don't exist."""

    # Skip migration for SQLite test database
    if "sqlite" in str(engine.url):
        logger.info("Skipping news tables migration for SQLite database")
        return

    with engine.begin() as conn:
        # Check if tables already exist
        result = conn.execute(
            text(
                """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'news_articles'
            );
        """
            )
        )

        if result.scalar():
            logger.info("News tables already exist, skipping migration")
            return

        logger.info("Creating news tables...")

        # Create news_sources table
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS news_sources (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(100) NOT NULL UNIQUE,
                domain VARCHAR(255),
                country VARCHAR(2),
                language VARCHAR(2),
                credibility_score FLOAT DEFAULT 0.5,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS ix_news_sources_name ON news_sources(name);
            CREATE INDEX IF NOT EXISTS ix_news_sources_domain ON news_sources(domain);
        """
            )
        )

        # Create news_articles table
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS news_articles (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                external_id VARCHAR(255) UNIQUE,
                title VARCHAR(500) NOT NULL,
                description TEXT,
                content TEXT,
                url VARCHAR(500) NOT NULL UNIQUE,
                image_url VARCHAR(500),
                source_id UUID REFERENCES news_sources(id),
                source_name VARCHAR(100),
                language VARCHAR(2) DEFAULT 'en',
                country VARCHAR(2),
                published_at TIMESTAMP WITH TIME ZONE NOT NULL,
                categories JSONB DEFAULT '[]'::jsonb,
                keywords JSONB DEFAULT '[]'::jsonb,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS ix_news_articles_published_at ON news_articles(published_at);
            CREATE INDEX IF NOT EXISTS ix_news_articles_source_id ON news_articles(source_id);
            CREATE INDEX IF NOT EXISTS ix_news_articles_external_id ON news_articles(external_id);
            CREATE INDEX IF NOT EXISTS ix_news_articles_url ON news_articles(url);
        """
            )
        )

        # Create news_sentiment table
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS news_sentiment (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                article_id UUID NOT NULL UNIQUE REFERENCES news_articles(id) ON DELETE CASCADE,
                sentiment_score FLOAT NOT NULL,
                sentiment_label VARCHAR(20),
                confidence FLOAT DEFAULT 0.5,
                positive_score FLOAT,
                negative_score FLOAT,
                neutral_score FLOAT,
                provider VARCHAR(50),
                analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS ix_news_sentiment_article_id ON news_sentiment(article_id);
            CREATE INDEX IF NOT EXISTS ix_news_sentiment_score ON news_sentiment(sentiment_score);
            CREATE INDEX IF NOT EXISTS ix_news_sentiment_label ON news_sentiment(sentiment_label);
        """
            )
        )

        # Create news_entities table
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS news_entities (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                article_id UUID NOT NULL REFERENCES news_articles(id) ON DELETE CASCADE,
                symbol VARCHAR(20),
                name VARCHAR(255) NOT NULL,
                type VARCHAR(50),
                exchange VARCHAR(20),
                country VARCHAR(2),
                industry VARCHAR(100),
                match_score FLOAT,
                sentiment_score FLOAT,
                mention_count INTEGER DEFAULT 1,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS ix_news_entities_article_id ON news_entities(article_id);
            CREATE INDEX IF NOT EXISTS ix_news_entities_symbol ON news_entities(symbol);
            CREATE INDEX IF NOT EXISTS ix_news_entities_type ON news_entities(type);
            CREATE INDEX IF NOT EXISTS ix_news_entities_name ON news_entities(name);
        """
            )
        )

        # Create asset_news association table
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS asset_news (
                asset_id INTEGER REFERENCES assets(id),
                article_id UUID REFERENCES news_articles(id),
                relevance_score FLOAT DEFAULT 1.0,
                sentiment_score FLOAT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (asset_id, article_id)
            );
        """
            )
        )

        # Create entity_sentiment_history table
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS entity_sentiment_history (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                symbol VARCHAR(20) NOT NULL,
                date TIMESTAMP WITH TIME ZONE NOT NULL,
                sentiment_score FLOAT NOT NULL,
                article_count INTEGER DEFAULT 0,
                positive_count INTEGER DEFAULT 0,
                negative_count INTEGER DEFAULT 0,
                neutral_count INTEGER DEFAULT 0,
                total_mentions INTEGER DEFAULT 0,
                unique_sources INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_entity_sentiment_history_symbol_date UNIQUE (symbol, date)
            );

            CREATE INDEX IF NOT EXISTS ix_entity_sentiment_history_symbol_date ON entity_sentiment_history(symbol, date);
        """
            )
        )

        logger.info("News tables created successfully")


if __name__ == "__main__":
    create_news_tables()
