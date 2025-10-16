#!/usr/bin/env python3
"""
Migration script to transform existing JSON accident data to new actores format.
This script handles the transition from the old separate tables to the unified actores table.
"""
import os
import json
import geopandas as gpd
import pandas as pd
from datetime import datetime
import psycopg2
import psycopg2.extras
from shapely.geometry import Point
from shapely.wkt import loads as wkt_loads
import glob

# Import our strategy for consistency
from strategies import ActoresLoaderStrategy

class DataMigrator:
    """Handles migration from old JSON format to new actores table"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.strategy = ActoresLoaderStrategy()
        self.stats = {
            'files_processed': 0,
            'records_migrated': 0,
            'errors': []
        }

    def migrate_json_files(self, data_dir: str = "../data") -> bool:
        """Migrate all JSON files in data directory"""
        print("🔄 Starting migration of existing JSON data...")

        # Find JSON files
        json_patterns = [
            "accidents_with_injuries.json",
            "accidents_with_fatalities.json",
            "*accidents*.json"
        ]

        migrated_any = False

        for pattern in json_patterns:
            search_path = os.path.join(data_dir, pattern)
            json_files = glob.glob(search_path)

            for json_file in json_files:
                if self.migrate_single_file(json_file):
                    migrated_any = True

        if migrated_any:
            print("✅ Migration completed successfully!")
            self.print_summary()
        else:
            print("⚠️  No files were migrated")

        return migrated_any

    def migrate_single_file(self, json_file: str) -> bool:
        """Migrate a single JSON file"""
        try:
            print(f"\n📄 Migrating: {json_file}")

            if not os.path.exists(json_file):
                print(f"❌ File not found: {json_file}")
                return False

            # Load JSON data
            with open(json_file, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)

            print(f"📊 Loaded {len(geojson_data.get('features', []))} features")

            # Convert to GeoDataFrame
            gdf = gpd.GeoDataFrame.from_features(
                geojson_data['features'],
                crs='EPSG:4326'
            )

            # Transform to new format
            transformed_gdf = self._transform_legacy_data(gdf)

            # Load to database
            records_loaded = self._load_to_database(transformed_gdf)

            if records_loaded > 0:
                self.stats['files_processed'] += 1
                self.stats['records_migrated'] += records_loaded
                print(f"✅ Migrated {records_loaded} records from {json_file}")
                return True
            else:
                print(f"⚠️  No records migrated from {json_file}")
                return False

        except Exception as e:
            error_msg = f"Error migrating {json_file}: {str(e)}"
            print(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)
            return False

    def _transform_legacy_data(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Transform legacy JSON data to new actores format"""
        print("🔄 Transforming legacy data format...")

        # Create mapping from old columns to new columns
        column_mapping = {
            'codigo_acc': 'CODIGO_ACCIDENTADO',
            'formulario': 'FORMULARIO',
            'edad': 'Edad',
            'genero': 'GENERO',
            'condicion': 'CONDICION_A',
        }

        # Rename columns if they exist
        for new_col, old_col in column_mapping.items():
            if old_col in gdf.columns:
                gdf = gdf.rename(columns={old_col: new_col})

        # Handle occurred_at -> fecha_acc conversion
        if 'occurred_at' in gdf.columns:
            print("📅 Converting occurred_at to fecha_acc")
            gdf['fecha_acc'] = pd.to_datetime(gdf['occurred_at']).dt.date
            # Also set fecha_nacimiento if we have edad (approximate)
            if 'edad' in gdf.columns:
                gdf['fecha_nacimiento'] = pd.to_datetime(gdf['occurred_at']) - pd.to_timedelta(gdf['edad'] * 365.25, unit='D')
                gdf['fecha_nacimiento'] = gdf['fecha_nacimiento'].dt.date

        # Set default values for required columns
        required_defaults = {
            'codigo_victima': 1,  # Default victim code
            'codigo_vehiculo': None,
            'estado_30d': 'Unknown',
            'muerte_posterior': 'No',
            'codigo': 'MIGRATED',
        }

        for col, default_value in required_defaults.items():
            if col not in gdf.columns:
                print(f"➕ Adding column {col} with default value")
                gdf[col] = default_value

        # Ensure geometry column exists and is valid
        if 'geom' not in gdf.columns and 'geometry' in gdf.columns:
            gdf['geom'] = gdf['geometry']

        # Convert coordinates to lat/lng if not present
        if 'latitud' not in gdf.columns or 'longitud' not in gdf.columns:
            print("📍 Extracting coordinates from geometry")
            if 'geom' in gdf.columns:
                coords = gdf['geom'].get_coordinates()
                if coords is not None and len(coords) > 0:
                    gdf['longitud'] = coords[:, 0]  # x/longitude
                    gdf['latitud'] = coords[:, 1]   # y/latitude

        print(f"✅ Transformation completed. Columns: {list(gdf.columns)}")
        return gdf

    def _load_to_database(self, gdf: gpd.GeoDataFrame) -> int:
        """Load transformed data to database"""
        if len(gdf) == 0:
            print("⚠️  No data to load")
            return 0

        print(f"💾 Loading {len(gdf)} records to actores table...")

        # Prepare records for insertion
        records = []
        for _, row in gdf.iterrows():
            record = self._prepare_migration_record(row)
            if record:
                records.append(record)

        if not records:
            print("⚠️  No valid records to insert")
            return 0

        # Execute batch insert
        insert_sql = """
        INSERT INTO public.victims
        (formulario, codigo_accidentado, codigo_victima, codigo_vehiculo,
         estado_30d, muerte_posterior, fecha_posterior_muerte, genero,
         fecha_nacimiento, edad, codigo, condicion_a, fecha_acc,
         latitud, longitud, geom)
        VALUES %s
        """
        return self._execute_batch_insert(insert_sql, records)

    def _prepare_migration_record(self, row) -> tuple:
        """Prepare a record from migrated data for database insertion"""
        try:
            # Define the expected column order for actores table
            columns = [
                'formulario', 'codigo_accidentado', 'codigo_victima', 'codigo_vehiculo',
                'estado_30d', 'muerte_posterior', 'fecha_posterior_muerte', 'genero',
                'fecha_nacimiento', 'edad', 'codigo', 'condicion_a', 'fecha_acc',
                'latitud', 'longitud', 'geom'
            ]

            values = []
            for col in columns:
                if col == 'geom':
                    # Handle geometry
                    if hasattr(row, 'geometry') and row.geometry:
                        values.append(row.geometry.wkt)
                    elif 'geom' in row.index and row.geom:
                        values.append(row.geom.wkt)
                    else:
                        values.append(None)
                else:
                    # Handle regular columns
                    value = row.get(col, None)
                    if pd.isna(value) or value == 'NaN':
                        values.append(None)
                    else:
                        values.append(value)

            return tuple(values)

        except Exception as e:
            print(f"⚠️  Error preparing migration record: {e}")
            return None

    def _execute_batch_insert(self, sql: str, records: list) -> int:
        """Execute batch insert"""
        try:
            with psycopg2.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    psycopg2.extras.execute_values(
                        cur, sql, records, page_size=1000
                    )
                    records_loaded = cur.rowcount
                    conn.commit()
                    print(f"   📊 Inserted {records_loaded} records")
                    return records_loaded

        except Exception as e:
            print(f"❌ Database error during migration: {e}")
            raise

    def print_summary(self):
        """Print migration summary"""
        print("
📈 Migration Summary:"        print(f"   Files processed: {self.stats['files_processed']}")
        print(f"   Records migrated: {self.stats['records_migrated']}")
        print(f"   Errors: {len(self.stats['errors'])}")

        if self.stats['errors']:
            print("
❌ Errors encountered:"            for error in self.stats['errors']:
                print(f"   • {error}")


def main():
    """Main migration function"""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("❌ Please set DATABASE_URL environment variable")
        return 1

    migrator = DataMigrator(database_url)
    success = migrator.migrate_json_files()

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())