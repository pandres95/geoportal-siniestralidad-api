"""
Model discovery mechanism for the data loading system.
This module handles automatic discovery of available models and their components.
"""
import os
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import the base strategy for type checking
from .strategy import BaseLoaderStrategy


class ModelDiscovery:
    """Discovers and manages all available models in the system"""

    def __init__(self, models_base_path: str = "models"):
        self.models_base_path = models_base_path
        self.discovered_models = {}
        self.strategies = {}

    def discover_models(self) -> Dict[str, Dict[str, Any]]:
        """Discover all available models in the models directory"""
        models_dir = Path(self.models_base_path)
        if not models_dir.exists():
            print(f"⚠️  Models directory not found: {models_dir}")
            return {}

        print(f"🔍 Discovering models in: {models_dir}")

        for model_path in models_dir.iterdir():
            if model_path.is_dir() and not model_path.name.startswith('_'):
                model_name = model_path.name
                model_info = self._discover_model(model_path, model_name)

                if model_info:
                    self.discovered_models[model_name] = model_info
                    print(f"✅ Discovered model: {model_name}")

        print(f"📊 Total models discovered: {len(self.discovered_models)}")
        return self.discovered_models

    def _discover_model(self, model_path: Path, model_name: str) -> Optional[Dict[str, Any]]:
        """Discover components of a specific model"""
        model_info = {
            'name': model_name,
            'path': str(model_path),
            'strategies': [],
            'migrations': [],
            'tests': [],
            'has_ingest': False,
            'has_migrate': False,
            'has_explore': False,
        }

        # Check for ingest components
        ingest_path = model_path / 'ingest'
        if ingest_path.exists():
            model_info['has_ingest'] = True

            # Look for strategy files (both singular and plural)
            for file_path in ingest_path.glob('*strateg*.py'):
                model_info['strategies'].append(str(file_path))

        # Check for migration components
        migrate_path = model_path / 'migrate'
        if migrate_path.exists():
            model_info['has_migrate'] = True

            # Look for SQL migration files
            for file_path in migrate_path.glob('*.sql'):
                model_info['migrations'].append(str(file_path))

        # Check for exploration components
        explore_path = model_path / 'explore'
        if explore_path.exists():
            model_info['has_explore'] = True

            # Look for exploration scripts
            for file_path in explore_path.glob('*.py'):
                model_info['tests'].append(str(file_path))

        # Check for test components
        test_files = list(model_path.glob('*test*.py'))
        model_info['tests'].extend([str(f) for f in test_files])

        return model_info

    def load_strategy(self, model_name: str) -> Optional['BaseLoaderStrategy']:
        """Load strategy for a specific model"""
        if model_name not in self.discovered_models:
            print(f"❌ Model not found: {model_name}")
            return None

        model_info = self.discovered_models[model_name]

        # Try to load strategy from model files
        for strategy_file in model_info['strategies']:
            try:
                # Import the strategy module
                spec = importlib.util.spec_from_file_location(
                    f"{model_name}_strategy",
                    strategy_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find strategy class (should inherit from BaseLoaderStrategy)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        issubclass(attr, BaseLoaderStrategy) and
                        attr != BaseLoaderStrategy):
                        strategy = attr()
                        self.strategies[model_name] = strategy
                        print(f"✅ Loaded strategy for {model_name}: {attr.__name__}")
                        return strategy

            except Exception as e:
                print(f"⚠️  Failed to load strategy from {strategy_file}: {e}")
                continue

        print(f"❌ No valid strategy found for model: {model_name}")
        return None

    def get_all_strategies(self) -> Dict[str, 'BaseLoaderStrategy']:
        """Load all available strategies"""
        if not self.discovered_models:
            self.discover_models()

        for model_name in self.discovered_models:
            if model_name not in self.strategies:
                self.load_strategy(model_name)

        return self.strategies

    def get_model_migrations(self, model_name: str) -> Tuple[List[str], List[str]]:
        """Get migration files for a model (up and down)"""
        if model_name not in self.discovered_models:
            return [], []

        model_info = self.discovered_models[model_name]
        up_migrations = []
        down_migrations = []

        for migration_file in model_info['migrations']:
            if 'rollback' in migration_file.lower() or 'down' in migration_file.lower():
                down_migrations.append(migration_file)
            else:
                up_migrations.append(migration_file)

        return sorted(up_migrations), sorted(down_migrations)