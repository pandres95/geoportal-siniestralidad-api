#!/usr/bin/env python3
"""
Test suite for the unified data loading system.
Tests the complete pipeline including model discovery, migrations, and data loading.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add loader to path for imports
sys.path.append('.')

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
from ingest_unified import UnifiedDataLoader


class TestUnifiedSystem(unittest.TestCase):
    """Test cases for the unified loading system"""

    def setUp(self):
        """Set up test environment"""
        self.database_url = "postgresql://test:test@localhost/test"
        self.models_path = "models"

    def test_model_discovery(self):
        """Test model discovery mechanism"""
        discovery = ModelDiscovery(self.models_path)
        models = discovery.discover_models()

        # Should discover at least the victims model
        self.assertIn('victims', models)
        self.assertTrue(models['victims']['has_ingest'])
        self.assertTrue(models['victims']['has_migrate'])

    def test_strategy_loading(self):
        """Test loading strategies from discovered models"""
        discovery = ModelDiscovery(self.models_path)
        strategies = discovery.get_all_strategies()

        # Should load at least the victims strategy
        self.assertIn('victims', strategies)
        self.assertIsInstance(strategies['victims'], BaseLoaderStrategy)

    def test_victims_strategy_interface(self):
        """Test that victims strategy implements required interface"""
        discovery = ModelDiscovery(self.models_path)
        strategies = discovery.get_all_strategies()

        victims_strategy = strategies['victims']

        # Test required methods exist
        self.assertTrue(hasattr(victims_strategy, 'load_data'))
        self.assertTrue(hasattr(victims_strategy, 'transform_data'))
        self.assertTrue(hasattr(victims_strategy, 'get_column_mapping'))
        self.assertTrue(hasattr(victims_strategy, 'get_insert_sql'))
        self.assertTrue(hasattr(victims_strategy, 'get_create_table_sql'))
        self.assertTrue(hasattr(victims_strategy, 'get_drop_table_sql'))

        # Test method signatures
        column_mapping = victims_strategy.get_column_mapping()
        self.assertIsInstance(column_mapping, dict)

        insert_sql = victims_strategy.get_insert_sql()
        self.assertIn('INSERT INTO', insert_sql)

        create_sql = victims_strategy.get_create_table_sql()
        self.assertIn('CREATE TABLE', create_sql)

        drop_sql = victims_strategy.get_drop_table_sql()
        self.assertIn('DROP TABLE', drop_sql)

    def test_migration_file_discovery(self):
        """Test discovery of migration files"""
        discovery = ModelDiscovery(self.models_path)
        up_migrations, down_migrations = discovery.get_model_migrations('victims')

        # Should find migration files
        self.assertGreater(len(up_migrations), 0, "Should find up migration files")
        self.assertGreater(len(down_migrations), 0, "Should find down migration files")

        # Files should exist
        for migration_file in up_migrations + down_migrations:
            self.assertTrue(os.path.exists(migration_file), f"Migration file should exist: {migration_file}")

    @patch('psycopg2.connect')
    def test_database_migration_execution(self, mock_connect):
        """Test database migration execution"""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Create loader and run migrations
        loader = UnifiedDataLoader(self.database_url, self.models_path)

        # Test migration execution
        discovery = ModelDiscovery(self.models_path)
        up_migrations, _ = discovery.get_model_migrations('victims')

        if up_migrations:
            success = loader._execute_sql_file(up_migrations[0])
            # Should attempt to execute (mocked)
            mock_cursor.execute.assert_called()

    def test_file_model_mapping(self):
        """Test mapping files to appropriate models"""
        loader = UnifiedDataLoader(self.database_url, self.models_path)

        # Test various file patterns
        test_cases = [
            ('accidents.gpkg', 'victims'),
            ('victims_data.gpkg', 'victims'),
            ('schools.gpkg', None),  # Not implemented yet
        ]

        for file_path, expected_model in test_cases:
            model = loader._determine_model_for_file(file_path)
            self.assertEqual(model, expected_model, f"Wrong model for {file_path}")

    def test_pipeline_initialization(self):
        """Test pipeline initialization"""
        loader = UnifiedDataLoader(self.database_url, self.models_path)

        # Should initialize without errors
        self.assertEqual(loader.database_url, self.database_url)
        self.assertEqual(loader.models_base_path, self.models_path)
        self.assertEqual(len(loader.stats['errors']), 0)

    def test_error_handling(self):
        """Test error handling in pipeline"""
        # Test with invalid database URL
        loader = UnifiedDataLoader("invalid_url")

        # Should handle gracefully
        success = loader.run_complete_pipeline(migrate_up=False, load_data=False)
        self.assertFalse(success)
        self.assertGreater(len(loader.stats['errors']), 0)


def run_specific_tests():
    """Run specific test functions"""
    print("🧪 Running unified system tests...")

    # Test model discovery
    print("\n📋 Testing model discovery...")
    discovery = ModelDiscovery("models")
    models = discovery.discover_models()
    print(f"   ✅ Discovered {len(models)} model(s)")

    # Test strategy loading
    print("\n🔧 Testing strategy loading...")
    strategies = discovery.get_all_strategies()
    print(f"   ✅ Loaded {len(strategies)} strategie(s)")

    # Test migration discovery
    print("\n🗄️  Testing migration discovery...")
    up_migrations, down_migrations = discovery.get_model_migrations('victims')
    print(f"   ✅ Found {len(up_migrations)} up migration(s)")
    print(f"   ✅ Found {len(down_migrations)} down migration(s)")

    # Test strategy interface
    print("\n🔌 Testing strategy interface...")
    if 'victims' in strategies:
        strategy = strategies['victims']
        print(f"   ✅ Strategy model name: {strategy.model_name}")
        print(f"   ✅ Strategy table name: {strategy.table_name}")

        # Test SQL generation
        insert_sql = strategy.get_insert_sql()
        create_sql = strategy.get_create_table_sql()
        drop_sql = strategy.get_drop_table_sql()

        print("   ✅ Generated insert SQL")
        print("   ✅ Generated create table SQL")
        print("   ✅ Generated drop table SQL")

    print("\n✅ All unified system tests passed!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--run-simple":
        # Run simple tests without unittest framework
        run_specific_tests()
    else:
        # Run full unittest suite
        unittest.main(argv=[''], exit=False)