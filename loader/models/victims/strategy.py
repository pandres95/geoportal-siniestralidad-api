"""
Strategy pattern for different data loading models.
Each strategy handles specific data format and transformation logic.
"""
import geopandas as gpd
import pandas as pd
from datetime import datetime
import json
import os
import glob
from typing import List, Dict, Any, Optional

# Import the base strategy interface
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from core.strategy import BaseLoaderStrategy
except ImportError:
    # Fallback for direct execution
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from core.strategy import BaseLoaderStrategy


class VictimsLoaderStrategy(BaseLoaderStrategy):
    """Strategy for loading victims data from .gpkg files"""

    def __init__(self):
        super().__init__("victims", "victims")
        self.source_crs = "EPSG:3857"  # Web Mercator from .gpkg

    def load_data(self, file_path: str) -> gpd.GeoDataFrame:
        """Load .gpkg file containing actores data"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        print(f"📖 Loading actores data from: {file_path}")
        gdf = gpd.read_file(file_path)

        print(f"✅ Loaded {len(gdf)} records")
        print(f"📋 Columns: {list(gdf.columns)}")
        print(f"📐 CRS: {gdf.crs}")

        return gdf

    def transform_data(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Transform actores data for database insertion"""
        print("🔄 Transforming actores data...")

        # Create a copy to avoid modifying original
        transformed_gdf = gdf.copy()

        # Transform coordinate system if needed
        if gdf.crs and gdf.crs.to_string() != self.target_crs:
            print(f"🌐 Transforming CRS from {gdf.crs} to {self.target_crs}")
            transformed_gdf = transformed_gdf.to_crs(self.target_crs)
        else:
            print(f"✅ CRS already {self.target_crs}")

        # Convert text dates to datetime objects
        date_columns = ['FECHA_NACIMIENTO', 'FECHA_ACC', 'FECHA_POSTERIOR_MUERTE']
        for col in date_columns:
            if col in transformed_gdf.columns:
                print(f"📅 Converting {col} to DATE")
                transformed_gdf[col] = self._convert_to_date(transformed_gdf[col])

        # Extract lat/lng from geometry if not present
        if 'LATITUD' not in transformed_gdf.columns or 'LONGITUD' not in transformed_gdf.columns:
            print("📍 Extracting coordinates from geometry")
            coords = transformed_gdf.geometry.get_coordinates()
            if coords is not None and len(coords) > 0:
                transformed_gdf['LONGITUD'] = coords[:, 0]  # x/longitude
                transformed_gdf['LATITUD'] = coords[:, 1]   # y/latitude

        # Rename columns to match database schema
        column_mapping = self.get_column_mapping()
        for source_col, target_col in column_mapping.items():
            if source_col in transformed_gdf.columns:
                print(f"📝 Renaming {source_col} → {target_col}")
                transformed_gdf.rename(columns={source_col: target_col}, inplace=True)

        # Validate required columns
        required_cols = ['formulario', 'codigo_accidentado', 'fecha_acc', 'geom']
        missing_cols = [col for col in required_cols if col not in transformed_gdf.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        print(f"✅ Transformation completed. Final columns: {list(transformed_gdf.columns)}")
        return transformed_gdf

    def _convert_to_date(self, series: pd.Series) -> pd.Series:
        """Convert text dates to datetime objects"""
        converted = pd.Series(index=series.index, dtype='object')

        for idx, value in series.items():
            if pd.isna(value) or value == 'NaN' or value == '':
                converted.iloc[idx] = None
                continue

            try:
                # Try different date formats
                if isinstance(value, str):
                    # Handle common formats
                    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d', '%m/%d/%Y']:
                        try:
                            converted.iloc[idx] = datetime.strptime(value, fmt).date()
                            break
                        except ValueError:
                            continue
                    else:
                        print(f"⚠️  Could not parse date: {value}")
                        converted.iloc[idx] = None
                elif isinstance(value, (int, float)):
                    # Handle Excel date numbers (days since 1900-01-01)
                    try:
                        converted.iloc[idx] = pd.to_datetime('1900-01-01') + pd.Timedelta(days=int(value))
                        converted.iloc[idx] = converted.iloc[idx].date()
                    except:
                        converted.iloc[idx] = None
                else:
                    converted.iloc[idx] = None

            except Exception as e:
                print(f"⚠️  Error converting date {value}: {e}")
                converted.iloc[idx] = None

        return converted

    def get_column_mapping(self) -> Dict[str, str]:
        """Map source columns to target database columns"""
        return {
            'FORMULARIO': 'formulario',
            'CODIGO_ACCIDENTADO': 'codigo_accidentado',
            'CODIGO_VICTIMA': 'codigo_victima',
            'CODIGO_VEHICULO': 'codigo_vehiculo',
            'ESTADO30D': 'estado',
            'MUERTE_POSTERIOR': 'muerte_posterior',
            'FECHA_POSTERIOR_MUERTE': 'fecha_posterior_muerte',
            'GENERO': 'genero',
            'FECHA_NACIMIENTO': 'fecha_nacimiento',
            'Edad': 'edad',
            'CODIGO': 'codigo',
            'CONDICION_A': 'condicion',
            'FECHA_ACC': 'fecha_acc',
            'LATITUD': 'latitud',
            'LONGITUD': 'longitud',
            'geometry': 'geom'
        }

    def get_insert_sql(self) -> str:
        """Return SQL insert statement for victims table"""
        return """
        INSERT INTO public.victims
        (formulario, codigo_accidentado, codigo_victima, codigo_vehiculo,
         estado, muerte_posterior, fecha_posterior_muerte, genero,
         fecha_nacimiento, edad, codigo, condicion, fecha_acc,
         latitud, longitud, geom)
        VALUES %s
        """

    def validate_data(self, gdf: gpd.GeoDataFrame) -> List[str]:
        """Validate victims-specific data"""
        warnings = super().validate_data(gdf)

        # Check for reasonable date ranges
        if 'fecha_acc' in gdf.columns:
            future_dates = gdf['fecha_acc'].dropna()
            if len(future_dates) > 0:
                future_count = (future_dates > datetime.now().date()).sum()
                if future_count > 0:
                    warnings.append(f"Found {future_count} accident dates in the future")

        # Check for reasonable age ranges
        if 'edad' in gdf.columns:
            invalid_ages = gdf['edad'].dropna()
            if len(invalid_ages) > 0:
                too_young = (invalid_ages < 0).sum()
                too_old = (invalid_ages > 150).sum()
                if too_young > 0:
                    warnings.append(f"Found {too_young} negative ages")
                if too_old > 0:
                    warnings.append(f"Found {too_old} ages over 150")

        return warnings

    def get_migration_files(self) -> Dict[str, List[str]]:
        """Return migration files for this model (up and down)"""
        model_path = f"models/{self.model_name}"
        migrate_path = f"{model_path}/migrate"

        up_migrations = []
        down_migrations = []

        if os.path.exists(migrate_path):
            # Get all .sql files in migrate directory
            for file_path in sorted(glob.glob(os.path.join(migrate_path, "*.sql"))):
                filename = os.path.basename(file_path)
                if 'rollback' in filename.lower() or 'down' in filename.lower():
                    down_migrations.append(file_path)
                elif filename != '001_create_migrations_table.sql':  # Skip the migrations table itself
                    up_migrations.append(file_path)

        return {
            'up': up_migrations,
            'down': down_migrations
        }

