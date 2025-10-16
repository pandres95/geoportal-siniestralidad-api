# 🚀 New Loader System - Complete Implementation

## Overview

This directory contains a completely refactored data loading system organized by models with exclusive .gpkg (GeoPackage) format support. The system features a unified "victims" model using the `victims` table, with a clean folder structure for easy maintenance and extension.

## 🏗️ Architecture

### Unified Pipeline Architecture

The system provides two complementary approaches:

#### 🚀 **Unified Loader** (`ingest_unified.py`)

- **Automatic discovery**: Finds all models in `models/` directory
- **Complete pipeline**: Handles migration + data loading in one command
- **Multi-model support**: Processes all discovered models automatically
- **Single entry point**: One command for complete data pipeline

#### 📦 **Model-Specific Loaders**

- **Individual control**: Separate loaders for each model
- **Granular management**: Handle models independently
- **Debugging friendly**: Easier to troubleshoot specific models

### Model-Based Organization

Each model is organized in its own folder with two main components:

- **`migrate/`**: Database schema and migration scripts
- **`ingest/`**: Data loading strategies and processing logic

*Note: Data exploration tools are available in `models/_template/explore/` for auxiliary use.*

### Strategy Pattern Design

- **BaseLoaderStrategy**: Abstract base class defining the interface
- **Model-specific strategies**: Concrete implementations (VictimsLoaderStrategy, etc.)
- **Automatic discovery**: Strategies loaded dynamically from model folders

### Key Features

- ✅ **Multiple model support**: Easy to add new data models
- ✅ **Exclusive .gpkg support**: Optimized for GeoPackage format only
- ✅ **Data transformation**: Automatic coordinate system and data type conversion
- ✅ **Environment configuration**: Database connection via environment variables
- ✅ **Rollback capability**: Migrate down functionality for safe deployments
- ✅ **Comprehensive testing**: Full test suite for validation

## 📁 File Structure

```
loader/
├── README_NEW_SYSTEM.md                    # This file
├── requirements.txt                        # Python dependencies
├── ingest_unified.py                       # 🚀 Main unified loader
├── base_strategy.py                        # 🔌 Base strategy interface
├── test_unified_system.py                  # 🧪 Unified system tests
└── models/
    ├── victims/                           # Victims model implementation
    │   ├── ingest/
    │   ├── migrate/
    │   │   ├── 001_create_victims_table.sql      # Database schema
    │   │   ├── 001_create_victims_table_rollback.sql  # Rollback script
    │   │   └── migrate_existing_data.py   # Legacy data migration
    │   ├── ingest/
    │   │   └── strategies.py              # Strategy implementation
    │   ├── migration_strategy.md          # Migration documentation
    │   └── test_new_system.py             # Test suite
    └── _template/                         # Template for new models
        ├── README.md                      # Template documentation
        ├── migrate/
        │   └── 001_create_template_table.sql     # Template schema
        └── ingest/
            ├── template_strategy.py       # Template strategy
            └── ingest_template.py         # Template loader
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
cd loader
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Unified Pipeline (Recommended)

```bash
# Set your database URL
export DATABASE_URL="your_postgresql_connection_string"

# Run complete pipeline (discover → migrate → load)
python3 ingest_unified.py

# Or run specific steps
python3 ingest_unified.py --no-load                      # Only discover models (safe)
python3 ingest_unified.py --migrate-up --no-load        # Discovery + migrations only
python3 ingest_unified.py --migrate-down                 # Rollback + reload (WARNING!)
python3 ingest_unified.py --discover-only                # Pure discovery mode
```

### 3. Individual Model Usage

```bash
# For victims model specifically
python3 models/victims/ingest/ingest_v2.py --file ../data/accidents.gpkg

# Run victims-specific tests
python3 models/victims/test_new_system.py

# Migrate legacy data
python3 models/victims/migrate/migrate_existing_data.py
```

### 4. Adding New Models

```bash
# Copy template to create new model
cp -r models/_template models/schools

# Customize the new model (edit files in models/schools/)
# The unified loader will automatically discover it
python3 ingest_unified.py  # Will include schools model
```

## 🔧 Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (required)

### Adding New Models

1. **Copy the template**:

   ```bash
   cp -r models/_template models/your_new_model
   ```

2. **Customize the files** in `models/your_new_model/`:
   - Update `migrate/001_create_template_table.sql` with your schema
   - Modify `ingest/template_strategy.py` for your data format
   - Adapt `ingest/ingest_template.py` for your loading logic

3. **Register the model** in the loader configuration

4. **Test thoroughly** before production use

### Model Configuration

Each model has its own configuration in its respective folder:

```python
# In models/your_model/ingest/ingest_your_model.py
MODEL_CONFIG = {
    'your_data.gpkg': 'your_model',
}
```

## 🗄️ Database Schema

### New `victims` Table

```sql
CREATE TABLE victims (
  fid SERIAL PRIMARY KEY,
  formulario TEXT,
  codigo_accidentado INTEGER,
  codigo_victima INTEGER,
  codigo_vehiculo INTEGER,
  estado_30d TEXT,
  muerte_posterior TEXT,
  fecha_posterior_muerte DATE,
  genero TEXT,
  fecha_nacimiento DATE,
  edad INTEGER,
  codigo TEXT,
  condicion_a TEXT,
  fecha_acc DATE,
  latitud DECIMAL(10,8),
  longitud DECIMAL(11,8),
  geom GEOMETRY(POINT, 4326) NOT NULL
);
```

## 🔄 Data Transformations

### Automatic Conversions

- **Coordinate Systems**: EPSG:3857 → EPSG:4326
- **Date Formats**: Text dates → DATE type
- **Column Mapping**: Source columns → Target schema
- **Geometry Validation**: WKT format validation

### Supported Date Formats

- `YYYY-MM-DD`
- `DD/MM/YYYY`
- `YYYY/MM/DD`
- `MM/DD/YYYY`
- Excel date numbers (days since 1900-01-01)

## 🧪 Testing

### Test Coverage

#### Unified System Tests

- ✅ Model discovery mechanism
- ✅ Strategy loading and interface compliance
- ✅ Migration file discovery and execution
- ✅ Complete pipeline integration
- ✅ Error handling and edge cases

#### Model-Specific Tests

- ✅ Strategy pattern implementation
- ✅ .gpkg file loading
- ✅ Data transformation logic
- ✅ Database connectivity
- ✅ Migration script functionality
- ✅ End-to-end loading pipeline

### Running Tests

#### Unified System Tests

```bash
# Test the complete unified pipeline
python3 test_unified_system.py

# Or run simple tests
python3 test_unified_system.py --run-simple
```

#### Model-Specific Tests

```bash
# Test individual models
python3 models/victims/test_new_system.py

# Test specific components
# python3 models/_template/explore/explore_generic.py ../data/your_file.gpkg
```

## 🔀 Migration Guide

### From Old System

1. **Backup existing data** (if needed)
2. **Run schema migration**: `models/victims/migrate/001_create_victims_table.sql`
3. **Migrate legacy data**: `models/victims/migrate/migrate_existing_data.py`
4. **Test new system**: `models/victims/test_new_system.py`
5. **Update API endpoints** to use `victims` table

### Rollback (if needed)

```sql
-- Drop new table
\i models/victims/migrate/001_create_victims_table_rollback.sql

-- Restore original tables (manual process)
-- CREATE original accidents_injuries table...
-- CREATE original accidents_fatalities table...
```

### Adding New Models

1. **Copy template**: `cp -r models/_template models/your_model_name`
2. **Customize schema**: Edit `models/your_model_name/migrate/001_create_*_table.sql`
3. **Implement strategy**: Modify `models/your_model_name/ingest/*_strategy.py`
4. **Create loader**: Adapt `models/your_model_name/ingest/ingest_*.py`
5. **Test thoroughly**: Run comprehensive tests before deployment

## 🚨 Important Notes

### Breaking Changes

- **Table name**: `accidents_injuries`/`accidents_fatalities` → `victims`
- **Column names**: Updated to match .gpkg source format
- **Data types**: Proper DATE types instead of text
- **Coordinate system**: Now using EPSG:4326 consistently
- **File organization**: Moved to model-based folder structure

### File Format Policy

- **Exclusive .gpkg support**: System processes only .gpkg (GeoPackage) files
- **No JSON/geojson processing**: All JSON and GeoJSON files are automatically ignored
- **Migration available**: Use `migrate_existing_data.py` to convert legacy data to .gpkg format
- **Future formats**: Easy to extend for additional geospatial formats when needed

### Performance Considerations

- **Batch size**: 1000 records per batch for optimal performance
- **Indexes**: Created on key query columns
- **Geometry**: Using GiST index for spatial queries

### Future Extensions

- **Schools model**: Use `models/_template/` to create `models/schools/`
- **Additional models**: Copy template structure for any new geospatial dataset
- **Model composition**: Combine multiple models for complex analyses
- **Real-time loading**: Can be extended for streaming data

## 📞 Support

For issues or questions:

1. **Check model structure**: Verify files are in correct `models/{model}/` folders
2. **Check test output**: Run `models/{model}/test_*.py` for diagnostics
3. **Review migration docs**: See `models/{model}/migration_strategy.md`
4. **Examine logs**: Check data transformation logs in model folders
5. **Verify database**: Confirm connectivity and permissions
6. **Use templates**: Copy from `models/_template/` for new models
7. **Explore data**: Use `models/_template/explore/explore_generic.py` for data analysis (auxiliary)

---

**Status**: ✅ Complete with unified pipeline and model-based organization
**Last Updated**: 2025-10-16
**Models Available**: victims (ready for schools, additional models)
**Pipeline**: Unified loader with automatic model discovery
**Compatibility**: Python 3.8+, PostgreSQL 12+, PostGIS 3.0+
**File Format**: Exclusive .gpkg support
