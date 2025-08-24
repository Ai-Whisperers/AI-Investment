"""
Supabase Migration Script
Migrates data from current database to Supabase with zero downtime
"""

import os
import sys
import logging
import argparse
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SupabaseMigrator:
    """Handles migration from any PostgreSQL to Supabase."""
    
    def __init__(self, source_url: str, target_url: str, dry_run: bool = True):
        self.source_url = source_url
        self.target_url = target_url
        self.dry_run = dry_run
        self.source_conn = None
        self.target_conn = None
        
        # Tables to migrate in order (respecting foreign keys)
        self.migration_order = [
            'users',
            'portfolios',
            'assets',
            'prices',
            'index_values',
            'allocations',
            'strategy_configs',
            'risk_metrics',
            'market_cap_data',
            'signals',  # New signals table
            'news'
        ]
        
    def connect(self):
        """Establish database connections."""
        try:
            logger.info("Connecting to source database...")
            self.source_conn = psycopg2.connect(self.source_url)
            
            if not self.dry_run:
                logger.info("Connecting to target database...")
                self.target_conn = psycopg2.connect(self.target_url)
            else:
                logger.info("DRY RUN MODE - Not connecting to target")
                
            logger.info("Connections established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise
            
    def disconnect(self):
        """Close database connections."""
        if self.source_conn:
            self.source_conn.close()
        if self.target_conn:
            self.target_conn.close()
            
    def check_table_exists(self, conn, table_name: str) -> bool:
        """Check if table exists in database."""
        with conn.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table_name,))
            return cur.fetchone()[0]
            
    def get_table_count(self, conn, table_name: str) -> int:
        """Get row count for a table."""
        if not self.check_table_exists(conn, table_name):
            return 0
            
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            return cur.fetchone()[0]
            
    def create_signals_table(self):
        """Create signals table if it doesn't exist."""
        create_sql = """
        CREATE TABLE IF NOT EXISTS signals (
            id SERIAL PRIMARY KEY,
            ticker VARCHAR(10) NOT NULL,
            signal_type VARCHAR(50) NOT NULL,
            confidence FLOAT NOT NULL,
            expected_return FLOAT NOT NULL,
            timeframe VARCHAR(50) NOT NULL,
            sources JSONB NOT NULL DEFAULT '[]'::jsonb,
            pattern_stack JSONB NOT NULL DEFAULT '[]'::jsonb,
            created_at TIMESTAMP DEFAULT NOW(),
            executed BOOLEAN DEFAULT FALSE,
            result FLOAT,
            action VARCHAR(20) NOT NULL,
            stop_loss FLOAT,
            take_profit FLOAT,
            allocation_percent FLOAT,
            volume_spike FLOAT,
            momentum_score FLOAT,
            sentiment_divergence FLOAT,
            meme_velocity FLOAT
        );
        
        CREATE INDEX IF NOT EXISTS idx_signals_ticker ON signals(ticker);
        CREATE INDEX IF NOT EXISTS idx_signals_confidence ON signals(confidence);
        CREATE INDEX IF NOT EXISTS idx_signals_created ON signals(created_at);
        CREATE INDEX IF NOT EXISTS idx_signals_type ON signals(signal_type);
        """
        
        if not self.dry_run and self.target_conn:
            with self.target_conn.cursor() as cur:
                cur.execute(create_sql)
                self.target_conn.commit()
                logger.info("Created signals table with indexes")
        else:
            logger.info("DRY RUN: Would create signals table")
            
    def migrate_table(self, table_name: str) -> Dict:
        """Migrate a single table."""
        logger.info(f"Migrating table: {table_name}")
        
        # Check if table exists in source
        if not self.check_table_exists(self.source_conn, table_name):
            logger.warning(f"Table {table_name} does not exist in source, skipping")
            return {'table': table_name, 'status': 'skipped', 'rows': 0}
            
        # Get source data
        source_count = self.get_table_count(self.source_conn, table_name)
        logger.info(f"Found {source_count} rows in {table_name}")
        
        if source_count == 0:
            return {'table': table_name, 'status': 'empty', 'rows': 0}
            
        # Fetch data in batches
        batch_size = 1000
        offset = 0
        total_migrated = 0
        
        with self.source_conn.cursor(cursor_factory=RealDictCursor) as source_cur:
            while offset < source_count:
                # Fetch batch
                source_cur.execute(
                    f"SELECT * FROM {table_name} LIMIT %s OFFSET %s",
                    (batch_size, offset)
                )
                rows = source_cur.fetchall()
                
                if not rows:
                    break
                    
                # Insert into target
                if not self.dry_run and self.target_conn:
                    self._insert_batch(table_name, rows)
                    total_migrated += len(rows)
                else:
                    logger.info(f"DRY RUN: Would migrate {len(rows)} rows")
                    total_migrated += len(rows)
                    
                offset += batch_size
                
        return {
            'table': table_name,
            'status': 'migrated' if not self.dry_run else 'dry_run',
            'rows': total_migrated
        }
        
    def _insert_batch(self, table_name: str, rows: List[Dict]):
        """Insert a batch of rows into target table."""
        if not rows:
            return
            
        # Get column names from first row
        columns = list(rows[0].keys())
        
        # Build insert query
        placeholders = ','.join(['%s'] * len(columns))
        columns_str = ','.join(columns)
        
        insert_sql = f"""
            INSERT INTO {table_name} ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT (id) DO UPDATE SET
            {','.join([f"{col}=EXCLUDED.{col}" for col in columns if col != 'id'])}
        """
        
        with self.target_conn.cursor() as cur:
            for row in rows:
                values = [row[col] for col in columns]
                cur.execute(insert_sql, values)
                
        self.target_conn.commit()
        
    def verify_migration(self) -> Dict:
        """Verify migration by comparing row counts."""
        verification = {}
        
        for table in self.migration_order:
            source_count = self.get_table_count(self.source_conn, table)
            
            if not self.dry_run and self.target_conn:
                target_count = self.get_table_count(self.target_conn, table)
                match = source_count == target_count
            else:
                target_count = "N/A (dry run)"
                match = None
                
            verification[table] = {
                'source_count': source_count,
                'target_count': target_count,
                'match': match
            }
            
        return verification
        
    def run_migration(self) -> Dict:
        """Run the complete migration process."""
        logger.info("Starting migration process...")
        
        results = {
            'start_time': datetime.now().isoformat(),
            'dry_run': self.dry_run,
            'tables': []
        }
        
        try:
            self.connect()
            
            # Create signals table if needed
            self.create_signals_table()
            
            # Migrate each table
            for table in self.migration_order:
                result = self.migrate_table(table)
                results['tables'].append(result)
                
            # Verify migration
            results['verification'] = self.verify_migration()
            
            results['end_time'] = datetime.now().isoformat()
            results['status'] = 'success'
            
            # Update sequences
            if not self.dry_run and self.target_conn:
                self._update_sequences()
                
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            results['status'] = 'failed'
            results['error'] = str(e)
            
        finally:
            self.disconnect()
            
        return results
        
    def _update_sequences(self):
        """Update sequences to max ID values."""
        logger.info("Updating sequences...")
        
        sequence_sql = """
        SELECT setval(pg_get_serial_sequence(%s, 'id'), 
               COALESCE((SELECT MAX(id) FROM %s), 1), 
               true);
        """
        
        with self.target_conn.cursor() as cur:
            for table in self.migration_order:
                if self.check_table_exists(self.target_conn, table):
                    cur.execute(sequence_sql, (table, table))
                    
        self.target_conn.commit()
        logger.info("Sequences updated successfully")


def main():
    """Main migration entry point."""
    parser = argparse.ArgumentParser(description='Migrate database to Supabase')
    parser.add_argument(
        '--source-url',
        default=os.getenv('DATABASE_URL'),
        help='Source database URL'
    )
    parser.add_argument(
        '--target-url',
        default=os.getenv('SUPABASE_DATABASE_URL'),
        help='Target Supabase database URL'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        default=True,
        help='Run without actually migrating data'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Execute the migration (disables dry-run)'
    )
    parser.add_argument(
        '--output',
        help='Output results to JSON file'
    )
    
    args = parser.parse_args()
    
    if args.execute:
        args.dry_run = False
        
    if not args.source_url:
        logger.error("Source database URL required")
        sys.exit(1)
        
    if not args.dry_run and not args.target_url:
        logger.error("Target database URL required for actual migration")
        sys.exit(1)
        
    # Run migration
    migrator = SupabaseMigrator(
        source_url=args.source_url,
        target_url=args.target_url,
        dry_run=args.dry_run
    )
    
    results = migrator.run_migration()
    
    # Output results
    print("\n" + "="*50)
    print("MIGRATION RESULTS")
    print("="*50)
    
    for table_result in results.get('tables', []):
        status_emoji = {
            'migrated': '✅',
            'dry_run': '🔍',
            'skipped': '⏭️',
            'empty': '📭'
        }.get(table_result['status'], '❓')
        
        print(f"{status_emoji} {table_result['table']}: {table_result['rows']} rows")
        
    if 'verification' in results:
        print("\nVERIFICATION:")
        for table, verify in results['verification'].items():
            if verify['match'] is True:
                print(f"✅ {table}: {verify['source_count']} rows matched")
            elif verify['match'] is False:
                print(f"❌ {table}: Source={verify['source_count']}, Target={verify['target_count']}")
            else:
                print(f"🔍 {table}: {verify['source_count']} rows (dry run)")
                
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults saved to {args.output}")
        
    print(f"\nStatus: {results.get('status', 'unknown').upper()}")
    
    if args.dry_run:
        print("\n⚠️  This was a DRY RUN. Use --execute to perform actual migration.")


if __name__ == "__main__":
    main()