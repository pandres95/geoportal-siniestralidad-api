# Migration Strategy: Current Accidents → New 'actores' Table

## Research Findings

**GeoPackage Analysis:**

- **Records**: 62,306 rows, 16 columns
- **CRS**: EPSG:3857 (Web Mercator) → needs transformation to EPSG:4326
- **Geometry**: Column named 'geometry' (not 'geom')
- **Data types**: Mixed text/numeric/geometry

## Migration Strategy

### Phase 1: Schema Creation

Create new `actores` table with proper data types and constraints:

```sql
CREATE TABLE actores (
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
  geom GEOMETRY(POINT, 4326)
);
```

### Phase 2: Data Transformation & Loading

1. **Coordinate transformation**: EPSG:3857 → EPSG:4326
2. **Date conversion**: Text fields → DATE type
3. **Data validation**: Ensure data integrity during migration
4. **Batch processing**: Handle large dataset efficiently

### Phase 3: Rollback Strategy (Migrate Down)

- Backup current tables before migration
- Provide reverse transformation scripts
- Enable rollback on demand

### Phase 4: Loader Refactoring

- Support .gpkg file format
- Implement strategy pattern for different models
- Add environment variable configuration
- Include comprehensive testing

## Key Transformations Required

1. **Geometry**: `ST_Transform(geometry, 4326)`
2. **Dates**: `TO_DATE(FECHA_NACIMIENTO, 'YYYY-MM-DD')`
3. **Coordinates**: Extract from geometry or use LATITUD/LONGITUD
4. **Data types**: Proper casting and validation

## Testing Strategy

1. **Pre-migration**: Validate .gpkg data structure
2. **During migration**: Monitor data transformation
3. **Post-migration**: Compare source and target datasets
4. **Rollback testing**: Verify rollback functionality
