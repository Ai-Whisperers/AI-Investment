"""
Add Google OAuth support to users table.
"""

from sqlalchemy import text


def upgrade(engine):
    """Add is_google_user column to users table."""
    # Skip migration for SQLite test database
    if "sqlite" in str(engine.url):
        print("Skipping Google auth migration for SQLite database")
        return
        
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(
            text(
                """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='is_google_user'
        """
            )
        )

        if not result.fetchone():
            # Add the column
            conn.execute(
                text(
                    """
                ALTER TABLE users 
                ADD COLUMN is_google_user BOOLEAN DEFAULT FALSE
            """
                )
            )
            conn.commit()
            print("Added is_google_user column to users table")
        else:
            print("is_google_user column already exists")


def downgrade(engine):
    """Remove is_google_user column from users table."""
    with engine.connect() as conn:
        conn.execute(
            text(
                """
            ALTER TABLE users 
            DROP COLUMN IF EXISTS is_google_user
        """
            )
        )
        conn.commit()
