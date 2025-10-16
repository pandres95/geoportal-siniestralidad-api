# Model Template

This is a template structure for creating new data models in the unified system.

## Structure

```
models/{model_name}/
├── explore/           # Data exploration and analysis tools
│   └── explore_{model}.py    # Model-specific exploration (optional)
├── migrate/           # Database migration scripts
│   ├── 001_create_{model}_table.sql      # Schema creation
│   └── 001_create_{model}_table_rollback.sql  # Rollback script
└── ingest/           # Data loading and processing logic
    ├── {model}_strategy.py   # Loading strategy implementation
    └── ingest_{model}.py     # Model-specific loader (optional)
```

## Files to Create

### 1. Explore (`explore/`)

Use the generic explorer for initial analysis:

```bash
python3 ../models/_template/explore/explore_generic.py ../data/your_file.gpkg
```

### 2. Migrate (`migrate/`)

- `001_create_{model}_table.sql` - Database schema creation
- `001_create_{model}_table_rollback.sql` - Rollback script (auto-generated)

### 3. Ingest (`ingest/`)

- `{model}_strategy.py` - Loading strategy implementation (required)
- `ingest_{model}.py` - Model-specific loader (optional - unified loader is preferred)

## Steps to Create a New Model

1. **Explore your data** (auxiliary step):

   ```bash
   # Use the generic explorer to understand your data structure
   python3 models/_template/explore/explore_generic.py ../data/your_file.gpkg
   ```

2. **Copy this template** to `models/{your_model_name}/`:

   ```bash
   cp -r models/_template models/your_model_name
   ```

3. **Update placeholders** in all files:
   - Replace `{MODEL_NAME}` with your model name (e.g., Schools)
   - Replace `{TABLE_NAME}` with your database table name (e.g., schools)
   - Replace `{GEOMETRY_TYPE}` with your geometry type (e.g., POINT, POLYGON)
   - Replace `{MODEL_DESCRIPTION}` with a description of your model

3. **Customize the strategy** in `ingest/*_strategy.py`:
   - Update `get_column_mapping()` for your data structure
   - Modify `transform_data()` for your specific transformations
   - Update `get_insert_sql()` to match your table schema

4. **Customize database schema** in `migrate/001_create_*_table.sql`:
   - Add your model-specific columns
   - Update geometry type and constraints
   - Add appropriate indexes

5. **Test your model**:

   ```bash
   # Test the unified system (will discover your new model)
   python3 ../ingest_unified.py --no-load

   # Run your model-specific tests
   python3 models/your_model_name/test_*.py
   ```

## Template Placeholders

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{MODEL_NAME}` | Your model name | Schools |
| `{TABLE_NAME}` | Database table name | schools |
| `{GEOMETRY_TYPE}` | Geometry type | POINT, POLYGON |
| `{MODEL_DESCRIPTION}` | Description of your model | School locations in Bogota |
| `{SOURCE_CRS}` | Source coordinate system | EPSG:4326 |

## Example Usage

```bash
# The unified loader automatically discovers all models
python3 ../ingest_unified.py

# Or work with individual models
python3 models/schools/ingest/schools_strategy.py
```
