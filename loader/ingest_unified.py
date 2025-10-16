#!/usr/bin/env python3
"""
Unified data loading system with automatic model discovery and migration pipeline.
This is the main entry point that handles the complete data pipeline for all models.
"""
import os
import glob
import argparse
import psycopg2
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional

# Import our core modules
try:
    from core.strategy import BaseLoaderStrategy
    from core.discovery import ModelDiscovery
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from core.strategy import BaseLoaderStrategy
    from core.discovery import ModelDiscovery


class UnifiedDataLoader:
    """Main unified loader that handles complete pipeline for all models"""

    def __init__(self, database_url: str, models_base_path: str = "models", single_model: str = None):
        self.database_url = database_url
        self.models_base_path = models_base_path
        self.single_model = single_model
        self.discovery = ModelDiscovery(models_base_path)
        self.strategies = {}
        self.stats = {
            'models_processed': 0,
            'migrations_run': 0,
            'files_processed': 0,
            'records_loaded': 0,
            'errors': []
        }

    def run_complete_pipeline(self, migrate_up: bool = True, migrate_down: bool = False,
                            load_data: bool = True) -> bool:
        """Run the complete pipeline: discover models → migrate → load data"""
        print("🚀 Starting unified data loading pipeline...")

        try:
            # Step 1: Discover all available models
            print("\n📋 Step 1: Discovering models...")
            models = self.discovery.discover_models()

            if not models:
                print("❌ No models discovered")
                return False

            # Filter to single model if specified
            if self.single_model:
                if self.single_model not in models:
                    print(f"❌ Specified model '{self.single_model}' not found. Available models: {list(models.keys())}")
                    return False
                models = {self.single_model: models[self.single_model]}
                print(f"📋 Processing single model: {self.single_model}")

            # Step 2: Load all strategies
            print("\n🔧 Step 2: Loading strategies...")
            if self.single_model:
                # Load only the specified strategy
                self.strategies = {self.single_model: self.discovery.load_strategy(self.single_model)}
            else:
                # Load all strategies
                self.strategies = self.discovery.get_all_strategies()

            if not self.strategies:
                print("❌ No strategies loaded")
                return False

            # Step 3: Run migrations (if requested)
            if migrate_up or migrate_down:
                print(f"\n🗄️  Step 3: Running migrations...")
                migration_success = self._run_migrations(migrate_up, migrate_down)

                if not migration_success:
                    print("❌ Migration step failed")
                    return False
            else:
                # Show what migrations would be run (if any)
                # Get migrations for all discovered models
                all_up = []
                all_down = []

                for model_name, strategy in self.strategies.items():
                    up_migrations, down_migrations = self.discovery.get_model_migrations(model_name)

                    # Also check strategy paths as fallback
                    strategy_up_path = None
                    strategy_down_path = None
                    try:
                        strategy_up_path = strategy.get_create_table_sql_path()
                        strategy_down_path = strategy.get_drop_table_sql_path()
                    except:
                        pass

                    # Combine discovered files and strategy paths
                    model_up = up_migrations + ([strategy_up_path] if strategy_up_path and os.path.exists(strategy_up_path) else [])
                    model_down = down_migrations + ([strategy_down_path] if strategy_down_path and os.path.exists(strategy_down_path) else [])

                    all_up.extend(model_up)
                    all_down.extend(model_down)

                if all_up or all_down:
                    print(f"\n🗄️  Step 3: Migrations available (not executed):")
                    if all_up:
                        print(f"   ⬆️  Up migrations: {len(all_up)} file(s)")
                        for migration in all_up:
                            print(f"      • {os.path.basename(migration)}")
                    if all_down:
                        print(f"   ⬇️  Down migrations: {len(all_down)} file(s)")
                        for migration in all_down:
                            print(f"      • {os.path.basename(migration)}")
                else:
                    print(f"\n🗄️  Step 3: No migrations found")

            # Step 4: Load data (if requested)
            if load_data:
                print("\n📦 Step 4: Loading data...")
                load_success = self._load_all_data()

                if not load_success:
                    print("❌ Data loading step failed")
                    return False

            # Success!
            print("\n✅ Pipeline completed successfully!")
            self._print_summary()
            return True

        except Exception as e:
            error_msg = f"Pipeline error: {str(e)}"
            print(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)
            return False

    def _run_migrations(self, migrate_up: bool, migrate_down: bool) -> bool:
        """Run database migrations for all models with proper sequencing"""
        success = True

        # First, ensure migrations table exists
        if not self._ensure_migrations_table():
            print("❌ Failed to create migrations table")
            return False

        for model_name, strategy in self.strategies.items():
            try:
                print(f"\n🔄 Processing migrations for model: {model_name}")

                # Get migration files using new strategy method
                migration_files = strategy.get_migration_files()
                up_migrations = migration_files['up']
                down_migrations = migration_files['down']

                # Run down migrations first (if requested) - in reverse order
                if migrate_down and down_migrations:
                    print(f"   ⬇️  Running down migrations...")
                    for migration_file in reversed(down_migrations):
                        if not self._execute_migration_file(migration_file, model_name, 'down'):
                            success = False
                            break  # Stop on first failure
                elif migrate_down:
                    print(f"   ⚠️  No down migrations found for {model_name}")

                # Run up migrations (if requested) - in order
                if migrate_up and up_migrations:
                    print(f"   ⬆️  Running up migrations...")
                    for migration_file in up_migrations:
                        if not self._execute_migration_file(migration_file, model_name, 'up'):
                            success = False
                            break  # Stop on first failure
                elif migrate_up:
                    print(f"   ⚠️  No up migrations found for {model_name}")

                if migrate_up or migrate_down:
                    print(f"   ✅ Migrations completed for {model_name}")

            except Exception as e:
                print(f"❌ Migration error for {model_name}: {e}")
                success = False

        return success

    def _ensure_migrations_table(self) -> bool:
        """Ensure the migrations tracking table exists"""
        try:
            migrations_sql_path = "core/001_create_migrations_table.sql"
            if os.path.exists(migrations_sql_path):
                print("🔧 Ensuring migrations table exists...")
                return self._execute_sql_file(migrations_sql_path)
            else:
                print("⚠️  Migrations table SQL file not found")
                return False
        except Exception as e:
            print(f"❌ Error ensuring migrations table: {e}")
            return False

    def _execute_migration_file(self, sql_file_path: str, model_name: str, direction: str) -> bool:
        """Execute a migration file with tracking"""
        try:
            if not os.path.exists(sql_file_path):
                print(f"   ⚠️  Migration file not found: {sql_file_path}")
                return False

            migration_name = os.path.basename(sql_file_path)
            print(f"   📄 Executing migration: {migration_name}")

            # Check if migration has already been applied (for up migrations)
            if direction == 'up':
                if self._is_migration_applied(model_name, migration_name):
                    print(f"   ⏭️  Migration {migration_name} already applied, skipping...")
                    return True

            # Execute the migration
            if not self._execute_sql_file(sql_file_path):
                return False

            # Record the migration as applied (for up migrations)
            if direction == 'up':
                self._record_migration_applied(model_name, migration_name)

            return True

        except Exception as e:
            print(f"   ❌ Migration execution error: {e}")
            return False

    def _is_migration_applied(self, model_name: str, migration_name: str) -> bool:
        """Check if a migration has already been applied"""
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT 1 FROM public.migrations WHERE model = %s AND migration = %s",
                        (model_name, migration_name)
                    )
                    return cur.fetchone() is not None
        except Exception as e:
            print(f"   ⚠️  Error checking migration status: {e}")
            return False

    def _record_migration_applied(self, model_name: str, migration_name: str) -> None:
        """Record that a migration has been applied"""
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO public.migrations (model, migration) VALUES (%s, %s)",
                        (model_name, migration_name)
                    )
                    conn.commit()
        except Exception as e:
            print(f"   ⚠️  Error recording migration: {e}")

    def _execute_sql_file(self, sql_file_path: str) -> bool:
        """Execute a SQL file against the database"""
        try:
            if not os.path.exists(sql_file_path):
                print(f"   ⚠️  SQL file not found: {sql_file_path}")
                return False

            print(f"   📄 Executing: {os.path.basename(sql_file_path)}")

            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # Parse SQL statements more carefully, handling functions and complex statements
            statements = []
            current_statement = []
            in_function = False
            in_dollar_quote = False
            dollar_tag = None

            for line in sql_content.split('\n'):
                line = line.strip()
                if not line or line.startswith('--'):
                    continue

                # Track function definitions
                if line.startswith('CREATE OR REPLACE FUNCTION'):
                    in_function = True

                # Track dollar quoting
                if '$$' in line and not in_dollar_quote:
                    in_dollar_quote = True
                    dollar_tag = '$$'
                elif line.startswith('$$') and in_dollar_quote:
                    in_dollar_quote = False
                    dollar_tag = None

                current_statement.append(line)

                # End of statement conditions
                if line.endswith(';') and not in_function and not in_dollar_quote:
                    statements.append('\n'.join(current_statement))
                    current_statement = []
                elif line == '$$' and in_function and not in_dollar_quote:
                    # End of function body
                    in_function = False

            # Add any remaining statement
            if current_statement:
                statements.append('\n'.join(current_statement))

            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    for statement in statements:
                        if statement.strip():
                            cur.execute(statement)
                    conn.commit()

            print(f"   ✅ Executed successfully")
            self.stats['migrations_run'] += 1
            return True

        except Exception as e:
            print(f"   ❌ SQL execution error: {e}")
            return False

    def _load_all_data(self) -> bool:
        """Load data for all models"""
        success = True

        # Find all .gpkg files in data directory
        data_dir = "../data"
        if os.path.exists(data_dir):
            gpkg_files = glob.glob(os.path.join(data_dir, "*.gpkg"))
            print(f"🔍 Found {len(gpkg_files)} .gpkg file(s)")

            # Filter files based on single model if specified
            if self.single_model:
                # For single model, only load files that match the model name
                filtered_files = [f for f in gpkg_files if self.single_model.lower() in os.path.basename(f).lower()]
                if filtered_files:
                    gpkg_files = filtered_files
                    print(f"📋 Filtered to {len(gpkg_files)} file(s) for model '{self.single_model}'")
                else:
                    print(f"⚠️  No files found matching model '{self.single_model}'")
                    return False

            for gpkg_file in gpkg_files:
                file_success = self._load_single_file(gpkg_file)
                if not file_success:
                    success = False
        else:
            print(f"⚠️  Data directory not found: {data_dir}")
            success = False

        return success

    def _load_single_file(self, file_path: str) -> bool:
        """Load a single file using appropriate strategy"""
        try:
            print(f"\n📦 Processing file: {os.path.basename(file_path)}")

            # Determine which model should handle this file
            model_name = self._determine_model_for_file(file_path)

            if not model_name or model_name not in self.strategies:
                print(f"⚠️  No strategy available for {file_path}")
                return False

            strategy = self.strategies[model_name]
            print(f"📋 Using model: {model_name}")

            # Load and transform data
            raw_data = strategy.load_data(file_path)
            transformed_data = strategy.transform_data(raw_data)

            # Validate data
            warnings = strategy.validate_data(transformed_data)
            if warnings:
                print("⚠️  Data validation warnings:")
                for warning in warnings:
                    print(f"   • {warning}")

            # Load to database
            records_loaded = self._load_to_database(transformed_data, strategy)

            if records_loaded > 0:
                self.stats['files_processed'] += 1
                self.stats['records_loaded'] += records_loaded
                print(f"✅ Loaded {records_loaded} records")
                return True
            else:
                print(f"⚠️  No records loaded from {file_path}")
                return False

        except Exception as e:
            error_msg = f"Error loading {file_path}: {str(e)}"
            print(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)
            return False

    def _determine_model_for_file(self, file_path: str) -> Optional[str]:
        """Determine which model should handle a specific file"""
        file_name = os.path.basename(file_path).lower()

        # Simple mapping based on filename patterns
        if 'accident' in file_name or 'victims' in file_name:
            return 'victims'
        elif 'schools' in file_name:
            return 'schools'
        elif 'zat' in file_name:
            return 'zat'

        return None

    def _load_to_database(self, gdf, strategy: BaseLoaderStrategy) -> int:
        """Load transformed data to PostgreSQL database"""
        if len(gdf) == 0:
            print("⚠️  No data to load")
            return 0

        print(f"💾 Loading {len(gdf)} records to {strategy.table_name}...")

        # Prepare data for insertion
        records = []
        invalid_records = 0

        for _, row in gdf.iterrows():
            record = self._prepare_record(row, strategy)
            if record:
                records.append(record)
            else:
                invalid_records += 1

        if invalid_records > 0:
            print(f"⚠️  Skipped {invalid_records} invalid records (null geometry or other issues)")

        if not records:
            print("⚠️  No valid records to insert")
            return 0

        # Execute batch insert
        insert_sql = strategy.get_insert_sql()
        records_loaded = self._execute_batch_insert(insert_sql, records, strategy.table_name)

        return records_loaded

    def _prepare_record(self, row, strategy: BaseLoaderStrategy) -> Optional[tuple]:
        """Prepare a single record for database insertion"""
        try:
            # Get column mapping
            column_mapping = strategy.get_column_mapping()

            # Extract values in correct order
            values = []
            for source_col, target_col in column_mapping.items():
                if target_col in ['geom']:
                    # Handle geometry separately - skip records with null geometry
                    if hasattr(row, 'geom') and row.geom and not row.geom.is_empty:
                        values.append(row.geom.wkt)
                    elif hasattr(row, 'geometry') and row.geometry and not row.geometry.is_empty:
                        values.append(row.geometry.wkt)
                    else:
                        # Return None to indicate this record should be skipped
                        return None
                else:
                    # Handle regular columns - use the target column name since data is already transformed
                    value = row.get(target_col, None)
                    if pd.isna(value) or value == 'NaN':
                        values.append(None)
                    else:
                        values.append(value)

            return tuple(values)

        except Exception as e:
            print(f"⚠️  Error preparing record: {e}")
            return None

    def _execute_batch_insert(self, sql: str, records: List[tuple], table_name: str) -> int:
        """Execute batch insert with error handling"""
        try:
            import psycopg2.extras

            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    # Use execute_values for efficient batch insertion
                    psycopg2.extras.execute_values(
                        cur,
                        sql,
                        records,
                        page_size=1000
                    )
                    records_loaded = cur.rowcount
                    conn.commit()

                    print(f"   📊 Inserted {records_loaded} records into {table_name}")
                    return records_loaded

        except Exception as e:
            print(f"❌ Database error: {e}")
            raise

    def _print_summary(self):
        """Print comprehensive pipeline summary"""
        print("\n📈 Pipeline Summary:")
        print(f"   Models discovered: {len(self.discovery.discovered_models)}")
        print(f"   Strategies loaded: {len(self.strategies)}")
        print(f"   Migrations run: {self.stats['migrations_run']}")
        print(f"   Files processed: {self.stats['files_processed']}")
        print(f"   Records loaded: {self.stats['records_loaded']}")
        print(f"   Errors: {len(self.stats['errors'])}")

        if self.stats['errors']:
            print("\n❌ Errors encountered:")
            for error in self.stats['errors']:
                print(f"   • {error}")


def main():
    """Main function for unified data loading pipeline"""
    parser = argparse.ArgumentParser(description='Unified data loading pipeline for all models')
    parser.add_argument('--migrate-up', action='store_true', default=False,
                       help='Run database migrations (up)')
    parser.add_argument('--migrate-down', action='store_true',
                       help='Run database migrations (down) - WARNING: destroys data')
    parser.add_argument('--no-load', action='store_true',
                       help='Skip data loading step (implies no migrations unless --migrate-up is specified)')
    parser.add_argument('--discover-only', action='store_true',
                        help='Only discover and list models (no migrations, no data loading)')
    parser.add_argument('--models-path', default='models',
                        help='Path to models directory')
    parser.add_argument('--model', type=str,
                        help='Specify a single model to process (e.g., schools, victims)')

    args = parser.parse_args()

    # Get database URL
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("❌ Please set DATABASE_URL environment variable")
        return 1

    # Determine what to run based on arguments
    if args.discover_only:
        # Discover only mode
        migrate_up = False
        migrate_down = False
        load_data = False
    elif args.no_load:
        # No load mode - only migrate if explicitly requested
        migrate_up = args.migrate_up  # False by default now
        migrate_down = args.migrate_down
        load_data = False
    else:
        # Full pipeline mode
        migrate_up = False  # Default for full pipeline - don't run migrations unless explicitly requested
        migrate_down = args.migrate_down
        load_data = True

    print("🔧 Pipeline Configuration:")
    print(f"   Discover models: ✅")
    print(f"   Load strategies: ✅")
    print(f"   Run migrations: {'✅' if migrate_up or migrate_down else '❌'}")
    print(f"   Load data: {'✅' if load_data else '❌'}")

    # Initialize and run pipeline
    loader = UnifiedDataLoader(database_url, args.models_path, args.model)

    success = loader.run_complete_pipeline(
        migrate_up=migrate_up,
        migrate_down=migrate_down,
        load_data=load_data
    )

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())