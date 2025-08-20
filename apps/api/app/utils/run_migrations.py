"""
Run database migrations including index creation.
This can be called from the application startup or manually.
"""

import logging
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError
from ..core.database import engine

logger = logging.getLogger(__name__)


def run_index_migration():
    """Create database indexes for performance optimization."""

    try:
        with engine.begin() as conn:
            logger.info("Running database index migration...")

            # Get inspector to check existing indexes
            inspector = inspect(engine)

            # Define indexes to create (safer than raw SQL)
            indexes_to_create = [
                ("prices", "idx_price_asset_date", ["asset_id", "date"]),
                ("prices", "idx_price_date", ["date"]),
                ("prices", "idx_price_asset_id", ["asset_id"]),
                ("allocations", "idx_allocation_date", ["date"]),
                ("allocations", "idx_allocation_asset_date", ["asset_id", "date"]),
                ("index_values", "idx_index_value_date", ["date"]),
            ]

            created_count = 0

            for table_name, index_name, columns in indexes_to_create:
                # Check if table exists
                if not inspector.has_table(table_name):
                    logger.warning(
                        f"Table {table_name} does not exist, skipping index {index_name}"
                    )
                    continue

                # Check if index already exists
                existing_indexes = inspector.get_indexes(table_name)
                index_exists = any(
                    idx["name"] == index_name for idx in existing_indexes
                )

                if not index_exists:
                    # Create index using parameterized statement
                    columns_str = ", ".join(columns)
                    # Use SQLAlchemy DDL for safer index creation
                    from sqlalchemy import DDL

                    create_index_ddl = DDL(
                        f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns_str})"
                    )
                    conn.execute(create_index_ddl)
                    logger.info(f"Created index: {index_name} on {table_name}")
                    created_count += 1
                else:
                    logger.debug(f"Index {index_name} already exists on {table_name}")

            # Add timestamp columns using safer approach
            tables_to_update = ["prices", "allocations", "index_values"]

            for table_name in tables_to_update:
                if not inspector.has_table(table_name):
                    continue

                # Get existing columns
                columns = inspector.get_columns(table_name)
                column_names = [col["name"] for col in columns]

                # Add created_at if missing
                if "created_at" not in column_names:
                    from sqlalchemy import DDL

                    add_column_ddl = DDL(
                        f"ALTER TABLE {table_name} ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                    )
                    conn.execute(add_column_ddl)
                    logger.info(f"Added created_at column to {table_name}")

                # Add updated_at if missing
                if "updated_at" not in column_names:
                    from sqlalchemy import DDL

                    add_column_ddl = DDL(
                        f"ALTER TABLE {table_name} ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                    )
                    conn.execute(add_column_ddl)
                    logger.info(f"Added updated_at column to {table_name}")

            # Create update trigger function (PostgreSQL specific)
            # Only create if using PostgreSQL
            if "postgresql" in str(engine.url):
                conn.execute(
                    text(
                        """
                    CREATE OR REPLACE FUNCTION update_updated_at_column()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.updated_at = CURRENT_TIMESTAMP;
                        RETURN NEW;
                    END;
                    $$ language 'plpgsql'
                """
                    )
                )

                # Create triggers for each table
                for table_name in tables_to_update:
                    if inspector.has_table(table_name):
                        trigger_name = f"update_{table_name}_updated_at"
                        from sqlalchemy import DDL

                        drop_trigger_ddl = DDL(
                            f"DROP TRIGGER IF EXISTS {trigger_name} ON {table_name}"
                        )
                        conn.execute(drop_trigger_ddl)
                        create_trigger_ddl = DDL(
                            f"CREATE TRIGGER {trigger_name} BEFORE UPDATE ON {table_name} "
                            f"FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()"
                        )
                        conn.execute(create_trigger_ddl)
                        logger.info(f"Created update trigger for {table_name}")

            # Update statistics for query planner
            for table_name in tables_to_update:
                if inspector.has_table(table_name):
                    from sqlalchemy import DDL

                    analyze_ddl = DDL(f"ANALYZE {table_name}")
                    conn.execute(analyze_ddl)

            logger.info(f"Migration completed. Created {created_count} new indexes.")

            # Verify final state
            total_indexes = 0
            for table_name, _, _ in indexes_to_create:
                if inspector.has_table(table_name):
                    indexes = inspector.get_indexes(table_name)
                    custom_indexes = [
                        idx for idx in indexes if idx["name"].startswith("idx_")
                    ]
                    total_indexes += len(custom_indexes)

            logger.info(f"Total custom indexes: {total_indexes}")
            return True

    except SQLAlchemyError as e:
        logger.error(f"Database migration failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        return False


def run_google_auth_migration():
    """Add Google OAuth support to users table."""
    try:
        # Skip for SQLite test databases
        if "sqlite" in str(engine.url):
            logger.info("Skipping Google auth migration for SQLite database")
            return True
            
        from ..migrations.add_google_auth import upgrade
        upgrade(engine)
        return True
    except Exception as e:
        logger.error(f"Google auth migration failed: {e}")
        return False


def run_all_migrations():
    """Run all pending database migrations."""

    migrations = [
        ("indexes", run_index_migration),
        ("google_auth", run_google_auth_migration),
    ]

    success_count = 0
    for name, migration_func in migrations:
        logger.info(f"Running migration: {name}")
        if migration_func():
            success_count += 1
            logger.info(f"Migration {name} completed successfully")
        else:
            logger.error(f"Migration {name} failed")

    logger.info(f"Migrations complete: {success_count}/{len(migrations)} successful")
    return success_count == len(migrations)


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Run migrations
    if run_all_migrations():
        print("All migrations completed successfully")
    else:
        print("Some migrations failed. Check logs for details.")
        exit(1)
